from __future__ import annotations
import json
import re
import anthropic
from platoon.models.tasking import MissionTasking, SquadTasking

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
2. Prioritized squad tasking as valid JSON block:

```json
{
  "squad_tasks": [
    {"squad": "alpha", "objective": "...", "targets": ["target1", "target2"], "priority": 1},
    {"squad": "bravo", "objective": "...", "targets": ["target1"], "priority": 1},
    {"squad": "charlie", "objective": "...", "targets": ["target1"], "priority": 2},
    {"squad": "weapons", "objective": "...", "targets": ["target1"], "priority": 3}
  ]
}
```

Priority: 1=immediate, 2=follow-on, 3=if time permits
All squads operate in RECON mode (passive, read-only) unless explicitly authorized otherwise.
"""


async def run_mett_tc_analysis(
    client: anthropic.AsyncAnthropic,
    target: str,
    target_type: str,
    depth: str,
) -> tuple[str, list[SquadTasking]]:
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

Issue prioritized squad tasking."""

    response = await client.messages.create(
        model="claude-opus-4-7",
        max_tokens=4096,
        thinking={"type": "adaptive"},
        system=METT_TC_PROMPT,
        messages=[{"role": "user", "content": mission_input}],
    )

    analysis_text = ""
    for block in response.content:
        if block.type == "text":
            analysis_text += block.text

    tasks = _extract_tasks(analysis_text)
    return analysis_text, tasks


def _extract_tasks(text: str) -> list[SquadTasking]:
    # Try ```json ... ``` block first
    code_block = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
    json_str = code_block.group(1) if code_block else None

    # Fallback: raw JSON with squad_tasks key
    if not json_str:
        raw_match = re.search(r'\{[^{}]*"squad_tasks"[\s\S]*?\}(?=\s*(?:$|[^,\s{]))', text)
        json_str = raw_match.group(0) if raw_match else None

    if json_str:
        try:
            data = json.loads(json_str)
            tasks = []
            for t in data.get("squad_tasks", []):
                tasks.append(SquadTasking(
                    squad=t["squad"],
                    objective=t.get("objective", ""),
                    targets=t.get("targets", []),
                    priority=t.get("priority", 2),
                ))
            if tasks:
                return tasks
        except (json.JSONDecodeError, KeyError, ValueError):
            pass

    # Default fallback — all four squads
    return [
        SquadTasking(squad="alpha", objective="Web recon", targets=[], priority=1),
        SquadTasking(squad="bravo", objective="Infrastructure recon", targets=[], priority=1),
        SquadTasking(squad="charlie", objective="Social footprint", targets=[], priority=2),
        SquadTasking(squad="weapons", objective="Document intel", targets=[], priority=3),
    ]
