from __future__ import annotations
from platoon.models.spot_report import SPOTReport
from platoon.models.tasking import MissionTasking, SquadTasking


class PlatoonSergeant:
    """Tracks the running intelligence picture. Prevents duplicate work. Issues stop conditions."""

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

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def should_continue(self) -> bool:
        return not self._stop_requested and self.iteration < self.max_iterations

    def increment_iteration(self) -> None:
        self.iteration += 1

    def stop(self) -> None:
        self._stop_requested = True

    # ── Tasking ──────────────────────────────────────────────────────────────

    def set_tasking(self, tasking: MissionTasking) -> None:
        self._current_tasking = tasking

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

    def get_all_findings(self) -> list[dict]:
        findings = []
        for reports in self.intelligence_picture.values():
            for r in reports:
                findings.extend(r.get("finds", []))
        return findings

    def export_intelligence_picture(self) -> dict:
        return {
            "target": self._current_tasking.target if self._current_tasking else "",
            "iterations_completed": self.iteration,
            "total_findings": len(self.get_all_findings()),
            "pending_pivots": self.pending_pivots[:10],
            "squad_reports": self.intelligence_picture,
        }
