#!/usr/bin/env bash
# Create a Cloud Armor security policy for the agent API endpoint.
# Apply this when exposing the agent via a Global External HTTP(S) Load Balancer.
set -euo pipefail

PROJECT_ID="${GOOGLE_CLOUD_PROJECT:-}"
POLICY_NAME="${CLOUD_ARMOR_POLICY:-agent-security-poc-policy}"
BACKEND_SERVICE="${BACKEND_SERVICE:-agent-api-backend}"

if [[ -z "$PROJECT_ID" ]]; then
  echo "Set GOOGLE_CLOUD_PROJECT" >&2
  exit 1
fi

echo "Creating Cloud Armor policy: $POLICY_NAME"

gcloud compute security-policies create "$POLICY_NAME" \
  --project="$PROJECT_ID" \
  --description="WAF policy for agentic security POC API endpoint"

# Block SQL injection and XSS at the edge (Layer 1 deterministic control)
gcloud compute security-policies rules create 1000 \
  --security-policy="$POLICY_NAME" \
  --expression="evaluatePreconfiguredExpr('sqli-v33-stable')" \
  --action=deny-403 \
  --project="$PROJECT_ID"

gcloud compute security-policies rules create 1001 \
  --security-policy="$POLICY_NAME" \
  --expression="evaluatePreconfiguredExpr('xss-v33-stable')" \
  --action=deny-403 \
  --project="$PROJECT_ID"

# Rate limit to mitigate abuse
gcloud compute security-policies rules create 2000 \
  --security-policy="$POLICY_NAME" \
  --expression="true" \
  --action=rate-based-ban \
  --rate-limit-threshold-count=100 \
  --rate-limit-threshold-interval-sec=60 \
  --ban-duration-sec=600 \
  --conform-action=allow \
  --exceed-action=deny-429 \
  --enforce-on-key=IP \
  --project="$PROJECT_ID"

echo ""
echo "Attach to backend service:"
echo "  gcloud compute backend-services update $BACKEND_SERVICE \\"
echo "    --security-policy=$POLICY_NAME --global --project=$PROJECT_ID"
echo ""
echo "Cloud Armor protects the agent API at the network edge, complementing"
echo "Model Armor which protects prompts/responses at the application layer."
