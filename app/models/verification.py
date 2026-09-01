from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"
    UNSUPPORTED = "unsupported"
    ERROR = "error"


class VerificationResult(BaseModel):
    """Evidence captured after an execution attempt.

    Potential savings are kept separate from realized savings.  The latter is
    populated only after a real action and a comparable post-action cost.
    """

    verification_id: str = Field(default_factory=lambda: str(uuid4()))
    execution_id: str | None = None
    resource_id: str
    action: str
    status: VerificationStatus
    expected_state: dict[str, Any] = Field(default_factory=dict)
    actual_state: dict[str, Any] = Field(default_factory=dict)
    checks: dict[str, bool | None] = Field(default_factory=dict)
    evidence: dict[str, Any] = Field(default_factory=dict)
    dry_run: bool = False
    message: str = ""
    rollback_required: bool = False
    verified_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
