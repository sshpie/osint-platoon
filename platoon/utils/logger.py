from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_instance: MissionLogger | None = None


class MissionLogger:
    def __init__(self, mission_id: str = ""):
        self.mission_id = mission_id or datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        self.log_path = Path(f"logs/mission_{self.mission_id}.jsonl")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self._token_total = 0

    def log(self, event: str, **kwargs) -> None:
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "mission": self.mission_id,
            "event": event,
            **{k: v for k, v in kwargs.items()},
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

        # Console: compact scalar-only preview
        preview = {k: v for k, v in kwargs.items() if isinstance(v, (str, int, float, bool))}
        print(f"  [{event}] {preview}", file=sys.stderr)

    def log_tokens(self, squad: str, input_tokens: int, output_tokens: int) -> None:
        cost = input_tokens * 0.000003 + output_tokens * 0.000015  # sonnet-4-6 pricing
        self._token_total += cost
        self.log("tokens", squad=squad, input=input_tokens, output=output_tokens,
                 cost_usd=round(cost, 4), cumulative_usd=round(self._token_total, 4))


def init_logger(mission_id: str = "") -> MissionLogger:
    global _instance
    _instance = MissionLogger(mission_id)
    return _instance


def get_logger() -> MissionLogger:
    global _instance
    if _instance is None:
        _instance = MissionLogger()
    return _instance
