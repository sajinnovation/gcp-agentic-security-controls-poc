# GCP Agentic Security Controls POC

A proof-of-concept application built with the [Google Agent Development Kit (ADK)](https://google.github.io/adk-docs/) that demonstrates defense-in-depth security for AI agents across eight Google Cloud security controls.

## Architecture

```mermaid
flowchart TB
    User[User / Attacker] --> CA[Cloud Armor<br/>Edge WAF]
    CA --> GW[Agent Gateway<br/>mTLS + DPoP]
    GW --> Agent[ADK Agent<br/>Agent Runtime]
    
    subgraph Layer2 [Layer 2 — Reasoning Defenses]
        MA[Model Armor<br/>Input/Output Screening]
    end
    
    subgraph Layer1 [Layer 1 — Deterministic Controls]
        DLP[Sensitive Data Protection<br/>Cloud DLP]
        IAM[Agent Identity<br/>SPIFFE + IAM]
    end
    
    subgraph Layer3 [Layer 3 — Continuous Assurance]
        TD[Agent Platform<br/>Threat Detection]
        SO[Google SecOps<br/>Agents]
    end
    
    Agent --> MA
    Agent --> DLP
    Agent --> IAM
    Agent --> BQ[(BigQuery<br/>customer_service)]
    
    TD -.->|Runtime telemetry| Agent
    SO -.->|SCC findings| TD
```

## Security Controls Demonstrated

| Control | Layer | What It Does | Implementation |
|---------|-------|--------------|----------------|
| **Model Armor** | 2 | Screens prompts/responses for injection, PII, harmful content, malicious URLs | `security_agent/guards/model_armor_guard.py` |
| **Agent Identity** | 1 | Per-agent SPIFFE identity with least-privilege IAM | `scripts/deploy_agent.py`, `scripts/grant_agent_iam.py` |
| **Agent Gateway** | 1 | mTLS + DPoP for outbound tool auth; credential vault | Deploy-time config (see below) |
| **Agent Platform Threat Detection** | 3 | Runtime + control-plane threat monitoring in SCC | `scripts/enable_threat_detection.sh` |
| **Google SecOps Agents** | 3 | Autonomous triage, detection engineering, threat hunting | SCC → Chronicle integration |
| **Confidential Computing** | 1 | Encrypted-in-use execution on Agent Runtime | `--confidential-computing` deploy flag |
| **Sensitive Data Protection** | 1 | Cloud DLP PII inspection | `security_agent/tools/dlp_inspect.py` |
| **Cloud Armor** | 1 | Edge WAF + rate limiting for agent API | `scripts/setup_cloud_armor.sh` |

## Quick Start

### Prerequisites

- Python 3.10+
- Google Cloud project with billing enabled
- `gcloud` CLI authenticated
- Vertex AI API enabled

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure GCP environment

```powershell
# Windows
$env:GOOGLE_CLOUD_PROJECT = "your-project-id"
.\scripts\setup_env.ps1
```

```bash
# Linux / Cloud Shell
export GOOGLE_CLOUD_PROJECT=your-project-id
./scripts/setup_env.sh
```

### 3. Create Model Armor template

```bash
python scripts/create_model_armor_template.py
cp .env.example .env   # add TEMPLATE_NAME from script output
```

### 4. Run locally with ADK Web

```bash
# From repo root — Model Armor requires GCP credentials
adk web
```

Open http://localhost:8000, select `security_agent`, and test with legitimate queries:

- "Look up customer CUST-001"
- "What is the status of order ORD-1001?"

### 5. Red team the controls

```bash
python scripts/red_team_scenarios.py
```

Try the attack prompts in ADK Web and verify Model Armor blocks them.

### 6. Deploy to Agent Runtime with Agent Identity

```bash
export STAGING_BUCKET=gs://your-staging-bucket
export ENABLE_AGENT_IDENTITY=1
python scripts/deploy_agent.py --agent-identity

# Grant least-privilege IAM to the agent identity principal
export AGENT_IDENTITY="principal://agents.global.org-..."
python scripts/grant_agent_iam.py
```

### 7. Enable platform-level controls

```bash
# Agent Platform Threat Detection (SCC Premium/Enterprise)
export ORG_ID=your-org-id
./scripts/enable_threat_detection.sh

# Cloud Armor (when exposing agent via load balancer)
./scripts/setup_cloud_armor.sh
```

## Agent Gateway

[Agent Gateway](https://cloud.google.com/gemini-enterprise-agent-platform/docs/govern/agent-identity-overview) is the networking and governance layer for Agent Identity. When enabled:

- Outbound tool calls route through the gateway with mTLS
- End-user OAuth tokens are encrypted by the Auth Manager and decrypted only at the gateway
- Context-Aware Access enforces DPoP (Demonstrable Proof of Possession) on access tokens

Configure Agent Gateway when deploying to Gemini Enterprise Agent Platform by registering auth providers in the Agent Identity Auth Manager console. This POC deploys to Agent Runtime; enable `ENABLE_AGENT_GATEWAY=1` and configure MCP tool endpoints through the gateway for production workloads.

## Google SecOps Agents

[Google SecOps Agents](https://cloud.google.com/blog/products/identity-security/detecting-and-containing-powered-threats-with-google-security-operations-agents) consume findings from Security Command Center:

- **Detection Engineering Agent** — translates new attack patterns into custom detections
- **Triage and Investigation Agent** — autonomously investigates alerts with verdicts
- **Threat Hunting Agent** — proactively hunts for stealthy adversary behaviors

Agent Platform Threat Detection findings (runtime attacks, IAM anomalies, data exfiltration) flow into SCC where SecOps Agents can triage and respond. Enable Chronicle in `setup_env` and connect SCC to Google SecOps in the console.

## Project Structure

```
security_agent/
  agent.py              # Root agent (exports root_agent)
  instructions.py       # Agent system prompt
  security_config.py    # Feature flags per control
  guards/
    model_armor_guard.py  # Model Armor callbacks
  tools/
    customer_data.py    # Simulated customer service data
    dlp_inspect.py      # Cloud DLP inspection tool
scripts/
  setup_env.ps1/sh      # Enable APIs, create datasets
  create_model_armor_template.py
  deploy_agent.py       # Deploy with Agent Identity
  grant_agent_iam.py    # Least-privilege IAM
  enable_threat_detection.sh
  setup_cloud_armor.sh
  red_team_scenarios.py
```

## Defense in Depth

This POC implements Google's hybrid security strategy:

1. **Deterministic controls** — IAM (Agent Identity), DLP, Cloud Armor enforce policy regardless of model behavior
2. **Reasoning-based defenses** — Model Armor screens content the model might mishandle
3. **Continuous assurance** — Threat Detection + SecOps Agents monitor runtime and respond to incidents

Even if an attacker bypasses Model Armor via a novel prompt injection, Agent Identity IAM denies access to the `admin` dataset. Even if the LLM is tricked into trying, infrastructure enforces the boundary.

## References

- [ADK Safety & Security](https://google.github.io/adk-docs/safety/)
- [Model Armor](https://cloud.google.com/security/products/model-armor)
- [Agent Identity](https://cloud.google.com/gemini-enterprise-agent-platform/docs/govern/agent-identity-overview)
- [Agent Platform Threat Detection](https://cloud.google.com/security-command-center/docs/agent-platform-threat-detection-overview)
- [Secure Agent Codelab](https://codelabs.developers.google.com/secure-customer-service-agent/instructions)