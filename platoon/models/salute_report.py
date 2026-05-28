from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any
from datetime import datetime, timezone


class TimelineEntry(BaseModel):
    timestamp: str
    event: str
    source: str = ""


class SALUTEReport(BaseModel):
    # S — Subject
    subject: str
    subject_type: str = ""

    # A — Activity
    activity: list[str] = Field(default_factory=list)

    # L — Location
    location: list[str] = Field(default_factory=list)

    # U — Unit/Org
    unit_org: list[str] = Field(default_factory=list)

    # T — Timeline
    timeline: list[TimelineEntry] = Field(default_factory=list)

    # E — Exposure
    exposure: list[dict[str, Any]] = Field(default_factory=list)

    # Meta
    confidence_overall: float = Field(ge=0.0, le=1.0, default=0.0)
    executive_summary: str = ""
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    iteration_count: int = 0
    target: str = ""
