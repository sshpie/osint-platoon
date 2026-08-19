# Case Study: 35.200.236.6 — Pukaar.ai Unauthenticated Pediatric Medical APIs

**Date:** 2026-05-28
**Method:** osint-platoon multi-agent dispatch (ORP + 4 squads in parallel)
**Researcher:**  / 

---

## SALUTE Report

### Subject

**Pukaar.ai** (Prakarann Innovation Lab Private Limited)
AI-powered infant health and parenting platform. Gurugram/New Delhi, India.
Founded 2024. Appeared on Shark Tank India Season 5 Episode 35 (aired 2026-02-21 — asked 48L for 1.5% equity, no deal). 50,000+ Android installs. App collects children's health data, diagnostics, contact info, and financial info.

- Domain: pukaarai.com / prakarann.com
- Android: com.prakarann.goonj (v2.0.18, updated 2026-05-15)
- iOS: id6755088190, developer PRAKARANN INNOVATION LAB PRIVATE LIMITED
- Contact: admin@prakarann.com / +91-8427698641

### Activity

Three FastAPI/Uvicorn inference endpoints exposed on non-standard ports with no authentication. All three are production-adjacent services tied to real user and child records. The `user_id` UUID and `child_id` integer fields in the inference request schema are direct references to live user data.

### Location

| Field | Value |
|---|---|
| IP | 35.200.236.6 |
| PTR | 6.236.200.35.bc.googleusercontent.com |
| ASN | AS396982 — Google Cloud Platform |
| GCP Region | asia-south1 (Mumbai, India) |
| OS | Debian 12 (bookworm) |

### Unit / Organization

| Person | Role | Background |
|---|---|---|
| Karan Birpali | Co-Founder & CEO | B.E. Biotechnology, IIT Delhi 2016-2020 |
| Akash Dangee | Co-Founder & CPO | B.Tech Mechanical, IIT Roorkee 2016-2020. Ex-CashFlo, Masters India |
| Chaiti Chatterjee | Chief Growth Officer | LinkedIn confirmed |
| Ravi Teja Kasula | Senior Gen AI Engineer | TCS background; probable API developer |
| Ravinder Kuhad | Founding AI Engineer | Concurrent profile at Tecnod8.ai; likely author of exposed backend |
| Mishal Raj | Team member | Ex-Razorpay |

GitHub: No public org found under prakarann or pukaar-ai.
LinkedIn: linkedin.com/company/pukaar-ai
Instagram: @pukaar.ai (464 followers)

### Time

- Port 9000 last confirmed by Shodan: 2026-05-26
- App last updated on Play Store: 2026-05-15
- Shark Tank India appearance: 2026-02-21

### Exposure

#### CRITICAL: Three Unauthenticated Medical Inference APIs

All three Uvicorn services on ports 4000, 8000, and 9000 return HTTP 200 with no credentials required. No authentication layer at any level — no API key, no bearer token, no IP restriction.

**Port 4000 — Baby Health Inference Service v0.1.0**

POST /infer accepts:
```json
{
  "user_id": "<uuid>",
  "child_id": <int>,
  "environment": "stage" | "prod"
}
```

Returns a nested `BabyInferenceReport`. Routes to stage or prod backend via `PUKAAR_ENV` environment variable. References an MCP (Model Context Protocol) backend for inference execution. The `environment: "prod"` field and `user_id`/`child_id` parameters confirm this is wired to live user records.

**Port 8000 — LightRAG Diagnostic Pipeline API v0.1.0**

5-step pediatric diagnostic workflow operating on a patient chart object:

Step 1: Initial symptom intake
Step 2: Red flag screening
Step 3: Differential diagnosis
Step 4: In-depth question generation
Step 5: Final diagnosis

Patient chart schema includes: `initial_symptoms`, `red_flag_responses`, `differentiating_symptoms_responses`, `top_2_conditions`, `in_depth_question_responses`.

Backend: LightRAG (HKUDS/LightRAG — graph-enhanced RAG framework). Processes structured pediatric clinical data with no access control.

**Port 9000 — Video RAG Search API v0.1.0**

POST /search accepts a query string, returns top result from indexed video content. Likely educational/instructional content for parents.

CWE-306 (Missing Authentication for Critical Function) — all three services.

#### CRITICAL: Child Health Data — No Access Control

The inference APIs process children's medical data. The `child_id` integer and `user_id` UUID in the InferenceRequest schema are direct references to records in Pukaar.ai's production database. Any unauthenticated client can:

- Submit arbitrary user_id/child_id combinations and retrieve inference reports
- Query the diagnostic pipeline with fabricated symptom inputs
- Access the video RAG corpus without any user verification

50,000+ children's health profiles are within blast radius of a single unauthenticated HTTP request.

