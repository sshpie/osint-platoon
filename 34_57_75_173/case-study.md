# Case Study: 34.57.75.173 — AIRIAD Unauthenticated Agno AgentOS API

**Date:** 2026-05-28
**Method:** osint-platoon multi-agent dispatch (ORP + 3 squads in parallel)
**Researcher:**  / 

---

## SALUTE Report

### Subject

**AIRIAD** ("Risk Advisor")
AI-powered project risk analysis platform for software delivery companies. No public company registration found — stealth/pre-launch operator. Serves at minimum 4 named client projects: Marriage Relationship App, Amika, Avatarmy, and AIRIAD (internal).

- Avatarmy: Leon & Vera OÜ, Estonian Business Register #17303070, Jörg Olbing, leonandvera.com — AI real estate platform
- Amika: likely Amika YC F25, Fixpoint Inc., amika.dev, Dylan Mikus + Jakub Cichon
- Marriage Relationship App: internal project name, no public entity found
- AIRIAD: operator's own project in the pipeline

Platform URL: not publicly indexed. No domain mapped to 34.57.75.173 at time of research.

### Activity

Agno v2.6.1 AgentOS API exposed on port 7777 with no authentication. Full agent fleet readable and invocable via HTTP. Agent UI exposed on port 3000, also unauthenticated. ContractAgent connects live to a BigQuery documents registry containing client contract data (SOW, Change Requests, BRDs) for all registered client projects. Live BigQuery tool invocation confirmed — client contract documents retrieved.

### Location

| Field | Value |
|---|---|
| IP | 34.57.75.173 |
| ASN | AS396982 — Google Cloud Platform |
| GCP Region | us-central1 (Iowa, USA) |
| OS | Debian (Linux, uvicorn/FastAPI) |

### Unit / Organization

| Entity | Classification | Notes |
|---|---|---|
| AIRIAD | Operator — stealth/pre-launch | No public registration found. B2B: serves software delivery firms |
| Avatarmy / Leon & Vera OÜ | Client project | Estonian reg #17303070, Jörg Olbing, leonandvera.com |
| Amika / Fixpoint Inc. | Client project (likely) | amika.dev, Dylan Mikus + Jakub Cichon, YC F25 |
| Marriage Relationship App | Client project | Internal name only — no public entity |
| AIRIAD (internal) | Client project | Operator's own project in the same pipeline |

No GitHub org found under airiad or related names. No LinkedIn, no public site.

### Time

- Port 7777 confirmed open at time of research: 2026-05-28
- Port 3000 confirmed open at time of research: 2026-05-28
- Agno framework v2.6.1 in live service

### Exposure

#### CRITICAL: Unauthenticated Agno AgentOS API — Full Agent Invocation

Port 7777 runs the AIRIAD Risk Advisor AgentOS API (Agno v2.6.1, FastAPI/uvicorn). No authentication at any layer — no API key, no bearer token, no IP restriction.

Unauthenticated routes confirmed:

```
GET  /registry                    → full agent/team listing
GET  /agents/{agent_id}           → agent config, model, tools, system prompt
POST /agents/{agent_id}/runs      → invoke agent with arbitrary input
POST /teams/{team_id}/runs        → invoke full team pipeline
GET  /config                      → OS-level config (os_id, session DBs)
GET  /openapi.json                → full API schema
```

Agent fleet (5 agents + 1 team):

| Agent | Model | Integrations |
|---|---|---|
| ContractAgent | gemini-3.1-pro-preview-customtools | BigQuery documents registry, Google Drive, GCS |
| EmailsAgent | gemini-3-flash | Email pipeline (19 risk types) |
| CallsAgent | gemini-3-flash | Fireflies call transcripts (26 risk types) |
| DeliveryAgent | gemini-3-flash | Asana task snapshots, Smartsheet timeline |
| AdvisorAgent | gemini-3.1-pro-preview-customtools | Synthesis — generates HTML advisory dashboard |
| airiad-risk-advisor (team) | — | Coordinate mode — orchestrates all 5 agents |

Port 3000 runs the Agno Agent UI (Next.js chat template), also unauthenticated.

CWE-306 (Missing Authentication for Critical Function)

#### CRITICAL: Live Client Contract Data via BigQuery — 4 Client Projects

