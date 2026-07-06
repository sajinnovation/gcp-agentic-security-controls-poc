"""Secure customer service agent demonstrating GCP agentic security controls."""

from __future__ import annotations

import os

from google.adk.agents import LlmAgent

from security_agent.guards.model_armor_guard import create_model_armor_guard
from security_agent.instructions import get_agent_instructions
from security_agent.security_config import SecurityFeatures
from security_agent.tools.customer_data import (
    lookup_customer,
    lookup_order,
    lookup_product,
)
from security_agent.tools.dlp_inspect import inspect_for_sensitive_data


def create_agent() -> LlmAgent:
    features = SecurityFeatures.from_env()
    print(features.summary())

    tools = [lookup_customer, lookup_order, lookup_product]
    if features.sensitive_data_protection:
        tools.append(inspect_for_sensitive_data)

    agent_kwargs: dict = {
        "model": os.environ.get("AGENT_MODEL", "gemini-2.5-flash"),
        "name": "secure_customer_service_agent",
        "instruction": get_agent_instructions(),
        "tools": tools,
    }

    if features.model_armor:
        try:
            guard = create_model_armor_guard()
            agent_kwargs["before_model_callback"] = guard.before_model_callback
            agent_kwargs["after_model_callback"] = guard.after_model_callback
        except ValueError as exc:
            print(f"[ModelArmorGuard] Skipped — {exc}")

    return LlmAgent(**agent_kwargs)


root_agent = create_agent()