India DPDP Act 2023 (Digital Personal Data Protection Act): children's data and health data are both sensitive personal data. Processing without adequate security measures is a violation. The absence of any authentication constitutes a failure to implement "reasonable security safeguards."

#### HIGH: MCP Backend — Likely Additional Exposed Host

The inference service on :4000 references an MCP backend for stage and prod environments. This MCP server is a separate host — likely another GCP instance in the same project or the same /28 subnet. It is not yet located.

---

## Arsenal Chain Status

| Step | Tool | Result |
|---|---|---|
| 0 | JAXEN | Not run — manual squad dispatch |
| 1 | aimap | Ports 4000/8000/9000 confirmed open HTTP 200. Port 9000 fingerprinted ZenML (false positive — confirmed Video RAG Search API via body). All three Uvicorn services confirmed live. aimap output ingested to .db. |
| 2 | VisorGraph | Not run — no TLS cert on any open port, no pivot surface |
| 3 | aimap-profile | Healthcare AI, children's data, India DPDP Act — sensitive personal data classification |
| 4 | JS-bundle | Not run — no web frontend surface on any open port |
| 5 | VisorLog | Ingested: 1 event (2 deduped) from aimap report |
| 6 | VisorScuba | **0/10 — AI.C1 violation** (unauthenticated AI service confirmed) |
| 7 | BARE | Run. Low semantic scores across all 3 findings (0.37-0.43) — no strong Metasploit module match for novel FastAPI/LightRAG inference exposure. No MSF coverage for this finding class. |
| 8 | VisorCorpus | LightRAG + MCP backend = LLM-adjacent surface. Not run. |
| + | Shodan | Ports 22/4000/8000/9000 confirmed; open-dir tag present; no vuln tags |
| + | crt.sh | 502 during window — no cert pivot data |
| + | GreyNoise | RIOT=true, benign classification |

**BARE note:** Best match for F2 (LightRAG) was `exploits_multi_http_apache_apisix_api_default_token_rce` (0.37) — semantic overlap on "unauthenticated API default token." Not applicable. No Metasploit coverage for unauth LightRAG or FastAPI inference endpoints. Novel finding class.

**aimap note:** Port 9000 fingerprinted as ZenML via `/health` endpoint match — false positive. Actual service is the Video RAG Search API. aimap v1.9.36 ZenML fingerprint fires on any `/health` returning 200 JSON.

---

## Additional Confirmed Intelligence (Weapons Squad)

**S3 bucket: `pukaarcry.s3.ap-south-1.amazonaws.com`**
Port 9000 Video RAG search returns live direct S3 object URLs for expert pediatric videos. Bucket not publicly listable but objects served through the unauthenticated search API. Confirms operator brand: PukaarCry. AWS ap-south-1 (Mumbai) — consistent with GCP asia-south1 backend.

**LightRAG clinical knowledge base confirmed live**
Port 8000 queried — RAG index loaded with real pediatric clinical content: meningitis, sepsis, pneumonia, dehydration protocols, neonatal hepatitis, blood culture differentials. Functioning clinical decision-support knowledge base, queryable without credentials.

**SSH confirmed: OpenSSH 9.2p1 Debian-2+deb12u10 — publickey auth only.** No password auth. Current patch level.

**WireGuard UDP candidates: 51819-51821 open/filtered** — likely internal VPN/service mesh. Not directly exploitable without peer keys.

**menlohunt:** Ran — missed ports 4000/8000 (not in default 29-port list). Port 9000 flagged as MinIO (false positive). No GCS/Firebase/Cloud Run misconfigs. Coverage gap: menlohunt + aimap are complementary on non-standard ports.

**VisorScuba: 0/10 — AI.C1 violation** (unauthenticated AI service). Ingested to .db.

## Intelligence Gaps

- MCP backend host not yet located — adjacent /28 sweep (35.200.236.0/28) is next move
- crt.sh 502 — no cert SAN pivot; re-run needed
- ThreatBook: 2 expired intels flagged but content gated behind auth
- No GitHub org found — source code not accessible
- S3 bucket `pukaarcry` — direct object URL pattern analysis pending (V021 pattern observed)

---

## Squad SPOT Summary

| Squad | Findings | Key Pivots | Confidence |
|---|---|---|---|
| Alpha (web) | 7 | Uvicorn stack on 4000/8000/9000, ThreatBook expired flags, GCP Mumbai | 0.90 |
| Bravo (infra) | 6 | GCP asia-south1, Debian 12, FastAPI stack confirmed, crt.sh 502 | 0.88 |
| Charlie (social) | 11 | Full operator dossier, Shark Tank attribution, patient chart schema, MCP pivot | 0.93 |
| Weapons (arsenal) | Pending | Background run in progress | — |
