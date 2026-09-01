from datetime import datetime, timezone

from app.models.execution import ActionType, ExecutionRequest


def _value(recommendation, name, default=None):
    if isinstance(recommendation, dict):
        return recommendation.get(name, default)
    return getattr(recommendation, name, default)


def recommendation_to_execution_request(recommendation, dry_run: bool = True):
    """Translate a validated recommendation into an auditable execution plan."""
    action_value = _value(recommendation, "action_type") or _value(recommendation, "action")
    action = ActionType(action_value)
    recommended_state = _value(recommendation, "recommended_state", {}) or {}
    current_state = _value(recommendation, "current_state", {}) or {}
    parameters = {}

    if action == ActionType.RESIZE_VM:
        target_sku = (
            recommended_state.get("sku")
            or _value(recommendation, "target_sku")
        )
        if target_sku:
            parameters["target_sku"] = target_sku

    if action == ActionType.ENABLE_AUTOSHUTDOWN:
        schedule = _value(recommendation, "schedule")
        if schedule:
            parameters["schedule"] = schedule

    return ExecutionRequest(
        action=action,
        resource_id=_value(recommendation, "resource_id"),
        parameters=parameters,
        reason=_value(recommendation, "explanation", ""),
        estimated_savings=float(_value(recommendation, "potential_savings") or _value(recommendation, "estimated_savings", 0) or 0),
        baseline_monthly_cost=_value(recommendation, "current_cost"),
        expected_state=recommended_state,
        before_state={
            "resource_id": _value(recommendation, "resource_id"),
            "resource_name": _value(recommendation, "resource_name"),
            "resource_type": current_state.get("resource_type") or "Microsoft.Compute/virtualMachines",
            "current_sku": current_state.get("sku") or current_state.get("current_sku"),
            "region": current_state.get("region"),
            "power_state": current_state.get("power_state"),
            "observed_cpu_average": _value(recommendation, "observed_cpu_average_percent"),
            "observed_cpu_max": _value(recommendation, "observed_cpu_max_percent"),
            "monthly_cost": _value(recommendation, "current_cost"),
            "potential_savings": _value(recommendation, "potential_savings") or _value(recommendation, "estimated_savings", 0),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
        risk_level=str(_value(recommendation, "implementation_risk", "low")).lower(),
        confidence=float(_value(recommendation, "confidence", 0) or 0),
        requires_approval=bool(_value(recommendation, "requires_approval", True)),
        # Callers must opt in explicitly.  The production executor has its
        # own dry-run gate as a second independent protection.
        dry_run=dry_run,
    )
