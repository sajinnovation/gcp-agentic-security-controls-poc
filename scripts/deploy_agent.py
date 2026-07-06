#!/usr/bin/env python3
"""Deploy the security POC agent to Agent Runtime with Agent Identity."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import vertexai
from vertexai import agent_engines


def deploy(
    project_id: str,
    location: str,
    display_name: str,
    staging_bucket: str,
    enable_agent_identity: bool,
    enable_confidential_computing: bool,
) -> None:
    repo_root = Path(__file__).resolve().parent.parent
    agent_module = repo_root / "security_agent"

    if not agent_module.exists():
        raise FileNotFoundError(f"Agent module not found: {agent_module}")

    client = vertexai.Client(
        project=project_id,
        location=location,
        http_options={"api_version": "v1beta1"},
    )

    config: dict = {
        "display_name": display_name,
        "requirements": str(repo_root / "requirements.txt"),
        "extra_packages": [str(agent_module)],
        "staging_bucket": staging_bucket,
    }

    if enable_agent_identity:
        config["identity_type"] = "AGENT_IDENTITY"
        print("Deploying with Agent Identity (SPIFFE-based per-agent principal)")

    if enable_confidential_computing:
        config["confidential_compute"] = True
        print("Deploying with Confidential Computing enabled")

    from security_agent.agent import root_agent

    remote_app = client.agent_engines.create(
        agent=root_agent,
        config=config,
    )

    print("\nDeployment successful!")
    print(f"  Resource name: {remote_app.api_resource.name}")
    print(f"  Display name:  {display_name}")

    if enable_agent_identity:
        engine_id = remote_app.api_resource.name.split("/")[-1]
        print("\nNext steps for Agent Identity IAM:")
        print("  1. Retrieve agent identity principal from deployment output")
        print("  2. Run: python scripts/grant_agent_iam.py --agent-identity <principal>")
        print(f"  3. Save AGENT_ENGINE_ID={engine_id}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy security POC agent")
    parser.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT"))
    parser.add_argument("--location", default=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"))
    parser.add_argument("--display-name", default="Agentic Security Controls POC")
    parser.add_argument("--staging-bucket", default=os.environ.get("STAGING_BUCKET"))
    parser.add_argument("--agent-identity", action="store_true", default=os.environ.get("ENABLE_AGENT_IDENTITY", "0") == "1")
    parser.add_argument("--confidential-computing", action="store_true", default=os.environ.get("ENABLE_CONFIDENTIAL_COMPUTING", "0") == "1")
    args = parser.parse_args()

    if not args.project:
        print("Set GOOGLE_CLOUD_PROJECT or pass --project", file=sys.stderr)
        return 1
    if not args.staging_bucket:
        print("Set STAGING_BUCKET (gs://your-bucket) or pass --staging-bucket", file=sys.stderr)
        return 1

    deploy(
        project_id=args.project,
        location=args.location,
        display_name=args.display_name,
        staging_bucket=args.staging_bucket,
        enable_agent_identity=args.agent_identity,
        enable_confidential_computing=args.confidential_computing,
    )
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    raise SystemExit(main())
