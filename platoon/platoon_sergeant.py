from __future__ import annotations
from platoon.models.spot_report import SPOTReport
from platoon.models.tasking import MissionTasking, SquadTasking


class PlatoonSergeant:
    """Tracks the running intelligence picture. Issues stop conditions. Files sector sketches.

    Doctrinal basis: ATP 3-21.8 para 5-155 (Platoon Sergeant role) — consolidates squad
    reports, tracks LACE (para 7-116), maintains sector sketch / coverage map (para A-93),
    and manages PIR collection status.
    """

    def __init__(self, mission_id: str, max_iterations: int = 3):
        self.mission_id = mission_id
        self.max_iterations = max_iterations
        self.iteration = 0
        self._stop_requested = False

        # Intelligence picture: squad -> list of serialized reports
        self.intelligence_picture: dict[str, list[dict]] = {}

        # Unique pivots discovered across all squads
        self.pending_pivots: list[str] = []
        self._seen_pivots: set[str] = set()

        # Dedup tracker: (squad, value) pairs already found
        self.completed_tasks: set[tuple[str, str]] = set()

        self.squad_status: dict[str, str] = {}
        self._current_tasking: MissionTasking | None = None

        # LACE tracking — aggregate health across all squads (para 7-116)
        self.lace_aggregate: dict[str, dict] = {}

        # Sector sketch — dead space coverage gaps across all squads (para A-93)
        self.dead_space: list[str] = []

        # PIR completion tracking
        self.pir_status: dict[str, bool] = {}

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def should_continue(self) -> bool:
        if self._stop_requested or self.iteration >= self.max_iterations:
            return False
        # Auto-stop if all PIRs answered (para 7-196 — collection stops when PIRs satisfied)
        if self.pir_status and all(self.pir_status.values()):
            return False
        return True

    def increment_iteration(self) -> None:
        self.iteration += 1

    def stop(self) -> None:
        self._stop_requested = True

    # ── Tasking ──────────────────────────────────────────────────────────────

    def set_tasking(self, tasking: MissionTasking) -> None:
        self._current_tasking = tasking
        # Initialize PIR tracking from CCIR/PIR hierarchy (glossary: PIR under CCIR)
        for pir in tasking.pirs:
            if pir not in self.pir_status:
                self.pir_status[pir] = False

    def get_current_tasking(self) -> MissionTasking | None:
        return self._current_tasking

    def update_tasking(self, replan: dict) -> None:
        if not replan.get("should_continue", False):
            self.stop()
            return

        refined = replan.get("refined_tasks", [])
        if refined and self._current_tasking:
            try:
                self._current_tasking.squad_tasks = [SquadTasking(**t) for t in refined]
            except Exception:
                pass  # malformed replan — keep existing tasking

    # ── Intelligence ─────────────────────────────────────────────────────────

    def register_spot_report(self, squad: str, report: SPOTReport) -> None:
        self.squad_status[squad] = "reported"

        if squad not in self.intelligence_picture:
            self.intelligence_picture[squad] = []
        self.intelligence_picture[squad].append(report.model_dump(mode="json"))

        for pivot in report.pivots:
            if pivot and pivot not in self._seen_pivots:
                self._seen_pivots.add(pivot)
                self.pending_pivots.append(pivot)

        # File LACE report (para 7-116)
        self.lace_aggregate[squad] = {
            "liquid": report.lace.liquid,
            "ammo": report.lace.ammo,
            "casualties": report.lace.casualties,
            "equipment": report.lace.equipment,
            "iteration": self.iteration,
        }

        # Consolidate dead space into sector sketch (para A-93)
        for gap in report.dead_space:
            if gap not in self.dead_space:
                self.dead_space.append(gap)

        # Update PIR status from squad answers (para 7-195)
        for pir, answered in report.pirs_answered.items():
            if pir in self.pir_status and answered:
                self.pir_status[pir] = True

    def get_all_findings(self) -> list[dict]:
        findings = []
        for reports in self.intelligence_picture.values():
            for r in reports:
                findings.extend(r.get("finds", []))
        return findings

    def get_lace_summary(self) -> dict:
        """Aggregate LACE picture across all squads."""
        total_casualties = sum(v["casualties"] for v in self.lace_aggregate.values())
        degraded = [sq for sq, v in self.lace_aggregate.items() if v["equipment"] != "ok"]
        rate_limited = [sq for sq, v in self.lace_aggregate.items() if v["liquid"] != "ok"]
        return {
            "total_failed_probes": total_casualties,
            "degraded_squads": degraded,
            "rate_limited": rate_limited,
            "squad_detail": self.lace_aggregate,
        }

    def export_intelligence_picture(self) -> dict:
        return {
            "target": self._current_tasking.target if self._current_tasking else "",
            "ccir": self._current_tasking.ccir if self._current_tasking else "",
            "iterations_completed": self.iteration,
            "total_findings": len(self.get_all_findings()),
            "pending_pivots": self.pending_pivots[:10],
            "pir_status": self.pir_status,
            "lace": self.get_lace_summary(),
            "dead_space": self.dead_space[:10],
            "squad_reports": self.intelligence_picture,
        }
