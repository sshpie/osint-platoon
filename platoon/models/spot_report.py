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


class SPOTReport(BaseModel):
    squad: Literal["alpha", "bravo", "charlie", "weapons"]
    finds: list[Finding] = Field(default_factory=list)
    pivots: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)
    raw: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    iteration: int = 0
