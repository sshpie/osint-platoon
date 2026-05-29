```
┏━┓┏━┓╻┏┓╻╺┳╸   ┏━┓╻  ┏━┓╺┳╸┏━┓┏━┓┏┓╻
┃ ┃┗━┓┃┃┗┫ ┃    ┣━┛┃  ┣━┫ ┃ ┃ ┃┃ ┃┃┗┫
┗━┛┗━┛╹╹ ╹ ╹    ╹  ┗━╸╹ ╹ ╹ ┗━┛┗━┛╹ ╹
```

# OSINT Platoon

OSINT framework that runs inside Claude Code. Squads are parallel `Agent` subagents dispatched from a live Claude Code session. Each squad returns a SPOT report. The session synthesizes them into a SALUTE.

Doctrine: US Army ATP 3-21.8.

---

## Setup

```bash
git clone https://github.com/nuclide-research/osint-platoon
cd osint-platoon
claude
```

No pip install needed for the agentic path. Claude Code is the runtime.

---

## Usage

Inside your Claude Code session:

```
run the osint platoon on 1.2.3.4
```

```
run the osint platoon on example.com
```

```
run the osint platoon on "Acme Corp"
```

Claude Code reads squad templates from `platoon/squads/`, dispatches Alpha / Bravo / Charlie / Weapons in parallel, and synthesizes SPOT reports into a SALUTE. The full NuClide arsenal chain runs on every target.

**Depth:**

| Keyword | Behavior |
|---------|----------|
| `hasty` | Single pass, web + infra only |
| `deliberate` | Full squad dispatch, one iteration (default) |
| `detailed` | Full squads, up to 3 replan iterations |

**Pivots:** If a squad surfaces a new IP, domain, or cert chain, say `follow the pivot on X` and Bravo re-tasks off it.

**Dry run:** `python cli.py --target example.com --dry-run` prints the METT-TC plan without firing squads.

---

## Architecture

```
Claude Code Session (Orchestrator)
  │
  ├── Agent: Squad Alpha    — Web recon (news, mentions, breach data, paste sites)
  ├── Agent: Squad Bravo    — Infrastructure (DNS, WHOIS, crt.sh, ASN, cert pivots)
  ├── Agent: Squad Charlie  — Social footprint (usernames, profiles, cross-platform)
  └── Agent: Weapons Squad  — Document intel + full NuClide arsenal chain
```

Each squad returns a SPOT report (Size / Activity / Location / Unit / Time / Equipment). The orchestrator synthesizes all four into a SALUTE and replans off discovered pivots.

---

## Arsenal

Every target runs the full chain:

| Step | Tool | What it does |
|------|------|---------|
| 0 | JAXEN | Shodan harvest → empire.db |
| 1 | aimap | Service fingerprint + deep enum (36 AI/ML services) |
| 2 | VisorGraph | Cert pivot → operator attribution |
| 3 | aimap-profile | Target classification + ethics flags |
| 4 | JS-bundle | Hidden API / secret extraction |
| 5 | VisorLog | Ledger ingest → nuclide.db |
| 6 | VisorScuba | Compliance scoring |
| 7 | BARE | Module ranking against 3,904 Metasploit entries |
| 8 | VisorCorpus | Corpus analysis for LLM-adjacent surfaces |

Null result = result. Nothing skipped.

---

## Case Studies

| Target | Operator | Finding |
|--------|----------|---------|
| [`34_111_184_20/`](34_111_184_20/) | Business Insider (Axel Springer) | Atlantis v0.32.0 fully unauthenticated. 5 active prod Terraform locks (Snowflake, BigQuery admin, data-eng-prod) readable and discardable without credentials. Disclosed 2026-05-28. |
| [`5_78_67_23/`](5_78_67_23/) | Voomi Supply LLC | Elasticsearch superuser credentials in plaintext Temporal schedule configs. Unauthenticated Temporal UI. Walmart + Amazon catalog pipelines in blast radius. Disclosed 2026-05-28. |
| [`40_160_235_43/`](40_160_235_43/) | Fluid Attacks security engineer (personal VPS) | Python SimpleHTTPServer serving full home directory. 33+ AI agent credential files exposed: Anthropic, OpenAI org-owner, GCP Vertex, GitHub PAT (taker — Fluid Attacks pentest pipeline). Credentials in hand. |
| [`35_200_236_6/`](35_200_236_6/) | Pukaar.ai (Prakarann Innovation Lab) | Three unauthenticated FastAPI/Uvicorn inference APIs. Baby health inference (prod environment flag, live child_id/user_id), LightRAG pediatric diagnostic pipeline, Video RAG search. 50,000+ children's health profiles in blast radius. India DPDP Act 2023 violation. |
| [`34_57_75_173/`](34_57_75_173/) | AIRIAD (stealth/pre-launch) | Agno v2.6.1 AgentOS API fully unauthenticated. Five production agents invocable. ContractAgent executes live BigQuery calls against client contract registry. Four client projects confirmed: Marriage Relationship App, Amika (YC F25), Avatarmy (Leon & Vera OÜ), AIRIAD. |

Each directory has a `case-study.md` (SALUTE), `findings-breakdown.txt` (plain-English impact), `poc.txt` (reproducible PoCs), and `screenshots/`.

---

## Standalone CLI

```bash
pip install -r requirements.txt
cp .env.example .env  # add ANTHROPIC_API_KEY

python cli.py --target example.com --type domain --depth deliberate
python cli.py --target 1.2.3.4 --type domain --depth detailed
python cli.py --target example.com --dry-run
```

---

## Rules of Engagement

- Passive collection and open-surface enumeration only
- No logins, no form submissions, no destructive operations
- Stop once a finding is proven
- Disclose
