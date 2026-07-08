#!/usr/bin/env python3
"""Deploy the security POC agent to Agent Runtime with Agent Identity."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import vertexai


def deploy(
    project_id: str,
    location: str,
    display_name: str,
    staging_bucket: str,
    enable_agent_identity: bool,
    enable_confidential_computing: bool,
    resource_name: str | None = None,
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

    wheel_path = repo_root / "dist" / "security_agent-0.1.0-py3-none-any.whl"
    if not wheel_path.exists():
        raise FileNotFoundError(
            f"Package wheel not found: {wheel_path}. "
            "Run: python -m build --wheel --outdir dist"
        )

    config: dict = {
        "display_name": display_name,
        "requirements": str(repo_root / "requirements.txt"),
        "extra_packages": [str(wheel_path)],
        "staging_bucket": staging_bucket,
        "python_version": "3.12",
        "env_vars": {
            "GOOGLE_GENAI_USE_VERTEXAI": "1",
            "ENABLE_MODEL_ARMOR": os.environ.get("ENABLE_MODEL_ARMOR", "1"),
            "ENABLE_SENSITIVE_DATA_PROTECTION": os.environ.get(
                "ENABLE_SENSITIVE_DATA_PROTECTION", "1"
            ),
            "TEMPLATE_NAME": os.environ.get(
                "TEMPLATE_NAME",
                f"projects/{project_id}/locations/{location}/templates/"
                f"{os.environ.get('MODEL_ARMOR_TEMPLATE_ID', 'security-poc-template')}",
            ),
            "MODEL_ARMOR_TEMPLATE_ID": os.environ.get(
                "MODEL_ARMOR_TEMPLATE_ID", "security-poc-template"
            ),
            "AGENT_MODEL": os.environ.get("AGENT_MODEL", "gemini-2.5-flash"),
            # Cloud Trace / OpenTelemetry for Agent Runtime
            # https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/tracing#write-traces
            "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY": "true",
            "OTEL_SEMCONV_STABILITY_OPT_IN": "gen_ai_latest_experimental",
            "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT": "EVENT_ONLY",
        },
    }

    if enable_agent_identity and not resource_name:
        config["identity_type"] = "AGENT_IDENTITY"
        print("Deploying with Agent Identity (SPIFFE-based per-agent principal)")

    if enable_confidential_computing:
        config["confidential_compute"] = True
        print("Deploying with Confidential Computing enabled")

    import cloudpickle
    import security_agent
    import security_agent.agent
    import security_agent.guards
    import security_agent.guards.model_armor_guard
    import security_agent.instructions
    import security_agent.security_config
    import security_agent.tools
    import security_agent.tools.customer_data
    import security_agent.tools.dlp_inspect
    from security_agent.agent import root_agent
    from vertexai.agent_engines import AdkApp

    # Embed local package source in the pickle so Agent Engine does not need
    # a pre-installed `security_agent` import path at unpickle time.
    for module in (
        security_agent,
        security_agent.agent,
        security_agent.guards,
        security_agent.guards.model_armor_guard,
        security_agent.instructions,
        security_agent.security_config,
        security_agent.tools,
        security_agent.tools.customer_data,
        security_agent.tools.dlp_inspect,
    ):
        cloudpickle.register_pickle_by_value(module)

    app = AdkApp(agent=root_agent, enable_tracing=True)

    if resource_name:
        print(f"Updating existing Agent Engine: {resource_name}")
        remote_app = client.agent_engines.update(
            name=resource_name,
            agent=app,
            config=config,
        )
    else:
        remote_app = client.agent_engines.create(
            agent=app,
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
    parser.add_argument(
        "--resource-name",
        default=os.environ.get("AGENT_ENGINE_RESOURCE_NAME"),
        help="Existing Agent Engine resource name to update",
    )
    parser.add_argument(
        "--agent-identity",
        action="store_true",
        default=os.environ.get("ENABLE_AGENT_IDENTITY", "0") == "1",
    )
    parser.add_argument(
        "--confidential-computing",
        action="store_true",
        default=os.environ.get("ENABLE_CONFIDENTIAL_COMPUTING", "0") == "1",
    )
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
        resource_name=args.resource_name,
    )
    return 0


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    raise SystemExit(main())