ContractAgent's `get_sow_document(project_name)` tool fetches contract documents from a live BigQuery documents registry, then pulls file bodies from Google Drive or GCS. Live invocation confirmed — BigQuery tool call executed, client project data returned.

Four client projects confirmed in the registry:

- Marriage Relationship App
- AIRIAD (operator internal)
- Amika
- Avatarmy

Any unauthenticated caller can invoke ContractAgent with any project name and receive the associated SOW, Change Requests, and BRD documents. The agent also calls `save_report` (writes to `analysis_reports/` on the host) and `convert_to_pdf` (Playwright — full headless browser exec on the host) as part of its standard workflow.

Contract documents contain: project scope, deliverables, milestones, team/role assignments, payment terms, change history.

CWE-359 (Exposure of Private Personal Information to an Unauthorized Actor — adapted for business data)

#### MEDIUM: Internal Dev Notes Embedded in Production System Prompt

ContractAgent instruction [8] contains explicit developer implementation context embedded directly in the production system prompt:

> "get_sow_document loads sanitized scope documents from the BigQuery documents registry and pulls file bodies from the registered backend (Google Drive or GCS) when credentials allow; otherwise it returns the artifact location or development fallback text if the project is not reporting-ready."

This is a development note describing fallback behavior, credential handling, and environment readiness states. It is live in production, readable without credentials, and exposes:
- BigQuery as the document registry backend
- Google Drive and GCS as the file body backends
- The concept of "reporting-ready" vs development state — indicating the backend is also used for dev/test runs against live data

CWE-615 (Inclusion of Sensitive Information in Source Code Comments — applied to exposed system prompts)

---

## Arsenal Chain Status

| Step | Tool | Result |
|---|---|---|
| 0 | JAXEN | Not run — manual squad dispatch |
| 1 | aimap | Ports 3000/7777 confirmed open. Port 7777: ZenML false positive on /health (same FP class as 35.200.236.6:9000). Actual: FastAPI/uvicorn AgentOS API. Port 3000: Next.js Agent UI. |
| 2 | VisorGraph | 0 nodes — no TLS cert on open ports, no pivot surface |
| 3 | aimap-profile | AI multi-agent platform, B2B risk analysis, client business data — no healthcare/HIPAA flag |
| 4 | JS-bundle | Not run — no extractable JS bundle surface on open ports |
| 5 | VisorLog | 1 event ingested to .db |
| 6 | VisorScuba | Not run this pass |
| 7 | BARE | Best match 0.461 (`exploit/multi/http/apache_apisix_api_default_token_rce`) — semantic overlap on "unauthenticated API default token." Not applicable. Novel class — no MSF coverage for unauth Agno AgentOS. |
| 8 | VisorCorpus | LLM-adjacent surface. Not run. |
| + | menlohunt | WireGuard UDP 51819-51821 open/filtered — internal VPN/service mesh. Not directly exploitable without peer keys. |
| + | Shodan | Not queried this pass |
| + | nu-recon | Not run |

**aimap note:** Port 7777 ZenML fingerprint fires on any `/health` returning 200 JSON — confirmed false positive class (same as 35.200.236.6:9000). Actual service identified via `/openapi.json` body and `/registry` response.

**BARE note:** No Metasploit module exists for unauth Agno AgentOS / FastAPI agentic platform invocation. Novel finding class — 0.461 best match is semantic, not functional.

---

## Intelligence Gaps

- No domain found for 34.57.75.173 — reverse DNS not resolved, no cert to pivot
- AIRIAD operator identity not confirmed — no public registration, no social presence found
- Marriage Relationship App: internal project name, no attribution
- GCS/Drive buckets behind ContractAgent not enumerated (ethical stop)
- Port 3000 Agent UI not exercised beyond existence confirmation
- crt.sh: no cert on either open port — no SAN pivot available

---

## Squad SPOT Summary

| Squad | Findings | Key Pivots | Confidence |
|---|---|---|---|
| Alpha (web) | 6 | Agent UI port 3000, full API schema, Avatarmy/Leon&Vera attribution, Amika/YC-F25 attribution | 0.91 |
| Bravo (infra) | 4 | GCP us-central1, uvicorn stack, WireGuard VPN candidates, ZenML FP documented | 0.87 |
| Charlie (social) | 7 | 4 client project names confirmed, Avatarmy=Leon&Vera=Jörg Olbing, Amika=Fixpoint/YC-F25, AIRIAD stealth/no-registration | 0.85 |
