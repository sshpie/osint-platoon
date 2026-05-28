"""Squad Charlie — Social Footprint. Username enumeration, public profiles, linked accounts."""
from __future__ import annotations
from platoon.models.spot_report import SPOTReport
from platoon.models.tasking import SquadTasking
from platoon.utils.claude_runner import run_claude
from platoon.utils.logger import get_logger
from platoon.squads.alpha import _parse_spot

_SYSTEM = """\
You are Squad Charlie — Social Footprint — of an OSINT research platoon (ATP 3-21.8).

Mission: Map the target's social presence. Find usernames, public profiles, linked accounts,
bios, follower/following patterns, joined dates, and cross-platform identity signals.

Platforms to cover: LinkedIn, GitHub, Twitter/X, Reddit, HackerNews, Instagram, Facebook,
YouTube, TikTok, Discord (public servers), Telegram (public), Stack Overflow, Dev.to,
Medium, Substack, Keybase, Mastodon, and any platform-specific mentions.

Rules of Engagement:
- Public data ONLY. No authenticated scraping, no logins.
- Use web_search to find profiles and mentions.
- Note: username, platform, URL, last-active date (if visible), bio/description.

Output: Conclude with SPOT JSON:

```json
{
  "squad": "charlie",
  "finds": [
    {
      "type": "social_profile|username|email|linked_account|bio_detail|follower_network",
      "value": "username or URL",
      "source_url": "https://platform.com/username",
      "timestamp": "2026-01-01T00:00:00Z",
      "confidence": 0.85,
      "metadata": {"platform": "GitHub", "last_active": "2026-05", "bio": "..."}
    }
  ],
  "pivots": ["alternate username", "linked email", "associated org"],
  "confidence": 0.7
}
```
"""


class SquadCharlie:
    async def run(self, target: str, tasking: SquadTasking) -> SPOTReport:
        log = get_logger()
        log.log("squad_dispatched", squad="charlie", objective=tasking.objective[:80])

        brief = (
            f"MISSION — SQUAD CHARLIE — SOCIAL FOOTPRINT\n\n"
            f"Primary target: {target}\n"
            f"Objective: {tasking.objective}\n"
            f"Additional targets: {', '.join(tasking.targets) if tasking.targets else 'none'}\n"
            f"Priority: {tasking.priority} | Mode: {tasking.mode.upper()}\n\n"
            f"Execute social footprint mapping:\n"
            f"1. Search for the target on major social platforms\n"
            f"2. Find GitHub/GitLab/Bitbucket accounts (check commit history for email leaks)\n"
            f"3. Find professional profiles (LinkedIn, company pages)\n"
            f"4. Identify linked usernames and cross-platform identity\n"
            f"5. Note any public bios, locations, or personal details\n"
            f"6. Look for archived/deleted profiles via web cache/Wayback\n\n"
            f"Conclude with the SPOT JSON block."
        )

        text = await run_claude(
            brief,
            system=_SYSTEM,
            model="claude-sonnet-4-6",
            allow_web_search=True,
        )
        report = _parse_spot(text, "charlie")
        log.log("spot_report", squad="charlie", findings=len(report.finds), pivots=len(report.pivots))
        return report
