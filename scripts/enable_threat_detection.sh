#!/usr/bin/env bash
# Enable Agent Platform Threat Detection in Security Command Center.
set -euo pipefail

ORG_ID="${ORG_ID:-}"
PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"

if [[ -z "$ORG_ID" && -z "$PROJECT_ID" ]]; then
  echo "Set ORG_ID or GOOGLE_CLOUD_PROJECT" >&2
  exit 1
fi

echo "Agent Platform Threat Detection monitors agents deployed to Agent Runtime."
echo "It detects runtime attacks (malicious binaries, container escapes, reverse shells)"
echo "and control-plane threats via Event Threat Detection audit log analysis."
echo ""

# Enable Container Threat Detection API (required for Agent Platform Threat Detection)
if [[ -n "$PROJECT_ID" ]]; then
  gcloud services enable containerthreatdetection.googleapis.com --project="$PROJECT_ID"
  echo "Enabled containerthreatdetection.googleapis.com on $PROJECT_ID"
fi

if [[ -n "$ORG_ID" ]]; then
  echo ""
  echo "To view monitored agents in SCC:"
  echo "  Console → Security Command Center → Findings → Resource type: Agent Platform agents"
  echo ""
  echo "Ensure SCC Premium/Enterprise tier is active for Agent Platform Threat Detection."
  echo "Org ID: $ORG_ID"
fi

echo ""
echo "Control-plane detectors (Event Threat Detection) cover:"
echo "  - AI Agent excessive permission denied actions"
echo "  - Cross-project token generation"
echo "  - BigQuery data exfiltration from agents"
echo "  - Anomalous metadata service access"
echo ""
echo "View findings: https://console.cloud.google.com/security/command-center/findings"
