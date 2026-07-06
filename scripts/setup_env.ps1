# Enable GCP APIs and platform security services for the agentic security POC.
$ErrorActionPreference = "Stop"

$ProjectId = $env:GOOGLE_CLOUD_PROJECT
$Location = if ($env:GOOGLE_CLOUD_LOCATION) { $env:GOOGLE_CLOUD_LOCATION } else { "us-central1" }

if (-not $ProjectId) {
    Write-Error "Set GOOGLE_CLOUD_PROJECT"
}

Write-Host "Configuring project: $ProjectId"

$Apis = @(
    "aiplatform.googleapis.com",
    "modelarmor.googleapis.com",
    "dlp.googleapis.com",
    "bigquery.googleapis.com",
    "securitycenter.googleapis.com",
    "containerthreatdetection.googleapis.com",
    "chronicle.googleapis.com",
    "compute.googleapis.com",
    "iam.googleapis.com",
    "cloudresourcemanager.googleapis.com"
)

foreach ($api in $Apis) {
    Write-Host "Enabling $api..."
    gcloud services enable $api --project=$ProjectId
}

Write-Host ""
Write-Host "Creating BigQuery datasets for Agent Identity demo..."
bq --project_id=$ProjectId mk --dataset --location=$Location "${ProjectId}:customer_service" 2>$null
bq --project_id=$ProjectId mk --dataset --location=$Location "${ProjectId}:admin" 2>$null

Write-Host ""
Write-Host "Setup complete. Next steps:"
Write-Host "  1. python scripts/create_model_armor_template.py"
Write-Host "  2. copy .env.example .env  # fill in values"
Write-Host "  3. adk web                  # local testing"
Write-Host "  4. python scripts/deploy_agent.py --agent-identity"
