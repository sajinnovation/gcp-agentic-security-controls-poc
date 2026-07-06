#!/usr/bin/env python3
"""Grant least-privilege IAM to an Agent Identity principal."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys


def run_gcloud(cmd: list[str]) -> None:
    print(f"$ {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Grant IAM to Agent Identity")
    parser.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT"))
    parser.add_argument("--agent-identity", default=os.environ.get("AGENT_IDENTITY"))
    parser.add_argument("--dataset", default="customer_service")
    args = parser.parse_args()

    if not args.project or not args.agent_identity:
        print("Set GOOGLE_CLOUD_PROJECT and AGENT_IDENTITY", file=sys.stderr)
        return 1

    baseline_roles = [
        "roles/serviceusage.serviceUsageConsumer",
        "roles/aiplatform.expressUser",
        "roles/browser",
        "roles/modelarmor.user",
        "roles/bigquery.jobUser",
    ]

    for role in baseline_roles:
        run_gcloud([
            "gcloud", "projects", "add-iam-policy-binding", args.project,
            f"--member={args.agent_identity}",
            f"--role={role}",
        ])

    condition = (
        "expression=resource.name.startsWith('projects/{}/datasets/{}'),"
        "title=Restrict to {} dataset,"
        "description=Agent Identity can only read customer_service dataset"
    ).format(args.project, args.dataset, args.dataset)

    run_gcloud([
        "gcloud", "projects", "add-iam-policy-binding", args.project,
        f"--member={args.agent_identity}",
        "--role=roles/bigquery.dataViewer",
        f"--condition={condition}",
    ])

    print("\nAgent Identity IAM configured with least-privilege BigQuery access.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
