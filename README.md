# OSINT Platoon

Multi-agent OSINT framework built to run natively inside **Claude Code**. Squads are Claude Code `Agent` tool subagents — not subprocess calls, not API wrappers. The orchestrator dispatches parallel agents from inside an active Claude Code session, collects SPOT reports, and synthesizes a SALUTE final product.

Structured on US Army ATP 3-21.8 infantry platoon doctrine.

---

## How It Actually Works

This runs **inside Claude Code** as an agentic session. Not a standalone scanner you pipe targets into.

1. Open Claude Code (`claude`) in this directory
2. Hand the orchestrator a target IP, domain, or operator name
3. The orchestrator dispatches 3-4 parallel `Agent` subagents (squads)
4. Squads return SPOT reports; orchestrator synthesizes the SALUTE
5. Full NuClide arsenal runs against the target (aimap, VisorGraph, BARE, VisorLog, etc.)

The `platoon/` directory contains squad prompt templates. `cli.py` is a standalone fallback for non-interactive use — the agentic path is the primary one.

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

Squads run in parallel via the Claude Code `Agent` tool. Each returns a **SPOT report** (Size / Activity / Location / Unit / Time / Equipment mapped to OSINT fields). Orchestrator synthesizes all four into a **SALUTE** final product and replans based on discovered pivots.

**Doctrinal basis:** ATP 3-21.8 Troop Leading Procedures, METT-TC(I), base-of-fire + bounding movement execution, CCIR/PIR tasking, GOTWA handoffs.

---

## NuClide Arsenal Integration

Every target runs the full 9-step chain:

| Step | Tool | Purpose |
|------|------|---------|
| 0 | JAXEN | Shodan harvest → empire.db |
| 1 | aimap | Service fingerprint + deep enum (36 AI/ML services) |
| 2 | VisorGraph | Cert pivot → operator attribution |
| 3 | aimap-profile | Target classification + ethics flags |
| 4 | JS-bundle | Hidden API / secret extraction |
| 5 | VisorLog | Ledger ingest → nuclide.db |
| 6 | VisorScuba | Compliance scoring |
| 7 | BARE | Module relevance ranking (3,904 Metasploit entries) |
| 8 | VisorCorpus | Corpus analysis (LLM-adjacent surfaces) |

Null result = result. Every step runs; none are conditional.

---

## Case Studies

Real research outputs from live Claude Code agentic sessions:

| Target | Operator | Findings |
|--------|----------|---------|
| [`34_111_184_20/`](34_111_184_20/) | Business Insider / Insider Inc. (Axel Springer) | CRITICAL: Atlantis v0.32.0 unauthenticated Terraform runner. 5 active production locks (Snowflake, BigQuery admin, data-eng-prod) fully readable and discardable without credentials. Disclosed 2026-05-28. |
| [`5_78_67_23/`](5_78_67_23/) | Voomi Supply LLC | CRITICAL: Elasticsearch superuser credentials in plaintext Temporal workflow schedule configs. Unauthenticated Temporal UI. Blast radius covers Walmart + Amazon catalog pipelines. Disclosed 2026-05-28. |

Each case study directory contains:
- `case-study.md` — SALUTE report with operator profile, arsenal chain status, squad SPOT summary
- `findings-breakdown.txt` — plain-English per-finding breakdown (business impact, attack paths, what an attacker can do right now)
- `poc.txt` — reproducible PoCs with expected output
- `screenshots/` — visual evidence

---

## Standalone CLI (Fallback)

For use outside Claude Code:

```bash
pip install -r requirements.txt
cp .env.example .env
# add ANTHROPIC_API_KEY

python cli.py --target example.com --type domain --depth deliberate
python cli.py --target 1.2.3.4 --type ip --depth detailed
python cli.py --target example.com --dry-run   # METT-TC plan only
```

---

## Output

- `reports/SALUTE_{target}_{timestamp}.md` — final intelligence product
- `logs/mission_{id}.jsonl` — structured mission log with token usage
- `{target_slug}/case-study.md` — full case study (agentic sessions)
- `{target_slug}/findings-breakdown.txt` — per-finding deliverable

---

## Rules of Engagement

- Passive collection and open-surface enumeration only
- No logins, no form submissions, no destructive operations
- Stop short of full impact once a finding is proven
- Disclose responsibly
