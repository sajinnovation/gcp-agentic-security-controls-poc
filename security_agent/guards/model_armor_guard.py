"""Model Armor guard for ADK agent-level callbacks.

Screens user prompts and model responses for prompt injection, sensitive data,
harmful content, and malicious URLs. Works with `adk web` (unlike runner plugins).
"""

from __future__ import annotations

import os
from typing import Optional, TYPE_CHECKING

from google.adk.agents.callback_context import CallbackContext
from google.adk.models.llm_request import LlmRequest
from google.adk.models.llm_response import LlmResponse
from google.genai import types

if TYPE_CHECKING:
    from google.cloud import modelarmor_v1


class ModelArmorGuard:
    """Model Armor security guard providing LlmAgent callbacks."""

    def __init__(
        self,
        template_name: str,
        location: str = "us-central1",
        block_on_match: bool = True,
    ) -> None:
        self.template_name = template_name
        self.location = location
        self.block_on_match = block_on_match

        from google.api_core.client_options import ClientOptions
        from google.cloud import modelarmor_v1

        self._modelarmor_v1 = modelarmor_v1
        self.client = modelarmor_v1.ModelArmorClient(
            transport="rest",
            client_options=ClientOptions(
                api_endpoint=f"modelarmor.{location}.rep.googleapis.com"
            ),
        )
        print(f"[ModelArmorGuard] Initialized with template: {template_name}")

    def _get_matched_filters(self, result) -> list[str]:
        matched_filters: list[str] = []
        if result is None:
            return matched_filters

        try:
            filter_results = dict(result.sanitization_result.filter_results)
        except (AttributeError, TypeError):
            return matched_filters

        filter_attr_mapping = {
            "csam": "csam_filter_filter_result",
            "malicious_uris": "malicious_uri_filter_result",
            "pi_and_jailbreak": "pi_and_jailbreak_filter_result",
            "rai": "rai_filter_result",
            "sdp": "sdp_filter_result",
            "virus_scan": "virus_scan_filter_result",
        }

        for filter_name, filter_obj in filter_results.items():
            attr_name = filter_attr_mapping.get(filter_name)
            if not attr_name:
                attr_name = (
                    "malicious_uri_filter_result"
                    if filter_name == "malicious_uris"
                    else f"{filter_name}_filter_result"
                )

            if not hasattr(filter_obj, attr_name):
                continue

            filter_result = getattr(filter_obj, attr_name)

            if filter_name == "sdp" and hasattr(filter_result, "inspect_result"):
                if (
                    hasattr(filter_result.inspect_result, "match_state")
                    and filter_result.inspect_result.match_state.name == "MATCH_FOUND"
                ):
                    matched_filters.append("sdp")
            elif filter_name == "rai":
                if (
                    hasattr(filter_result, "match_state")
                    and filter_result.match_state.name == "MATCH_FOUND"
                ):
                    matched_filters.append("rai")
                if hasattr(filter_result, "rai_filter_type_results"):
                    for sub_result in filter_result.rai_filter_type_results:
                        if hasattr(sub_result, "key") and hasattr(sub_result, "value"):
                            if (
                                hasattr(sub_result.value, "match_state")
                                and sub_result.value.match_state.name == "MATCH_FOUND"
                            ):
                                matched_filters.append(f"rai:{sub_result.key}")
            elif (
                hasattr(filter_result, "match_state")
                and filter_result.match_state.name == "MATCH_FOUND"
            ):
                matched_filters.append(filter_name)

        return matched_filters

    def _block_message(self, matched_filters: list[str], context: str) -> str:
        if "pi_and_jailbreak" in matched_filters:
            return (
                "I cannot process this request. Your message appears to contain "
                "instructions that could compromise safety guidelines. "
                "Please rephrase your question."
            )
        if "sdp" in matched_filters:
            return (
                "Your message contains sensitive personal information. "
                "For your security, please remove sensitive data and try again."
            )
        if any(f.startswith("rai") for f in matched_filters):
            return (
                "I cannot respond to this type of request. "
                "Please rephrase your question respectfully."
            )
        if context == "output":
            return (
                "My response was filtered for security reasons. "
                "Could you please rephrase your question?"
            )
        return (
            "I cannot process this request due to security concerns. "
            "Please rephrase your question."
        )

    def _extract_user_text(self, llm_request: LlmRequest) -> str:
        try:
            if llm_request.contents:
                for content in reversed(llm_request.contents):
                    if content.role == "user":
                        for part in content.parts:
                            if hasattr(part, "text") and part.text:
                                return part.text
        except Exception as exc:
            print(f"[ModelArmorGuard] Error extracting user text: {exc}")
        return ""

    def _extract_model_text(self, llm_response: LlmResponse) -> str:
        try:
            if llm_response.content and llm_response.content.parts:
                for part in llm_response.content.parts:
                    if hasattr(part, "text") and part.text:
                        return part.text
        except Exception as exc:
            print(f"[ModelArmorGuard] Error extracting model text: {exc}")
        return ""

    async def before_model_callback(
        self,
        callback_context: CallbackContext,
        llm_request: LlmRequest,
    ) -> Optional[LlmResponse]:
        user_text = self._extract_user_text(llm_request)
        if not user_text:
            return None

        print(f"[ModelArmorGuard] Screening user prompt: '{user_text[:80]}...'")

        try:
            ma = self._modelarmor_v1
            sanitize_request = ma.SanitizeUserPromptRequest(
                name=self.template_name,
                user_prompt_data=ma.DataItem(text=user_text),
            )
            result = self.client.sanitize_user_prompt(request=sanitize_request)
            matched_filters = self._get_matched_filters(result)

            if matched_filters and self.block_on_match:
                print(f"[ModelArmorGuard] BLOCKED input: {matched_filters}")
                message = self._block_message(matched_filters, "input")
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=message)],
                    )
                )

            print("[ModelArmorGuard] User prompt passed screening")
        except Exception as exc:
            print(f"[ModelArmorGuard] Error during prompt sanitization: {exc}")

        return None

    async def after_model_callback(
        self,
        callback_context: CallbackContext,
        llm_response: LlmResponse,
    ) -> Optional[LlmResponse]:
        model_text = self._extract_model_text(llm_response)
        if not model_text:
            return None

        print(f"[ModelArmorGuard] Screening model response: '{model_text[:80]}...'")

        try:
            ma = self._modelarmor_v1
            sanitize_request = ma.SanitizeModelResponseRequest(
                name=self.template_name,
                model_response_data=ma.DataItem(text=model_text),
            )
            result = self.client.sanitize_model_response(request=sanitize_request)
            matched_filters = self._get_matched_filters(result)

            if matched_filters and self.block_on_match:
                print(f"[ModelArmorGuard] BLOCKED output: {matched_filters}")
                message = self._block_message(matched_filters, "output")
                return LlmResponse(
                    content=types.Content(
                        role="model",
                        parts=[types.Part.from_text(text=message)],
                    )
                )

            print("[ModelArmorGuard] Model response passed screening")
        except Exception as exc:
            print(f"[ModelArmorGuard] Error during response sanitization: {exc}")

        return None


def create_model_armor_guard(
    project_id: str | None = None,
    location: str | None = None,
    template_name: str | None = None,
) -> ModelArmorGuard:
    """Create a ModelArmorGuard from environment variables."""
    project_id = (
        project_id
        or os.environ.get("GOOGLE_CLOUD_PROJECT")
        or os.environ.get("PROJECT_ID")
    )
    location = (
        location
        or os.environ.get("GOOGLE_CLOUD_LOCATION")
        or os.environ.get("LOCATION", "us-central1")
    )
    template_name = template_name or os.environ.get("TEMPLATE_NAME")
    template_id = os.environ.get("MODEL_ARMOR_TEMPLATE_ID")

    if not template_name and project_id and template_id:
        template_name = (
            f"projects/{project_id}/locations/{location}/templates/{template_id}"
        )

    if not template_name:
        raise ValueError(
            "Set TEMPLATE_NAME or MODEL_ARMOR_TEMPLATE_ID + GOOGLE_CLOUD_PROJECT. "
            "Run: python scripts/create_model_armor_template.py"
        )

    return ModelArmorGuard(template_name=template_name, location=location)
