```
┏━┓┏━┓╻┏┓╻╺┳╸   ┏━┓╻  ┏━┓╺┳╸┏━┓┏━┓┏┓╻
┃ ┃┗━┓┃┃┗┫ ┃    ┣━┛┃  ┣━┫ ┃ ┃ ┃┃ ┃┃┗┫
┗━┛┗━┛╹╹ ╹ ╹    ╹  ┗━╸╹ ╹ ╹ ┗━┛┗━┛╹ ╹
```

# OSINT Platoon

Multi-agent OSINT framework built to run natively inside **Claude Code**. Squads are Claude Code `Agent` tool subagents — not subprocess calls, not API wrappers. The orchestrator dispatches parallel agents from inside an active Claude Code session, collects SPOT reports, and synthesizes a SALUTE final product.

Structured on US Army ATP 3-21.8 infantry platoon doctrine.

---

## Using with Claude Code

### Setup

```bash
git clone https://github.com/Nicholas-Kloster/osint-platoon
cd osint-platoon
claude   # open Claude Code in this directory
```

That's it. No API key config, no pip install for the agentic path. Claude Code is the runtime.

### Running an assessment

Inside your Claude Code session, hand it a target:

```
run the osint platoon on 1.2.3.4
```

```
run the osint platoon on example.com
```

```
run the osint platoon on "Acme Corp"
```

Claude Code acts as the orchestrator. It reads the squad templates from `platoon/squads/`, dispatches Alpha / Bravo / Charlie / Weapons as parallel `Agent` subagents, and synthesizes their SPOT reports into a SALUTE final product. The full NuClide arsenal chain runs as part of the Weapons squad pass.

### What Claude Code does automatically

- Dispatches squads in parallel (base-of-fire + bounding movement pattern)
- Replans after each iteration based on discovered pivots
- Writes `{target_slug}/case-study.md` and `findings-breakdown.txt` as deliverables
- Runs all 9 arsenal steps — null results logged, nothing silently skipped
- Captures screenshots and PoC evidence for any confirmed findings

### Depth control

Tell Claude Code the depth in your prompt:

| Phrase | Behavior |
|--------|----------|
| `hasty` | Single-pass, fast — web + infra only |
| `deliberate` | Full squad dispatch, one iteration |
| `detailed` | Full squads, up to 3 replan iterations |

Default when unspecified is `deliberate`.

### Tips

- Run from the repo root so relative paths resolve correctly
- If a squad comes back with a pivot (new IP, new domain, cert chain), say `follow the pivot on X` and Claude Code will re-task Bravo off it
- The `--dry-run` flag on `cli.py` prints the METT-TC plan without dispatching squads — useful for previewing tasking before a live run

---

## How It Actually Works

Squads are Claude Code `Agent` tool subagents — not subprocess calls, not API wrappers. The orchestrator dispatches parallel agents from inside the active Claude Code session, collects SPOT reports, and synthesizes the SALUTE final product.

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
