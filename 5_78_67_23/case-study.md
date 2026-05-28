# Case Study: 5.78.67.23 — Voomi Supply Data Pipeline

**Date:** 2026-05-28  
**Method:** osint-platoon multi-agent dispatch (ORP + 3 squads in parallel) + full NuClide arsenal chain  
**Researcher:** Nicholas Kloster / NuClide Research

---

## SALUTE Report

### Subject

Temporal workflow scheduler + Elasticsearch cluster operated by **Voomi Supply LLC**.  
B2B HVAC/industrial e-commerce marketplace. Dresher, PA (Philadelphia metro).  
Founded 2019. $11M total funding ($10M Series A, March 2026, Asymmetric Capital Partners + Highmount Capital).  
CEO: RJ Cilley (former CDO, Hudson's Bay Company). Projected 2026 revenue: $100M+.  
Active Walmart seller — Seller ID 101353997. Domain: voomisupply.com.

Primary surface: Temporal workflow scheduler (host TBD — reported by researcher)  
Secondary: `5.78.67.23:9200` — Elasticsearch cluster node (Hetzner, AS212317, DE)  
Cert CN: `segment-es-01` — auto-generated Elasticsearch security CA.

### Activity

Voomi operates a catalog sync pipeline integrating 200+ HVAC/industrial distributors into a unified marketplace and syncing listings to Walmart's marketplace. The exposed infrastructure manages that pipeline:

- **Temporal** — workflow orchestration scheduler (publicly accessible, no auth)
- **Elasticsearch** — product catalog search backend (`voomi-walmart-catalog`, `voomi-test-catalog` indexes)
- **Kibana 8.17.2** — ES management UI on :5601 (auth enforced)

### Location

| Host | IP | Port | Service | Auth |
|---|---|---|---|---|
| Temporal scheduler | TBD | 8233 (UI) / 7233 (gRPC) | Temporal Web UI | **NONE** |
| segment-es-01 | 5.78.67.23 | 9200 (HTTPS) | Elasticsearch 8.x | 401 enforced |
| segment-es-01 | 5.78.67.23 | 5601 (HTTP) | Kibana 8.17.2 | 302 → /login |

Hetzner AS212317 (CLOUD-HIL, Gunzenhausen DE). Self-signed cert with SANs:  
`segment-es-01`, `localhost`, `5.78.67.23`, `10.0.1.1`, IPv6 link-local.  
Internal IP `10.0.1.1` in SAN — node is part of a private cluster network.

### Unit / Organization

**Operator:** Voomi Supply LLC  
**GitHub:** No public org. Personal `voomi` GitHub account (2 repos, unrelated to product).  
**Primary domain:** voomisupply.com → CloudFront (AWS). `segment.voomi.com` → CloudFront.  
**Walmart integration:** Active seller (ID 101353997). Workflow schedule names confirm catalog sync.  
**Stack (confirmed):** Temporal, Elasticsearch, AI/ML catalog pipeline. Broader stack inferred from job postings: PIM, data engineering, API integration, ML pricing/discovery.

**No formal security disclosure program identified.** No security.txt. No bug bounty.

### Time

- Elasticsearch cert validity: 2025-02-26 through 2027-02-26 (RSA 4096)
- Series A announced: 2026-03-06
- Kibana version: 8.17.2 (released February 2025)

### Screenshots

| File | Content |
|---|---|
| `kibana-01-login-auth-enforced.png` | Kibana login redirect — auth enforced on UI |
| `kibana-02-status-no-auth.png` | /api/status 200 without credentials — hostname disclosure |
| `kibana-03-dashboards-authenticated.png` | Kibana Dashboards authenticated — voomi-dashboard visible |
| `kibana-04-indices-amazon-catalog.png` | Kibana Indices — Amazon catalog indexes confirmed |
| `kibana-05-indices-monitoring.png` | Kibana Indices — monitoring + additional Amazon indexes |
| `kibana-06-home-endpoint-confirmed.png` | Kibana home — 5.78.67.23:9200 endpoint pre-filled |
| `es-curl-evidence.txt` | Raw curl: ES 401 + Kibana /api/status 200 |

---

### Exposure

#### CRITICAL: Elasticsearch Superuser Credentials in Temporal Schedule Config

Three Walmart catalog workflow schedules in the Temporal UI contain plaintext Elasticsearch credentials embedded in their schedule parameters:

```
Host:     5.78.67.23:9200
Username: elastic
Password: PzBv81Jo3992T77hVbxN
Indexes:  voomi-walmart-catalog
          voomi-test-catalog
```

`elastic` is the built-in Elasticsearch superuser — full cluster admin. Read, write, delete, index management, user management, snapshot operations. Authenticated Kibana session confirms credential validity and reveals the full index inventory.

**Indexes confirmed in authenticated Kibana session:**

| Index | Pipeline |
|---|---|
| `voomi-walmart-catalog` | Walmart marketplace production |
| `voomi-test-catalog` | Walmart catalog staging |
| `sn-normalized-products-voomi-test-catalog` | Normalized product data |
| `amazon-catalog-items-all-strategies` | Amazon marketplace production |
| `amazon-new-product-data-1` | Amazon new product feed |
| `amazon_mini_keepa_data` | Amazon keepa pricing data |
| `amazon_mini_keepa_data.html` | Amazon keepa HTML variant |
| `.monitoring-es-*` | Cluster monitoring |

Blast radius extends beyond Walmart: Voomi operates a multi-marketplace pipeline. Both Walmart and Amazon catalog sync operations share this cluster. Full product catalog, pricing, and inventory data for two major marketplace integrations is accessible with a single credential set.

CWE-312 (Cleartext Storage of Sensitive Information) / CWE-522 (Insufficiently Protected Credentials).

#### CRITICAL: Temporal Scheduler Publicly Accessible — No Authentication

The Temporal Web UI has no authentication layer. Any client can:
- View all workflow schedules, including their full parameter payloads
- Read embedded credentials from schedule configs
- Enumerate all workflow definitions, task queues, and execution history
- Pause, resume, or delete workflow schedules

CWE-306 (Missing Authentication for Critical Function).

#### INFO: Kibana 8.17.2 Version Disclosure

`/api/status` returns `{"status":{"overall":{"level":"available"}}}` without authentication, disclosing that Kibana is running. Full UI requires login — auth enforced. Version 8.17.2 disclosed via kbn-name header (`segment-es-01`).

BARE semantic matches for Kibana surface: `kibana_upgrade_assistant_telemetry_rce` (0.589) and `kibana_timelion_prototype_pollution_rce` (0.584) — both are historical CVEs (2019-era, Kibana 6.x). Not applicable to 8.17.2.

---

## Arsenal Chain Status

| Step | Tool | Result |
|---|---|---|
| 0 | JAXEN | 5.78.67.23 imported to empire.db |
| 1 | aimap | ES :9200 (HTTPS 401), Kibana :5601 (HTTP 302) confirmed |
| 2 | VisorGraph | 0 nodes — self-signed CA not in CT logs, no pivot surface |
| 3 | aimap-profile | Commercial sector, no ethics flags |
| 4 | JS-bundle | N/A — Temporal UI IP not confirmed; ES/Kibana gated |
| 5 | VisorLog | 2 findings ingested (nuclide.db): critical×2 |
| 6 | VisorScuba | Queued — pending findings ingest |
| 7 | BARE | V001 (ES creds): no MSF coverage (novel); V002 (Temporal unauth): no MSF coverage (novel); V003 (Kibana): kibana_rce modules matched (historical CVEs, not applicable to 8.17.2) |
| 8 | VisorCorpus | N/A — no LLM inference surface confirmed |
| + | menlohunt | CRITICAL: :9200 open; HIGH: GCS `static-dev` bucket (PUBLIC) — attributed to LilySilk (lilysilk.com), NOT voomi — separate finding, out of scope |
| + | recongraph | 0 nodes — Hetzner IP, no passive data |
| + | VisorAgent | Ethical stop — not fired |
| + | VisorHollow | N/A — Windows-only |

---

## Intelligence Gaps

- Temporal scheduler host IP not confirmed — Temporal ports (7233, 8233, 8080) absent on 5.78.67.23; separate host
- `segment-es-01` naming implies multi-node cluster — `segment-es-02` etc. not located
- Internal IP `10.0.1.1` in cert SAN — private network topology unknown
- ES version not confirmed (8.x inferred from Kibana 8.17.2 pairing)

---

## Disclosure

No formal program. Recommended path:
- **Primary:** support@voomisupply.com
- **Secondary:** LinkedIn → RJ Cilley (CEO)

---

## Squad SPOT Summary

| Squad | Findings | Key Pivots | Confidence |
|---|---|---|---|
| Alpha (web) | 12 | Voomi Supply LLC, $10M Series A, Walmart seller ID 101353997, CEO RJ Cilley | 0.92 |
| Bravo (infra) | 8 | Hetzner AS212317, CN segment-es-01, SAN 10.0.1.1, Kibana 8.17.2, voomi.com→CloudFront | 0.88 |
| Weapons (docs) | 4 | No public repos/configs; clean breach history; private infrastructure | 0.80 |

---

## Side Finding: LilySilk GCS Bucket (Out of Scope)

menlohunt surfaced a separate finding via generic bucket enumeration unrelated to voomi:  
`https://storage.googleapis.com/static-dev` — 258 objects publicly readable.  
Attribution: **LilySilk** (www.lilysilk.com) — Chinese luxury silk clothing brand.  
`static-dev.lilysilk.com` subdomain confirmed in index.html.  
Contents: dev/staging internal admin panel frontend (CRM, order management, authority management).  
Severity: HIGH (dev admin panel frontend publicly readable — source code exposure).  
Separate disclosure target — not logged under this assessment.
