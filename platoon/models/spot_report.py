from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal, Any
from datetime import datetime, timezone


class Finding(BaseModel):
    type: str
    value: str
    source_url: str = ""
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LACEReport(BaseModel):
    """Post-objective status report (para 7-116/7-121).
    Liquid=rate-limit health, Ammo=queries remaining, Casualties=failed probes, Equipment=tool health.
    """
    liquid: str = "ok"       # rate-limit/connectivity status
    ammo: int = -1           # estimated queries/budget remaining (-1 = unknown)
    casualties: int = 0      # count of failed or blocked probe attempts
    equipment: str = "ok"    # tool health note


class SPOTReport(BaseModel):
    squad: Literal["alpha", "bravo", "charlie", "weapons"]
    finds: list[Finding] = Field(default_factory=list)
    pivots: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    raw: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    iteration: int = 0

    # LACE health report — filed at ORP after actions on objective (para 7-116)
    lace: LACEReport = Field(default_factory=LACEReport)

    # Sector sketch: dead space = targets seen but not penetrated (para 6-80 / A-93)
    dead_space: list[str] = Field(default_factory=list)

    # PIR answers — which specific questions were confirmed/denied
    pirs_answered: dict[str, bool] = Field(default_factory=dict)
