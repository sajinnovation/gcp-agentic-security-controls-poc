"""Sensitive Data Protection (Cloud DLP) inspection tool.

Demonstrates Layer 1 deterministic controls for PII detection. When deployed,
this complements Model Armor's SDP filter and Agent Identity IAM boundaries.
"""

from __future__ import annotations

import os
import re
from typing import Any

# Local regex patterns for offline demo; Cloud DLP API used when configured.
_LOCAL_PATTERNS: dict[str, re.Pattern[str]] = {
    "CREDIT_CARD_NUMBER": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "US_SOCIAL_SECURITY_NUMBER": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "EMAIL_ADDRESS": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"),
    "PHONE_NUMBER": re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "GCP_API_KEY": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
}


def _local_inspect(text: str) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    for info_type, pattern in _LOCAL_PATTERNS.items():
        if pattern.search(text):
            findings.append({"info_type": info_type, "source": "local_pattern"})
    return findings


def _cloud_dlp_inspect(text: str, project_id: str) -> list[dict[str, Any]]:
    from google.cloud import dlp_v2

    client = dlp_v2.DlpServiceClient()
    parent = f"projects/{project_id}/locations/global"

    inspect_config = dlp_v2.InspectConfig(
        info_types=[
            dlp_v2.InfoType(name=t) for t in _LOCAL_PATTERNS
        ],
        include_quote=False,
        min_likelihood=dlp_v2.Likelihood.POSSIBLE,
    )

    item = dlp_v2.ContentItem(value=text)
    response = client.inspect_content(
        request={
            "parent": parent,
            "inspect_config": inspect_config,
            "item": item,
        }
    )

    findings: list[dict[str, Any]] = []
    for finding in response.result.findings:
        findings.append(
            {
                "info_type": finding.info_type.name,
                "likelihood": finding.likelihood.name,
                "source": "cloud_dlp",
            }
        )
    return findings


def inspect_for_sensitive_data(text: str) -> dict:
    """Inspect text for sensitive data using Cloud DLP or local patterns.

    Use this tool before returning user-provided data to verify no PII leaks.
    Requires DLP API when USE_CLOUD_DLP=1 and GOOGLE_CLOUD_PROJECT are set.

    Args:
        text: Text content to inspect for sensitive data types.

    Returns:
        Inspection results with findings list and whether sensitive data was found.
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT", "")
    use_cloud = os.environ.get("USE_CLOUD_DLP", "0") == "1"

    if use_cloud and project_id:
        try:
            findings = _cloud_dlp_inspect(text, project_id)
            return {
                "engine": "cloud_dlp",
                "findings": findings,
                "has_sensitive_data": len(findings) > 0,
            }
        except Exception as exc:
            return {
                "engine": "cloud_dlp",
                "error": str(exc),
                "findings": _local_inspect(text),
                "has_sensitive_data": bool(_local_inspect(text)),
                "fallback": "local_pattern",
            }

    findings = _local_inspect(text)
    return {
        "engine": "local_pattern",
        "findings": findings,
        "has_sensitive_data": len(findings) > 0,
    }
