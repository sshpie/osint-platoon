"""Squad Bravo — Domain/IP/Infra. DNS, WHOIS, cert transparency, ASN attribution."""
from __future__ import annotations
import asyncio
import json
import re
from datetime import datetime, timezone
import httpx
from platoon.models.spot_report import SPOTReport, Finding
from platoon.models.tasking import SquadTasking
from platoon.utils.claude_runner import run_claude
from platoon.utils.logger import get_logger

_SYSTEM = """\
You are Squad Bravo — Infrastructure Recon — of an OSINT research platoon (ATP 3-21.8).

Mission: Map technical infrastructure. Analyze DNS records, WHOIS data, SSL certificates,
subdomains, ASN/hosting attribution, and historical DNS records.

You will receive raw DNS/WHOIS/cert data. Analyze it and use web_search to enrich findings.

Rules of Engagement:
- PASSIVE. No active port scanning. DNS and CT log queries only.
- Cite every finding with its source.

Output: Conclude with a SPOT JSON block:

```json
{
  "squad": "bravo",
  "finds": [
    {
      "type": "ip|domain|subdomain|asn|registrar|nameserver|mx_record|ssl_cert|whois_email|hosting_provider",
      "value": "the finding",
      "source_url": "dns|whois|crt.sh|shodan",
      "timestamp": "2026-01-01T00:00:00Z",
      "confidence": 0.9,
      "metadata": {"ttl": 300, "record_type": "A"}
    }
  ],
  "pivots": ["related domain", "IP range", "registrant email"],
  "confidence": 0.8,
  "lace": {"liquid": "ok|rate_limited|blocked", "ammo": -1, "casualties": 0, "equipment": "ok"},
  "dead_space": ["auth-gated registrar", "private WHOIS"]
}
```
"""


async def _dns_lookup(domain: str) -> dict[str, list[str]]:
    results: dict[str, list[str]] = {}
    try:
        import dns.resolver
        for rtype in ("A", "AAAA", "MX", "NS", "TXT", "CNAME"):
            try:
                answers = dns.resolver.resolve(domain, rtype, lifetime=5)
                results[rtype] = [str(r) for r in answers]
            except Exception:
                pass
    except ImportError:
        pass
    return results


async def _whois_lookup(domain: str) -> dict:
    try:
        import whois
        w = whois.whois(domain)
        if hasattr(w, "__dict__"):
            raw = {k: str(v) for k, v in w.__dict__.items() if v and not k.startswith("_")}
            return raw
        return {}
    except Exception:
        return {}


async def _cert_transparency(domain: str) -> list[str]:
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"https://crt.sh/?q=%.{domain}&output=json",
                headers={"User-Agent": "osint-platoon/1.0 (security research)"},
            )
            if resp.status_code == 200:
                entries = resp.json()
                seen: set[str] = set()
                subs: list[str] = []
                for e in entries[:100]:
                    name = e.get("name_value", "")
                    for n in name.split("\n"):
                        n = n.strip().replace("*.", "")
                        if n and n not in seen:
                            seen.add(n)
                            subs.append(n)
                return subs[:30]
    except Exception:
        pass
    return []


class SquadBravo:
    async def run(self, target: str, tasking: SquadTasking) -> SPOTReport:
        log = get_logger()
        log.log("squad_dispatched", squad="bravo", objective=tasking.objective[:80],
                wcs=tasking.weapons_control)

        # Extract domain-like targets for DNS/WHOIS
        domains = [t for t in tasking.targets if "." in t and not t.startswith("@")]
        if not domains:
            domains = [target] if "." in target else []

        # Parallel passive collection
        infra_data: dict[str, dict] = {}
        for domain in domains[:3]:
            dns_res, whois_res, ct_res = await asyncio.gather(
                _dns_lookup(domain),
                _whois_lookup(domain),
                _cert_transparency(domain),
                return_exceptions=True,
            )
            infra_data[domain] = {
                "dns": dns_res if not isinstance(dns_res, Exception) else {},
                "whois": whois_res if not isinstance(whois_res, Exception) else {},
                "cert_transparency": ct_res if not isinstance(ct_res, Exception) else [],
            }

        brief = (
            f"MISSION — SQUAD BRAVO — INFRASTRUCTURE RECON\n\n"
            f"Primary target: {target}\n"
            f"Objective: {tasking.objective}\n"
            f"Mode: {tasking.mode.upper()}\n\n"
            f"RAW PASSIVE COLLECTION:\n"
            f"{json.dumps(infra_data, indent=2, default=str)[:3000]}\n\n"
            f"Analyze this data and use web search to:\n"
            f"1. Identify the hosting provider and ASN\n"
            f"2. Look up significant IPs in threat intel\n"
            f"3. Find historical DNS records (SecurityTrails, viewdns.info)\n"
            f"4. Identify operator/registrant from WHOIS data\n"
            f"5. Surface any cloud infrastructure indicators\n\n"
            f"Conclude with the SPOT JSON block."
        )

        text = await run_claude(
            brief,
            system=_SYSTEM,
            model="claude-sonnet-4-6",
            allow_web_search=True,
        )

        raw_finds = _extract_raw_finds(infra_data, domains)
        report = _parse_spot(text, "bravo", raw_finds)
        log.log("spot_report", squad="bravo", findings=len(report.finds), pivots=len(report.pivots))
        return report


def _extract_raw_finds(infra_data: dict, domains: list[str]) -> list[Finding]:
    finds: list[Finding] = []
    now = datetime.now(timezone.utc)
    for domain, data in infra_data.items():
        for rtype, records in (data.get("dns") or {}).items():
            for rec in records[:5]:
                finds.append(Finding(
                    type="ip" if rtype in ("A", "AAAA") else rtype.lower() + "_record",
                    value=rec,
                    source_url="dns",
                    timestamp=now,
                    confidence=0.95,
                    metadata={"record_type": rtype, "domain": domain},
                ))
        for sub in (data.get("cert_transparency") or [])[:10]:
            finds.append(Finding(
                type="subdomain",
                value=sub,
                source_url="crt.sh",
                timestamp=now,
                confidence=0.9,
                metadata={"parent_domain": domain},
            ))
    return finds


def _parse_spot(text: str, squad: str, raw_finds: list[Finding] | None = None) -> SPOTReport:
    from platoon.squads.alpha import _parse_spot as alpha_parse
    report = alpha_parse(text, squad)
    if raw_finds:
        # Merge raw finds into parsed report
        existing_vals = {f.value for f in report.finds}
        for f in raw_finds:
            if f.value not in existing_vals:
                report.finds.append(f)
                existing_vals.add(f.value)
    return report
