"""Platoon Orchestrator — implements ATP 3-21.8 8-step TLP."""
from __future__ import annotations
import asyncio
import json
import re
from datetime import datetime, timezone
from pathlib import Path
import anthropic
from platoon.models.salute_report import SALUTEReport, TimelineEntry
from platoon.models.spot_report import SPOTReport
from platoon.models.tasking import MissionTasking, SquadTasking
from platoon.platoon_sergeant import PlatoonSergeant
from platoon.squads.alpha import SquadAlpha
from platoon.squads.bravo import SquadBravo
from platoon.squads.charlie import SquadCharlie
from platoon.squads.weapons import WeaponsSquad
from platoon.utils.logger import get_logger
from platoon.utils.mett_tc import run_mett_tc_analysis

_REPLAN_SYSTEM = """\
You are the Platoon Leader — OSINT research orchestrator (ATP 3-21.8).

Review the current intelligence picture and decide:
1. Should the mission continue another iteration?
2. If so, what refined tasks should each squad pursue?
3. Which high-value pivots warrant deeper investigation?

Output JSON:
```json
{
  "should_continue": true,
  "rationale": "why continue or stop",
  "refined_tasks": [
    {
      "squad": "alpha|bravo|charlie|weapons",
      "objective": "specific refined objective",
      "targets": ["pivot1", "pivot2"],
      "priority": 1,
      "mode": "recon"
    }
  ]
}
```
"""

_SALUTE_SYSTEM = """\
You are the Platoon Leader producing the final SALUTE intelligence report (ATP 3-21.8).

SALUTE format:
- Subject: Who/what is the target
- Activity: What they are doing (digital operations, infrastructure, presence)
- Location: Where they operate (domains, IPs, social platforms)
- Unit/Organization: Corporate structure, aliases, related entities
- Time: Key timestamps — registration dates, last activity, document creation dates
- Exposure: Publicly accessible systems, data leaks, vulnerabilities

You have received all squad SPOT reports. Synthesize them into a coherent SALUTE report.

Output JSON:
```json
{
  "subject": "...",
  "activity": "...",
  "location": "...",
  "unit_org": "...",
  "timeline": [
    {"date": "2025-01-01", "event": "..."}
  ],
  "exposure": "...",
  "executive_summary": "...",
  "key_findings": ["finding1", "finding2"],
  "confidence": 0.8
}
```
"""


