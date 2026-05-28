"""ORP — Objective Rally Point leader's reconnaissance (ATP 3-21.8 para 7-15/7-111).

Passive pre-check only. Confirms target identity, ethics flags, and contact action
before any squad is dispatched. Does not actively probe the target.

Five contact option branches (para 4-68): attack, defend, bypass, delay, withdraw.
- attack: proceed as planned
- defend: proceed with reduced scope / passive-only
- bypass: skip this target entirely (ethics flag, honeypot, out-of-scope)
- delay: proceed but note constraints
- withdraw: abort (target not found, fatal ethics flag)
"""
from __future__ import annotations
import json
import re
from platoon.models.tasking import MissionTasking
from platoon.utils.claude_runner import run_claude

_ORP_SYSTEM = """\
You are the Platoon Leader conducting a leader's reconnaissance at the Objective Rally Point
(ATP 3-21.8 para 7-15). This is a passive pre-check only — no active probing.

Assess the target using only open-source passive signals (domain age, known reputation,
public records, org type) to determine the contact action and any ethics flags.

Output JSON:
```json
{
  "contact_action": "attack|defend|bypass|delay|withdraw",
  "reason": "one-sentence rationale",
  "ethics_flags": [],
  "target_class": "commercial|government|personal|infrastructure|unknown",
  "confidence": 0.8,
  "modified_scope": null
}
```

Contact actions:
- attack: proceed as planned — target appears in scope, no ethics concerns
- defend: proceed passive-only — target has some sensitivity, reduce active probing
- bypass: skip — target is a honeypot, known decoy, or clearly out of scope
- delay: proceed with noted constraint — target requires additional authorization check
- withdraw: abort mission — fatal ethics flag (healthcare, critical infra without auth, etc.)
"""


async def run_leaders_recon(
    target: str,
    target_type: str,
    tasking: MissionTasking,
) -> dict:
    """Passive pre-check at the ORP. Returns contact action and ethics assessment."""
    prompt = (
        f"Target: {target}\n"
        f"Type: {target_type}\n"
        f"CCIR: {tasking.ccir or 'not specified'}\n"
        f"Depth: {tasking.depth}\n\n"
        f"Conduct passive leader's recon. Assess target class, ethics flags, "
        f"and recommend a contact action."
    )

    try:
        text = await run_claude(
            prompt,
            system=_ORP_SYSTEM,
            model="claude-sonnet-4-6",
        )
        m = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
        if m:
            return json.loads(m.group(1))
    except Exception:
        pass

    # Default: proceed (attack) if ORP check fails — don't halt on parse error
    return {
        "contact_action": "attack",
        "reason": "ORP check inconclusive — proceeding",
        "ethics_flags": [],
        "target_class": "unknown",
        "confidence": 0.5,
        "modified_scope": None,
    }
