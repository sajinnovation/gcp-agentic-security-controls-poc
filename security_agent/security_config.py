"""Security feature configuration for the agentic security controls POC."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, "1" if default else "0").lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


@dataclass(frozen=True)
class SecurityFeatures:
    """Toggle each GCP security control demonstrated in this POC."""

    model_armor: bool
    agent_identity: bool
    agent_gateway: bool
    threat_detection: bool
    secops_agents: bool
    confidential_computing: bool
    sensitive_data_protection: bool
    cloud_armor: bool

    @classmethod
    def from_env(cls) -> "SecurityFeatures":
        return cls(
            model_armor=_env_bool("ENABLE_MODEL_ARMOR", default=True),
            agent_identity=_env_bool("ENABLE_AGENT_IDENTITY"),
            agent_gateway=_env_bool("ENABLE_AGENT_GATEWAY"),
            threat_detection=_env_bool("ENABLE_THREAT_DETECTION"),
            secops_agents=_env_bool("ENABLE_SECOPS_AGENTS"),
            confidential_computing=_env_bool("ENABLE_CONFIDENTIAL_COMPUTING"),
            sensitive_data_protection=_env_bool("ENABLE_SENSITIVE_DATA_PROTECTION", True),
            cloud_armor=_env_bool("ENABLE_CLOUD_ARMOR"),
        )

    def summary(self) -> str:
        lines = [
            "Security Controls Status:",
            f"  Model Armor:              {'ON' if self.model_armor else 'OFF'}",
            f"  Agent Identity:           {'ON' if self.agent_identity else 'OFF'}",
            f"  Agent Gateway:            {'ON' if self.agent_gateway else 'OFF'}",
            f"  Threat Detection:         {'ON' if self.threat_detection else 'OFF'}",
            f"  SecOps Agents:            {'ON' if self.secops_agents else 'OFF'}",
            f"  Confidential Computing:   {'ON' if self.confidential_computing else 'OFF'}",
            f"  Sensitive Data Protection:{'ON' if self.sensitive_data_protection else 'OFF'}",
            f"  Cloud Armor:              {'ON' if self.cloud_armor else 'OFF'}",
        ]
        return "\n".join(lines)
