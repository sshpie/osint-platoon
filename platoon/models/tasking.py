from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Literal


class SquadTasking(BaseModel):
    squad: Literal["alpha", "bravo", "charlie", "weapons"]
    objective: str
    targets: list[str] = Field(default_factory=list)
    priority: int = Field(ge=1, le=3, default=2)
    mode: Literal["recon", "active"] = "recon"

    # GOTWA — mandatory per para 7-15 / 3-81
    # G=objective(above), O=tools implied by squad, T=timeout, W=escalation, A=contact actions
    timeout: int = 300  # seconds (T — time expected)
    disengagement_criteria: list[str] = Field(default_factory=list)  # W — what if fail
    actions_on_contact: str = "report and hold"  # A — on unexpected response
    bypass_criteria: list[str] = Field(default_factory=list)  # conditions to skip

    # Weapons Control Status (para A-59/A-60)
    # hold=only if ordered, tight=confirmed targets only, free=any non-friendly
    weapons_control: Literal["hold", "tight", "free"] = "tight"


class MissionTasking(BaseModel):
    mission_id: str = ""
    target: str
    target_type: str
    depth: Literal["hasty", "deliberate"] = "deliberate"
    squad_tasks: list[SquadTasking] = Field(default_factory=list)
    mett_tc_analysis: str = ""

    # Intelligence requirements hierarchy (glossary: CCIR > PIR)
    ccir: str = ""  # Commander's Critical Information Requirement — the research thesis
    pirs: list[str] = Field(default_factory=list)  # Priority Intelligence Requirements per target
