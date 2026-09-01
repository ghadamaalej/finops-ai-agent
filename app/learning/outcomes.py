"""Deterministically build Phase 6 learning evidence from completed actions."""

from typing import Any

from app.models.outcome import OptimizationOutcome


def _value(value: Any, key: str, default=None):
    return value.get(key, default) if isinstance(value, dict) else getattr(value, key, default)


def _status(value):
    return getattr(value, "value", value)


def build_outcome(recommendation, execution, verification: dict | None = None, approval_id: str | None = None):
    """Create one immutable outcome without inferring unobserved economics."""
    verification = verification or {}
    potential = _value(recommendation, "potential_savings")
    estimated = _value(recommendation, "estimated_savings", 0)
    return OptimizationOutcome(
        execution_id=_value(execution, "execution_id"),
        recommendation_id=_value(recommendation, "source_issue_id"),
        resource_id=_value(execution, "resource_id") or _value(recommendation, "resource_id"),
        recommendation={
            "action": _status(_value(execution, "action") or _value(recommendation, "action_type")),
            "confidence": _value(recommendation, "confidence", 0),
            "potential_savings": potential if potential is not None else estimated,
            "estimated_savings": estimated,
            "cost_source": _value(recommendation, "cost_source"),
            "cost_type": _value(recommendation, "cost_type"),
        },
        execution={
            "status": _status(_value(execution, "status")),
            "dry_run": bool(_value(execution, "dry_run", False)),
            "approval_id": approval_id,
            "executed_at": _value(execution, "executed_at"),
        },
        before_state=_value(execution, "previous_state", {}) or {},
        after_state=_value(verification, "actual_state", _value(execution, "new_state", {})) or {},
        verification={
            "status": _value(verification, "verification_status", "NOT_EXECUTED"),
            "checks": _value(verification, "checks", {}) or {},
            "evidence": _value(verification, "evidence", {}) or {},
        },
        rollback={
            "required": bool((_value(verification, "rollback", {}) or {}).get("rollback_required", False)),
            "status": _value(verification, "rollback_status", "not_required"),
            "verified": _value(verification, "final_state") == "BEFORE_STATE",
            "manual_intervention_required": bool(_value(verification, "manual_intervention_required", False)),
        },
        savings={
            "potential": potential if potential is not None else estimated,
            "estimated": estimated,
            "realized": _value(verification, "realized_savings"),
            "status": _value(verification, "savings_status", "NOT_YET_VERIFIABLE"),
        },
    )


def feedback_for(recommendation, outcome: OptimizationOutcome | None, approved: bool, decision: str | None = None, reason: str | None = None):
    """A compact recommendation feedback record suitable for later persistence."""
    execution = outcome.execution if outcome else {}
    verification = outcome.verification if outcome else {}
    result = {
        "recommendation_id": _value(recommendation, "source_issue_id"),
        "resource_id": _value(recommendation, "resource_id"),
        "approved": approved,
        "decision": decision or ("APPROVED" if approved else "DEFERRED"),
        "executed": bool(outcome) and not execution.get("dry_run", False),
        "verified": verification.get("status") in {"MEASURED", "PENDING_MEASUREMENT", "PASSED"},
        "failed": bool(outcome) and execution.get("status") in {"failed_verification", "rollback_failed", "failed"},
    }
    if reason:
        result["reason"] = reason
    return result
