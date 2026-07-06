#!/usr/bin/env bash
# Enable GCP APIs and platform security services for the agentic security POC.
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
LOCATION="${GOOGLE_CLOUD_LOCATION:-us-central1}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Set GOOGLE_CLOUD_PROJECT" >&2
  exit 1
fi

echo "Configuring project: $PROJECT_ID"

APIS=(
  aiplatform.googleapis.com
  modelarmor.googleapis.com
  dlp.googleapis.com
  bigquery.googleapis.com
  securitycenter.googleapis.com
  containerthreatdetection.googleapis.com
  chronicle.googleapis.com
  compute.googleapis.com
  iam.googleapis.com
  cloudresourcemanager.googleapis.com
)

for api in "${APIS[@]}"; do
  echo "Enabling $api..."
  gcloud services enable "$api" --project="$PROJECT_ID"
done

echo ""
echo "Creating BigQuery datasets for Agent Identity demo..."
bq --project_id="$PROJECT_ID" mk --dataset --location="$LOCATION" "${PROJECT_ID}:customer_service" 2>/dev/null || true
bq --project_id="$PROJECT_ID" mk --dataset --location="$LOCATION" "${PROJECT_ID}:admin" 2>/dev/null || true

echo ""
echo "Setup complete. Next steps:"
echo "  1. python scripts/create_model_armor_template.py"
echo "  2. cp .env.example .env  # fill in values"
echo "  3. adk web               # local testing"
echo "  4. python scripts/deploy_agent.py --agent-identity"
