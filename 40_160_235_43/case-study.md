# Case Study: 40.160.235.43 — Fluid Attacks Engineer Credential Dump

**Date:** 2026-05-28
**Method:** osint-platoon multi-agent dispatch (ORP + 4 squads in parallel)
**Researcher:**  / 

---

## SALUTE Report

### Subject

Personal research VPS operated by **Cristian Vargas**, security engineer at **Fluid Attacks**.

- Email: cristian.vargas@fluidattacks.com / cvargas@fluidattacks.com / dthmchg@gmail.com
- GitHub: github.com/tachote
- Org: Fluid Attacks (Bogota/Medellin, Colombian AppSec firm, MITRE CNA, 156 CVEs published)

Fluid Attacks offers continuous hacking, SAST/DAST/SCA/CSPM/PTaaS. The operator is a working security researcher — not a company production asset.

### Activity

Python SimpleHTTPServer on port 8080 serving the full `/home/ubuntu` home directory without authentication. 68 browsable entries including dotfile directories for 33+ AI agent tools. Full credential material across every major LLM platform accessible in the clear.

### Location

| Field | Value |
|---|---|
| IP | 40.160.235.43 |
| PTR | vps-a016bd38.vps.ovh.us |
| ASN | AS16276 — OVH US LLC |
| Netblock | 40.160.234.0/23 (registered 2024-06-27) |
| Datacenter | OVH US LZ-PAO, San Jose CA |

### Unit / Organization

Personal VPS — not Fluid Attacks company infrastructure. SSH `authorized_keys` reference a prior Hetzner NBG1 machine (`brewuser@ubuntu-4gb-nbg1-1`), indicating this is a personal dev/research box.

**No company production credentials or client data identified.**

### Time

- Shodan `open-dir` tag active at last crawl (2026-05-24)
- Port 8080 was live at Shodan scan time; intermittent at assessment time
- OVH netblock registered: 2026-06-27

### Exposure

#### CRITICAL: Unauthenticated Home Directory Listing

Python SimpleHTTPServer (Python 3.13.3) on :8080 serving full home directory. No authentication, no IP restriction. Single HTTP GET to `http://40.160.235.43:8080/` returns a browsable directory listing of the researcher's working environment.

CWE-548 (Exposure of Information Through Directory Listing)

#### CRITICAL: LLM Platform Credential Exposure

The following credential classes were found in the exposed filesystem. **Actual values are not reproduced here.**

| File | Credential Class | Platform | Account |
|---|---|---|---|
| `.claude/.credentials.json` | OAuth access + refresh token | Anthropic Claude Code | Team subscription |
| `.codex/auth.json` | JWT access + refresh token | OpenAI ChatGPT | Team plan, org owner role, `cvargas@fluidattacks.com` |
| `.openclaw/.env` | API key | Gemini | — |
| `.openclaw/.env` | API key | OpenRouter | — |
| `.openclaw/.env` | Bearer token | GCP Vertex AI | Live at time of collection |
| `.openclaw/.env` | API key | Perplexity | — |
| `.openclaw/.env` | API key | OpenCode | — |
| `.openclaw/.env` | Bot token | Telegram | — |
| `.gemini/oauth_creds.json` | Google OAuth access + refresh | Google Cloud (`cloud-platform` scope) | `dthmchg@gmail.com` |

CWE-312 (Cleartext Storage of Sensitive Information) / CWE-522 (Insufficiently Protected Credentials)

#### HIGH: GitHub Personal Access Token

`.config/gh/hosts.yml` — PAT for GitHub user `tachote`. Full repo read/write access. **Value not reproduced.**

#### HIGH: Anonymous MQTT Broker — ICS/OT Telemetry

`zb.conf`: Mosquitto MQTT on :1884, `allow_anonymous true`. Broker live at time of scan (port confirmed open).

`zb_capture.log` shows MQTT topic stream from `fleet/site-042`:
- `fleet/site-042/public/telemetry/hmi` — pump/pipeline telemetry (tank level, line pressure, flow rate, pump speed, valve position, alarm states)
- `fleet/site-042/internal/hmi/operator-credentials` — operator credentials published in plaintext across 20+ format variations

ICS topology (`ics/topology.png`): Internet → HMI + S7 Proxy + Siemens S7 PLC → Wind Turbine T02.

**Assessment:** The `pwnedvps` credential string and format-enumeration log pattern indicate a research simulation, not live OT infrastructure. Consistent with ICS security research or CTF preparation. External MQTT clients observed connecting (`149.6.129.245`, `38.225.225.60`) — whether those are controlled research clients or incidental is unknown.

#### MED: CUPS :631 — CVE-2024-47176 Surface

CUPS 2.4.19 on :631. Returns 403. CVE-2024-47176 / CVE-2024-47177 (Sept 2024 CUPS RCE chain) affects publicly exposed CUPS/IPP. Version not confirmed against patched range — requires banner grab with full CUPS version string.

#### MED: Personal Financial PII

`workspace/` contains a personal debt tracker web app with Colombian bank account balances, credit card details, and loan amounts (Bancolombia, Scotiabank Colpatria, Lulo Bank). Personal data — not in scope for further analysis.

---

## Arsenal Chain Status

| Step | Tool | Result |
|---|---|---|
| 0 | JAXEN | Not run — manual squad dispatch |
| 1 | aimap | F1 CRIT: open-dir :8080; SSH dir, Claude config, OpenHands config exposed |
| 2 | VisorGraph | Module not found in current Python env — not run |
| 3 | aimap-profile | Script not found at expected path — not run |
| 4 | JS-bundle | Not applicable — no web app surface |
| 5 | VisorLog | Pending ingest |
| 6 | VisorScuba | Pending |
| 7 | BARE | Binary present, input schema error — not run productively |
| 8 | VisorCorpus | 33+ AI agent directories present — high LLM-adjacent surface |
| + | crt.sh | 502 during assessment window — no cert pivot data |
| + | Shodan InternetDB | Ports 22, 631, 8080 confirmed; open-dir tag present |

---

## Intelligence Gaps

- Port 8080 was intermittent — full directory listing not confirmed live at assessment time
- crt.sh 502 during window — no cert SAN/CN pivots available
- CUPS version not confirmed against CVE-2024-47176 patch boundary
- External MQTT clients (`149.6.129.245`, `38.225.225.60`) — identity unknown; may be researcher-controlled

---

## Squad SPOT Summary

| Squad | Findings | Key Pivots | Confidence |
|---|---|---|---|
| Alpha (web) | 7 | Fluid Attacks operator ID, tachote GitHub, OVH VPS, no threat feed hits | 0.93 |
| Bravo (infra) | 6 | AS16276 OVH, PTR vps-a016bd38, port 631 CUPS, crt.sh 502 | 0.88 |
| Charlie (social) | 9 | Full operator dossier: Cristian Vargas, fluidattacks, tachote repos, financial PII | 0.91 |
| Weapons (arsenal) | 10 | F1 dir listing → F2-F10 credential chain; MQTT broker live | 0.90 |
