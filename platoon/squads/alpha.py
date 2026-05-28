"""Squad Alpha — Web Recon. News, mentions, public records, breach data, paste sites."""
from __future__ import annotations
import json
import re
from datetime import datetime, timezone
from platoon.models.spot_report import SPOTReport, Finding, LACEReport
from platoon.models.tasking import SquadTasking
from platoon.utils.claude_runner import run_claude
from platoon.utils.logger import get_logger

_SYSTEM = """\
You are Squad Alpha — Web Recon — of an OSINT research platoon (ATP 3-21.8).

Mission: Surface-level web reconnaissance. Search for news, public mentions, business records,
data breach appearances, paste sites, forums, and any publicly indexed references.

Rules of Engagement:
- PASSIVE mode. Read-only. No logins, no account creation, no form submissions.
- Weapons Control: TIGHT — report only positively confirmed findings.
- Use web_search to gather intelligence on the target.
- Cite every finding with its source URL.

Disengagement criteria: stop collecting on a source if it returns rate-limit signals,
requires authentication, or shows signs of being a canary/honeypot.

Output: After completing reconnaissance, end your response with a SPOT report as a JSON block:

```json
{
  "squad": "alpha",
  "finds": [
    {
      "type": "web_mention|news_article|public_record|data_breach|paste_site|email|address|person|org|phone",
      "value": "the finding",
      "source_url": "https://...",
      "timestamp": "2026-01-01T00:00:00Z",
      "confidence": 0.8,
      "metadata": {}
    }
  ],
  "pivots": ["domain to investigate", "username found", "email address"],
  "confidence": 0.7,
  "lace": {
    "liquid": "ok|rate_limited|blocked",
    "ammo": -1,
    "casualties": 0,
    "equipment": "ok|degraded"
  },
  "dead_space": ["surfaces seen but not accessible", "auth-gated endpoint found"]
}
```
"""


class SquadAlpha:
    async def run(self, target: str, tasking: SquadTasking) -> SPOTReport:
        log = get_logger()
        log.log("squad_dispatched", squad="alpha", objective=tasking.objective[:80],
                wcs=tasking.weapons_control)

        brief = (
            f"MISSION — SQUAD ALPHA — WEB RECON\n\n"
            f"Primary target: {target}\n"
            f"Objective: {tasking.objective}\n"
            f"Additional targets: {', '.join(tasking.targets) if tasking.targets else 'none'}\n"
            f"Priority: {tasking.priority} | Mode: {tasking.mode.upper()}"
            f" | WCS: {tasking.weapons_control.upper()}\n"
        )
        if tasking.disengagement_criteria:
            brief += f"Disengage if: {', '.join(tasking.disengagement_criteria)}\n"
        brief += (
            f"\nExecute web reconnaissance. Search for:\n"
            f"1. News and media mentions\n"
            f"2. Business filings / public records\n"
            f"3. Data breach appearances (HaveIBeenPwned, breach databases)\n"
            f"4. Paste site / code repository leaks\n"
            f"5. Social media cross-references\n"
            f"6. Any emails, phone numbers, addresses associated with the target\n\n"
            f"Note any surfaces that were visible but inaccessible (auth-gated, rate-limited) "
            f"in the dead_space field.\n\n"
            f"Conclude with the SPOT JSON block."
        )

        text = await run_claude(
            brief,
            system=_SYSTEM,
            model="claude-sonnet-4-6",
            allow_web_search=True,
        )
        report = _parse_spot(text, "alpha")
        log.log("spot_report", squad="alpha", findings=len(report.finds), pivots=len(report.pivots),
                confidence=report.confidence, casualties=report.lace.casualties)
        return report


def _parse_spot(text: str, squad: str) -> SPOTReport:
    # Try ```json block
    m = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
    json_str = m.group(1) if m else None

    # Fallback: raw JSON object with "squad" key
    if not json_str:
        m2 = re.search(r'\{\s*"squad"\s*:\s*"' + squad + r'"[\s\S]*?\}(?=\s*(?:$|\n```|\Z))', text)
        json_str = m2.group(0) if m2 else None

    if json_str:
        try:
            data = json.loads(json_str)
            finds = []
            for f in data.get("finds", []):
                try:
                    ts_raw = f.get("timestamp", "")
                    ts = (datetime.fromisoformat(ts_raw.replace("Z", "+00:00"))
                          if ts_raw else datetime.now(timezone.utc))
                    finds.append(Finding(
                        type=f.get("type", "web_mention"),
                        value=str(f.get("value", ""))[:500],
                        source_url=str(f.get("source_url", ""))[:500],
                        timestamp=ts,
                        confidence=float(f.get("confidence", 0.5)),
                        metadata=f.get("metadata", {}),
                    ))
                except Exception:
                    continue

            # Parse LACE report
            lace_raw = data.get("lace", {})
            lace = LACEReport(
                liquid=lace_raw.get("liquid", "ok"),
                ammo=int(lace_raw.get("ammo", -1)),
                casualties=int(lace_raw.get("casualties", 0)),
                equipment=lace_raw.get("equipment", "ok"),
            )

            return SPOTReport(
                squad=squad,  # type: ignore[arg-type]
                finds=finds,
                pivots=[str(p)[:200] for p in data.get("pivots", [])[:10]],
                confidence=float(data.get("confidence", 0.5)),
                lace=lace,
                dead_space=[str(s)[:200] for s in data.get("dead_space", [])[:10]],
                raw={"response_preview": text[:1000]},
            )
        except (json.JSONDecodeError, Exception):
            pass

    return SPOTReport(
        squad=squad,  # type: ignore[arg-type]
        finds=[],
        pivots=[],
        confidence=0.2,
        raw={"response_preview": text[:1000], "parse_error": "no_spot_json"},
    )
