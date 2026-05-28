from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal


class SquadTasking(BaseModel):
    squad: Literal["alpha", "bravo", "charlie", "weapons"]
    objective: str
    targets: list[str] = Field(default_factory=list)
    priority: int = Field(ge=1, le=3, default=2)
    mode: Literal["recon", "active"] = "recon"


class MissionTasking(BaseModel):
    mission_id: str
    target: str
    target_type: str
    depth: Literal["hasty", "deliberate"]
    squad_tasks: list[SquadTasking] = Field(default_factory=list)
    mett_tc_analysis: str = ""
