#!/usr/bin/env python3
"""Create a Model Armor template with security filters for the POC."""

from __future__ import annotations

import argparse
import os
import sys

from google.api_core.client_options import ClientOptions
from google.cloud import modelarmor_v1


def create_template(
    project_id: str,
    location: str,
    template_id: str,
) -> str:
    client = modelarmor_v1.ModelArmorClient(
        transport="rest",
        client_options=ClientOptions(
            api_endpoint=f"modelarmor.{location}.rep.googleapis.com"
        ),
    )

    parent = f"projects/{project_id}/locations/{location}"
    template_name = f"{parent}/templates/{template_id}"

    template = modelarmor_v1.Template(
        filter_config=modelarmor_v1.FilterConfig(
            pi_and_jailbreak_filter_settings=modelarmor_v1.PiAndJailbreakFilterSettings(
                filter_enforcement=modelarmor_v1.PiAndJailbreakFilterSettings.PiAndJailbreakFilterEnforcement.ENABLED
            ),
            sdp_filter_settings=modelarmor_v1.SdpFilterSettings(
                basic_config=modelarmor_v1.SdpBasicConfig(
                    filter_enforcement=modelarmor_v1.SdpBasicConfig.SdpBasicConfigEnforcement.ENABLED
                )
            ),
            rai_filter_settings=modelarmor_v1.RaiFilterSettings(
                rai_settings=modelarmor_v1.RaiSettings(
                    filter_enforcement=modelarmor_v1.RaiSettings.RaiFilterEnforcement.ENABLED
                )
            ),
            malicious_uri_filter_settings=modelarmor_v1.MaliciousUriFilterSettings(
                filter_enforcement=modelarmor_v1.MaliciousUriFilterSettings.MaliciousUriFilterEnforcement.ENABLED
            ),
        )
    )

    try:
        operation = client.create_template(
            parent=parent,
            template_id=template_id,
            template=template,
        )
        result = operation.result(timeout=120)
        return result.name
    except Exception as exc:
        if "already exists" in str(exc).lower():
            print(f"Template already exists: {template_name}")
            return template_name
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Create Model Armor template")
    parser.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT"))
    parser.add_argument("--location", default=os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1"))
    parser.add_argument("--template-id", default=os.environ.get("MODEL_ARMOR_TEMPLATE_ID", "security-poc-template"))
    args = parser.parse_args()

    if not args.project:
        print("Set GOOGLE_CLOUD_PROJECT or pass --project", file=sys.stderr)
        return 1

    template_name = create_template(args.project, args.location, args.template_id)
    print(f"Created Model Armor template: {template_name}")
    print(f"\nAdd to your .env:\nTEMPLATE_NAME={template_name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
