from __future__ import annotations
import json
import re
from platoon.models.tasking import MissionTasking, SquadTasking
from platoon.utils.claude_runner import run_claude

METT_TC_PROMPT = """\
You are a research mission planner. Conduct a METT-TC(I) situational analysis for the assigned subject, \
then issue prioritized team tasking.

Available research teams:
- alpha: Web — news coverage, mentions, public records, public data repositories
- bravo: Infrastructure — DNS records, WHOIS, certificate data, network attribution
- charlie: Social — public profiles, linked accounts, organization mapping
- weapons: Documents — published PDFs, technical docs, metadata from public files

Output structure:
1. Full METT-TC(I) analysis (prose)
2. Key research questions — CCIR (thesis) and PIRs (specific questions)
3. Prioritized team tasking as valid JSON block:

```json
{
  "ccir": "one-sentence research thesis",
  "pirs": ["specific verifiable question 1", "specific verifiable question 2"],
  "squad_tasks": [
    {
      "squad": "alpha",
      "objective": "...",
      "targets": ["target1"],
      "priority": 1,
      "weapons_control": "tight",
      "disengagement_criteria": ["source returns 429", "requires login"],
      "bypass_criteria": ["already covered this session"],
      "actions_on_contact": "report and hold"
    },
    {"squad": "bravo", "objective": "...", "targets": ["target1"], "priority": 1},
    {"squad": "charlie", "objective": "...", "targets": ["target1"], "priority": 2},
    {"squad": "weapons", "objective": "...", "targets": ["target1"], "priority": 3}
  ]
}
```

Priority: 1=immediate, 2=follow-on, 3=if time permits.
All teams are read-only and passive — no logins, no form submissions.
"""


async def run_mett_tc_analysis(
    target: str,
    target_type: str,
    depth: str,
) -> tuple[str, MissionTasking]:
    mission_input = f"""\
RESEARCH ORDER

Subject: {target}
Subject Type: {target_type}
Depth: {depth.upper()}

Situational analysis:
- Mission: What are we researching and why?
- Subject: What is known about {target}?
- Terrain: What public-facing surfaces exist? (web, DNS/network, social, documents)
- Troops: Which research teams fit this subject type?
- Time: {depth} depth — calibrate scope.
- Constraints: Any scope limitations for this subject type?

Provide CCIR (research thesis) and 3-5 PIRs. Issue team tasking."""

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
