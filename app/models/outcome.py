"""Immutable evidence contract joining recommendation and execution history."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class OptimizationOutcome(BaseModel):
    """Historical record; learning may measure it but must never rewrite it."""

    model_config = ConfigDict(frozen=True)

    outcome_id: str = Field(default_factory=lambda: str(uuid4()))
    execution_id: str | None = None
    recommendation_id: str | None = None
    resource_id: str
    recommendation: dict[str, Any] = Field(default_factory=dict)
    execution: dict[str, Any] = Field(default_factory=dict)
    before_state: dict[str, Any] = Field(default_factory=dict)
    after_state: dict[str, Any] = Field(default_factory=dict)
    verification: dict[str, Any] = Field(default_factory=dict)
    rollback: dict[str, Any] = Field(default_factory=dict)
    savings: dict[str, Any] = Field(default_factory=dict)
    recorded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
