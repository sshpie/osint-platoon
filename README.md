# OSINT Platoon

Multi-agent OSINT system structured on US Army ATP 3-21.8 infantry platoon doctrine.

## Architecture

```
Platoon Leader (Orchestrator) — claude-opus-4-7, adaptive thinking
  ├── Squad Alpha    — Web Recon (news, mentions, breach data, paste sites)
  ├── Squad Bravo    — Infrastructure (DNS, WHOIS, crt.sh, ASN attribution)
  ├── Squad Charlie  — Social Footprint (usernames, profiles, cross-platform)
  └── Weapons Squad  — Document Intel (PDF/DOCX metadata, author leaks)
```

**Doctrinal basis:** 8-Step Troop Leading Procedures (TLP), METT-TC(I) analysis, SPOT reports, SALUTE final product, base-of-fire + bounding movement execution pattern.

**Execution pattern:** Alpha + Charlie run in parallel (base of fire). Bravo bounds off Alpha's domain pivots. Weapons synthesizes across all three. Orchestrator replans after each iteration using discovered pivots.

## Install

```bash
pip install -r requirements.txt
cp .env.example .env
# add your ANTHROPIC_API_KEY to .env
```

## Usage

```bash
# Domain recon
python cli.py --target example.com --type domain --depth deliberate

# Person / username
python cli.py --target "Jane Doe" --type person --depth hasty

# Deep multi-iteration
python cli.py --target example.com --type domain --depth detailed --max-iterations 3

# Dry run — METT-TC plan without dispatching squads
python cli.py --target example.com --dry-run
```

## Output

- Console: SALUTE report (Subject / Activity / Location / Unit / Time / Exposure)
- `reports/SALUTE_{target}_{timestamp}.md` — full report
- `logs/mission_{id}.jsonl` — structured mission log with token usage

## Squads

| Squad   | Mission                            | Model           | Tools                   |
|---------|------------------------------------|-----------------|-------------------------|
| Alpha   | Web recon, breach data, paste sites| claude-sonnet-4-6 | web_search            |
| Bravo   | DNS, WHOIS, crt.sh, ASN            | claude-sonnet-4-6 | web_search + dnspython |
| Charlie | Social footprint, username enum    | claude-sonnet-4-6 | web_search            |
| Weapons | PDF/DOCX metadata extraction       | claude-sonnet-4-6 | web_search + httpx     |

## SPOT / SALUTE Schema

Each squad returns a **SPOT report** (Size, Activity, Location, Unit, Time, Equipment mapped to OSINT fields). The Orchestrator synthesizes all SPOT reports into a **SALUTE report** — the final intelligence product.

## Rules of Engagement

- Passive collection only — no logins, no form submissions, no active scanning
- Public data only — web search, DNS queries, CT logs, public APIs
- Documents fetched only if publicly indexed (appear in search results)