class Orchestrator:
    def __init__(self, client: anthropic.AsyncAnthropic, max_iterations: int = 3):
        self.client = client
        self.max_iterations = max_iterations
        self._squad_alpha = SquadAlpha(client)
        self._squad_bravo = SquadBravo(client)
        self._squad_charlie = SquadCharlie(client)
        self._weapons = WeaponsSquad(client)

    # ── TLP Step 1: Receive the mission ──────────────────────────────────────

    async def run_mission(
        self,
        target: str,
        target_type: str = "domain",
        depth: str = "deliberate",
    ) -> SALUTEReport:
        log = get_logger()
        mission_id = log.mission_id
        log.log("mission_start", target=target, type=target_type, depth=depth)

        ps = PlatoonSergeant(mission_id, max_iterations=self.max_iterations)

        # TLP Step 2: Issue warning order (WARNO) — logged
        log.log("warno_issued", target=target, depth=depth)

        # TLP Step 3: Make a tentative plan — METT-TC analysis
        log.log("tlp_step3_mett_tc_start")
        mett_tc_text, squad_tasks = await run_mett_tc_analysis(
            self.client, target, target_type, depth
        )
        log.log("mett_tc_complete", tasks_planned=len(squad_tasks))

        initial_tasking = MissionTasking(
            target=target,
            target_type=target_type,
            depth=depth,
            squad_tasks=squad_tasks,
        )
        ps.set_tasking(initial_tasking)

        # TLP Steps 4–6: Initiate movement, conduct recon, complete the plan
        while ps.should_continue():
            ps.increment_iteration()
            log.log("iteration_start", iteration=ps.iteration)

            tasking = ps.get_current_tasking()
            if not tasking:
                break

            spot_reports = await self._execute_squads(target, tasking, ps)

            for squad, report in spot_reports.items():
                ps.register_spot_report(squad, report)
                log.log("spot_registered", squad=squad,
                        finds=len(report.finds), pivots=len(report.pivots))

            if ps.should_continue():
                replan = await self._replan(target, ps)
                ps.update_tasking(replan)
                log.log("replan_complete", continuing=replan.get("should_continue"))

        # TLP Step 7: Issue OPORD — produce final SALUTE
        log.log("tlp_step7_salute_start")
        salute = await self._produce_salute(target, ps)
        log.log("salute_complete", key_findings=len(salute.key_findings),
                confidence=salute.confidence)

        # TLP Step 8: Supervise & refine — save report
        report_path = self.save_report(salute, target)
        log.log("mission_complete", report=str(report_path),
                total_findings=ps.export_intelligence_picture()["total_findings"])

        return salute

    # ── Base-of-fire + bounding movement ─────────────────────────────────────

    async def _execute_squads(
        self,
        target: str,
        tasking: MissionTasking,
        ps: PlatoonSergeant,
    ) -> dict[str, SPOTReport]:
        log = get_logger()
        task_map = {t.squad: t for t in tasking.squad_tasks}

        # Base of fire: Alpha + Charlie in parallel (web recon + social)
        alpha_tasking = task_map.get("alpha") or SquadTasking(
            squad="alpha", objective=f"Web recon on {target}",
            targets=[target], priority=1, mode="recon",
        )
        charlie_tasking = task_map.get("charlie") or SquadTasking(
            squad="charlie", objective=f"Social footprint of {target}",
            targets=[target], priority=2, mode="recon",
        )

        log.log("base_of_fire", squads=["alpha", "charlie"])
        alpha_task = asyncio.create_task(
            self._squad_alpha.run(target, alpha_tasking)
        )
        charlie_task = asyncio.create_task(
            self._squad_charlie.run(target, charlie_tasking)
        )

        # Wait for Alpha — Bravo bounds off Alpha's pivots (domain signals)
        alpha_report = await alpha_task
        log.log("alpha_complete", finds=len(alpha_report.finds))

        domain_pivots = [
            p for p in alpha_report.pivots
            if "." in p and not p.startswith("@")
        ]
        bravo_targets = list({target, *domain_pivots[:3]})
        bravo_tasking = task_map.get("bravo") or SquadTasking(
            squad="bravo", objective=f"Infrastructure recon for {target}",
            targets=bravo_targets, priority=1, mode="recon",
        )
        bravo_tasking.targets = bravo_targets  # enrich with Alpha's pivots

        log.log("bravo_bounds", targets=bravo_targets[:3])
        bravo_task = asyncio.create_task(
            self._squad_bravo.run(target, bravo_tasking)
        )

        charlie_report = await charlie_task
        bravo_report = await bravo_task
        log.log("recon_complete",
                charlie_finds=len(charlie_report.finds),
                bravo_finds=len(bravo_report.finds))

        # Weapons synthesizes from all collected intel
        weapons_tasking = task_map.get("weapons") or SquadTasking(
            squad="weapons", objective=f"Document intel for {target}",
            targets=[target], priority=3, mode="recon",
        )
        all_pivots = list({
            *alpha_report.pivots,
            *bravo_report.pivots,
            *charlie_report.pivots,
        })
        weapons_tasking.targets = [target, *all_pivots[:5]]

        weapons_report = await self._weapons.run(target, weapons_tasking)
        log.log("weapons_complete", finds=len(weapons_report.finds))

        return {
            "alpha": alpha_report,
            "bravo": bravo_report,
            "charlie": charlie_report,
            "weapons": weapons_report,
        }

    # ── TLP Step 6: Complete the plan — replan ────────────────────────────────

    async def _replan(self, target: str, ps: PlatoonSergeant) -> dict:
        intel = ps.export_intelligence_picture()
        intel_summary = json.dumps(intel, default=str, indent=2)[:4000]

        pivot_list = "\n".join(f"- {p}" for p in ps.pending_pivots[:10])

        prompt = (
            f"Target: {target}\n"
            f"Iterations completed: {ps.iteration}\n"
            f"Max iterations: {ps.max_iterations}\n\n"
            f"HIGH-VALUE PIVOTS DISCOVERED:\n{pivot_list or 'none'}\n\n"
            f"INTELLIGENCE PICTURE:\n{intel_summary}\n\n"
            f"Should the mission continue? If yes, specify refined tasks for each squad."
        )

        try:
            resp = await self.client.messages.create(
                model="claude-opus-4-7",
                max_tokens=2048,
                thinking={"type": "adaptive"},
                system=_REPLAN_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            text = " ".join(b.text for b in resp.content if hasattr(b, "text"))
            m = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
            if m:
                return json.loads(m.group(1))
        except Exception:
            pass

        return {"should_continue": False, "rationale": "replan parse failed"}

    # ── TLP Step 7: Produce SALUTE ────────────────────────────────────────────

    async def _produce_salute(self, target: str, ps: PlatoonSergeant) -> SALUTEReport:
        intel = ps.export_intelligence_picture()
        all_finds = ps.get_all_findings()

        # Summarize top findings by type
        by_type: dict[str, list[str]] = {}
        for f in all_finds:
            ftype = f.get("type", "unknown")
            by_type.setdefault(ftype, []).append(str(f.get("value", ""))[:100])

        finds_summary = json.dumps(
            {k: v[:5] for k, v in by_type.items()},
            indent=2
        )[:3000]

        prompt = (
            f"Target: {target}\n"
            f"Total findings: {len(all_finds)}\n"
            f"Iterations: {ps.iteration}\n\n"
            f"FINDINGS BY TYPE:\n{finds_summary}\n\n"
            f"INTELLIGENCE PICTURE:\n"
            f"{json.dumps(intel, default=str, indent=2)[:3000]}\n\n"
            f"Produce the SALUTE intelligence report."
        )

        try:
            resp = await self.client.messages.create(
                model="claude-opus-4-7",
                max_tokens=4096,
                thinking={"type": "adaptive"},
                system=_SALUTE_SYSTEM,
                messages=[{"role": "user", "content": prompt}],
            )
            text = " ".join(b.text for b in resp.content if hasattr(b, "text"))

            if resp.usage:
                get_logger().log_tokens("salute", resp.usage.input_tokens, resp.usage.output_tokens)

            m = re.search(r"```json\s*(\{[\s\S]*?\})\s*```", text)
            if m:
                data = json.loads(m.group(1))
                timeline = [
                    TimelineEntry(date=e.get("date", ""), event=e.get("event", ""))
                    for e in data.get("timeline", [])
                ]
                return SALUTEReport(
                    subject=data.get("subject", target),
                    activity=data.get("activity", ""),
                    location=data.get("location", ""),
                    unit_org=data.get("unit_org", ""),
                    timeline=timeline,
                    exposure=data.get("exposure", ""),
                    executive_summary=data.get("executive_summary", ""),
                    key_findings=[str(f)[:300] for f in data.get("key_findings", [])[:20]],
                    confidence=float(data.get("confidence", 0.5)),
                    raw={"intel_picture": intel, "total_finds": len(all_finds)},
                )
        except Exception:
            pass

        # Fallback minimal report
        return SALUTEReport(
            subject=target,
            activity="OSINT reconnaissance conducted",
            location=target,
            unit_org="",
            timeline=[],
            exposure=f"{len(all_finds)} findings collected",
            executive_summary=f"OSINT mission against {target} completed {ps.iteration} iterations.",
            key_findings=[str(f.get("value", ""))[:200] for f in all_finds[:10]],
            confidence=0.3,
            raw={"intel_picture": intel},
        )

    # ── Dry run ───────────────────────────────────────────────────────────────

    async def dry_run(
        self,
        target: str,
        target_type: str = "domain",
        depth: str = "deliberate",
    ) -> str:
        log = get_logger()
        log.log("dry_run_start", target=target)

        mett_tc_text, squad_tasks = await run_mett_tc_analysis(
            self.client, target, target_type, depth
        )

        lines = [
            f"METT-TC PLAN — DRY RUN — {target}",
            "=" * 60,
            "",
            mett_tc_text,
            "",
            "PLANNED SQUAD TASKINGS:",
            "-" * 40,
        ]
        for t in squad_tasks:
            lines.append(
                f"  [{t.squad.upper()}] {t.objective}"
                f" | priority={t.priority} | mode={t.mode}"
            )
            if t.targets:
                lines.append(f"    targets: {', '.join(t.targets[:3])}")

        lines += [
            "",
            f"Max iterations: {self.max_iterations}",
            "No squads dispatched — dry run complete.",
        ]
        return "\n".join(lines)

    # ── Persistence ───────────────────────────────────────────────────────────

    @staticmethod
    def save_report(report: SALUTEReport, target: str) -> Path:
        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        safe_target = re.sub(r"[^\w\-.]", "_", target)[:40]
        path = reports_dir / f"SALUTE_{safe_target}_{ts}.md"

        lines = [
            f"# SALUTE REPORT — {report.subject}",
            f"Generated: {ts}",
            "",
            f"## Executive Summary",
            report.executive_summary,
            "",
            f"## SALUTE",
            f"**Subject:** {report.subject}",
            f"**Activity:** {report.activity}",
            f"**Location:** {report.location}",
            f"**Unit/Org:** {report.unit_org}",
            f"**Exposure:** {report.exposure}",
            "",
            f"## Timeline",
        ]
        for entry in report.timeline:
            lines.append(f"- {entry.date}: {entry.event}")

        lines += [
            "",
            f"## Key Findings",
        ]
        for i, finding in enumerate(report.key_findings, 1):
            lines.append(f"{i}. {finding}")

        lines.append(f"\n**Confidence:** {report.confidence:.0%}")

        path.write_text("\n".join(lines))
        return path
