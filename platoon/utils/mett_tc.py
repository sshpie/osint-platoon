from __future__ import annotations
import json
import re
from platoon.models.tasking import MissionTasking, SquadTasking
from platoon.utils.claude_runner import run_claude

METT_TC_PROMPT = """\
You are the Platoon Leader of an OSINT research unit operating under ATP 3-21.8 doctrine.

Conduct a METT-TC(I) analysis for the assigned mission, then issue prioritized squad tasking.

Available squads:
- Alpha: Web recon — news, mentions, public records, breach data, paste sites
- Bravo: Domain/IP/Infra — DNS, WHOIS, cert transparency, ASN attribution
- Charlie: Social footprint — username enumeration, public profiles, linked accounts
- Weapons: Document intel — public PDFs/docs, metadata extraction

Output structure:
1. Full METT-TC(I) analysis (prose)
2. Intelligence requirements — CCIR and PIRs
3. Prioritized squad tasking as valid JSON block:

```json
{
  "ccir": "one-sentence research thesis — what this mission must answer",
  "pirs": ["specific verifiable question 1", "specific verifiable question 2"],
  "squad_tasks": [
    {
      "squad": "alpha",
      "objective": "...",
      "targets": ["target1", "target2"],
      "priority": 1,
      "weapons_control": "tight",
      "disengagement_criteria": ["target returns 429", "suspected honeypot signal"],
      "bypass_criteria": ["already enumerated this session"],
      "actions_on_contact": "report and hold"
    },
    {"squad": "bravo", "objective": "...", "targets": ["target1"], "priority": 1},
    {"squad": "charlie", "objective": "...", "targets": ["target1"], "priority": 2},
    {"squad": "weapons", "objective": "...", "targets": ["target1"], "priority": 3}
  ]
}
```

Priority: 1=immediate, 2=follow-on, 3=if time permits
Weapons control: hold=only if ordered, tight=confirmed targets only, free=any non-friendly
All squads operate in RECON mode (passive, read-only) unless explicitly authorized otherwise.
Disengagement criteria: pre-defined conditions that halt a squad without orchestrator consultation.
"""


async def run_mett_tc_analysis(
    target: str,
    target_type: str,
    depth: str,
) -> tuple[str, MissionTasking]:
    mission_input = f"""\
MISSION ORDER

Target: {target}
Target Type: {target_type}
Assessment Depth: {depth.upper()}

Conduct METT-TC(I) analysis:
- Mission: What intelligence are we collecting and why?
- Enemy (Target): What do we already know about {target}?
- Terrain: What attack surfaces are in scope? (web presence, DNS/infra, social, documents)
- Troops: Which squads are most valuable given target type?
- Time: {depth} depth — calibrate thoroughness accordingly.
- Civil/Info: Any ethical/legal constraints on this target type?

State the CCIR (one-sentence research thesis) and 3-5 specific PIRs.
Issue prioritized squad tasking with disengagement criteria."""

    analysis_text = await run_claude(
        mission_input,
        system=METT_TC_PROMPT,
        model="claude-opus-4-7",
        effort="high",
    )

    tasking = _extract_tasking(analysis_text, target, target_type, depth)
    tasking.mett_tc_analysis = analysis_text
    return analysis_text, tasking


def _extract_tasking(
    text: str,
    target: str,
    target_type: str,
    depth: str,
) -> MissionTasking:
    code_block = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
    json_str = code_block.group(1) if code_block else None

    if not json_str:
        raw_match = re.search(r'\{[^{}]*"squad_tasks"[\s\S]*?\}(?=\s*(?:$|[^,\s{]))', text)
        json_str = raw_match.group(0) if raw_match else None

    squad_tasks: list[SquadTasking] = []
    ccir = ""
    pirs: list[str] = []

    if json_str:
        try:
            data = json.loads(json_str)
            ccir = data.get("ccir", "")
            pirs = data.get("pirs", [])
            for t in data.get("squad_tasks", []):
                squad_tasks.append(SquadTasking(
                    squad=t["squad"],
                    objective=t.get("objective", ""),
                    targets=t.get("targets", []),
                    priority=t.get("priority", 2),
                    mode=t.get("mode", "recon"),
                    weapons_control=t.get("weapons_control", "tight"),
                    disengagement_criteria=t.get("disengagement_criteria", []),
                    bypass_criteria=t.get("bypass_criteria", []),
                    actions_on_contact=t.get("actions_on_contact", "report and hold"),
                ))
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    if not squad_tasks:
        squad_tasks = [
            SquadTasking(squad="alpha", objective="Web recon", targets=[], priority=1),
            SquadTasking(squad="bravo", objective="Infrastructure recon", targets=[], priority=1),
            SquadTasking(squad="charlie", objective="Social footprint", targets=[], priority=2),
            SquadTasking(squad="weapons", objective="Document intel", targets=[], priority=3),
        ]

    return MissionTasking(
        target=target,
        target_type=target_type,
        depth=depth,  # type: ignore[arg-type]
        squad_tasks=squad_tasks,
        ccir=ccir,
        pirs=pirs,
    )
