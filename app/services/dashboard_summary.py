"""Read-only dashboard projection over persisted FinOps evidence."""

from collections import defaultdict
from datetime import datetime, timezone
import json

from app.database.models import CostCache, CostHistory, ExecutionMemory, LearningMetricMemory, OptimizationOutcomeMemory, RecommendationMemory


def _resource_in_subscription(resource_id, subscription_id):
    return (resource_id or "").lower().startswith(f"/subscriptions/{subscription_id.lower()}/")


def _resource_type(resource_id):
    parts = [part for part in (resource_id or "").split("/") if part]
    for index, part in enumerate(parts):
        if part.lower() == "providers" and index + 2 < len(parts):
            return f"{parts[index + 1]}/{parts[index + 2]}".lower()
    return None


def _resource_group(resource_id):
    parts = [part for part in (resource_id or "").split("/") if part]
    for index, part in enumerate(parts):
        if part.lower() == "resourcegroups" and index + 1 < len(parts):
            return parts[index + 1]
    return None


def _outcome_payload(row):
    return row.outcome if isinstance(row.outcome, dict) else {}


def _environment_snapshot(metrics, subscription_id):
    if isinstance(metrics, str):
        try:
            metrics = json.loads(metrics)
        except (TypeError, ValueError):
            return {}
    if not isinstance(metrics, dict) or metrics.get("subscription_id") != subscription_id:
        return {}
    environment = metrics.get("environment")
    if environment is None:
        environment = metrics
    return environment if isinstance(environment, dict) else {}


class DashboardSummaryService:
    def build(self, session, subscription_id):
        costs = session.query(CostCache).filter(CostCache.subscription_id == subscription_id).all()
        history = (
            session.query(CostHistory)
            .filter(CostHistory.subscription_id == subscription_id)
            .order_by(CostHistory.collected_at.asc())
            .all()
        )
        recommendations = [item for item in session.query(RecommendationMemory).all() if _resource_in_subscription(item.resource_id, subscription_id)]
        executions = [item for item in session.query(ExecutionMemory).all() if _resource_in_subscription(item.resource_id, subscription_id)]
        outcomes = [item for item in session.query(OptimizationOutcomeMemory).all() if _resource_in_subscription(item.resource_id, subscription_id)]
        environment = {}
        for metrics_row in session.query(LearningMetricMemory).order_by(LearningMetricMemory.calculated_at.desc()).all():
            environment = _environment_snapshot(metrics_row.metrics, subscription_id)
            if environment:
                break

        available_costs = [item for item in costs if item.monthly_cost is not None]
        monthly = round(sum(float(item.monthly_cost) for item in available_costs), 2) if available_costs else None
        by_service = defaultdict(float)
        for item in costs:
            monthly_cost = float(item.monthly_cost or 0)
            if monthly_cost > 0:
                by_service[item.service_name or "Unclassified"] += monthly_cost
        drivers = sorted(
            (item for item in available_costs if float(item.monthly_cost) > 0),
            key=lambda item: float(item.monthly_cost or 0),
            reverse=True,
        )[:5]
        potential = round(sum(float(item.estimated_savings or 0) for item in recommendations), 2)
        cost_by_resource = {item.resource_id.casefold(): item for item in costs}
        metrics_by_resource = {item.get("resource_id", "").casefold(): item for item in (environment.get("performance", {}).get("resources", []) or [])}
        recommendations_by_resource = defaultdict(list)
        for item in recommendations:
            recommendations_by_resource[item.resource_id.casefold()].append(item)
        diagnostics = []
        for resource in environment.get("resource_inventory", []):
            resource_id = str(resource.get("resource_id", "")).casefold()
            cost = cost_by_resource.get(resource_id)
            metric = metrics_by_resource.get(resource_id)
            linked_recommendations = recommendations_by_resource.get(resource_id, [])
            missing = []
            if cost is None or cost.monthly_cost is None: missing.append("cost")
            if not metric or metric.get("utilization_status") == "unavailable": missing.append("utilization")
            if resource.get("configuration_status") != "available": missing.append("configuration")
            if not linked_recommendations: missing.append("resource-specific recommendation")
            diagnostics.append({"resource_name": resource.get("resource_name"), "resource_id": resource.get("resource_id"), "cost_status": (cost.cost_status if cost else "unavailable"), "cost_source": (cost.cost_source if cost else "none"), "utilization_status": (metric.get("utilization_status") if metric else "unavailable"), "utilization_reason": (metric.get("utilization_reason") if metric else "no_data"), "configuration_status": resource.get("configuration_status", "unavailable"), "recommendation_status": "available" if linked_recommendations else "unavailable", "missing_data": missing})

        snapshots = defaultdict(float)
        resource_history = defaultdict(lambda: {"resource_name": None, "service_name": None, "points": defaultdict(float)})
        for item in history:
            if item.collected_at:
                snapshots[item.collected_at] += float(item.monthly_cost or 0)
            resource = resource_history[item.resource_id]
            resource["resource_name"] = item.resource_name or resource["resource_name"]
            resource["service_name"] = item.service_name or resource["service_name"]
            resource["points"][item.collected_at] += float(item.monthly_cost or 0)
        snapshot_points = [
            {"timestamp": timestamp.isoformat(), "monthly_cost": round(total, 2)}
            for timestamp, total in sorted(snapshots.items())[-12:]
        ]
        previous = snapshot_points[-2]["monthly_cost"] if len(snapshot_points) >= 2 else None
        change_percent = (
            round(((monthly - previous) / previous) * 100, 2)
            if monthly is not None and previous not in (None, 0)
            else None
        )
        forecast = (
            round(monthly + (monthly - previous), 2)
            if monthly is not None and previous is not None
            else None
        )

        def common_cost_value(attribute):
            values = {getattr(item, attribute) for item in costs}
            return next(iter(values)) if len(values) == 1 else None

        verified = []
        realized_values = []
        for row in outcomes:
            payload = _outcome_payload(row)
            verification = payload.get("verification", {})
            savings = payload.get("savings", {})
            if verification.get("status") in {"MEASURED", "PENDING_MEASUREMENT", "PASSED"}:
                verified.append((row, payload))
                if savings.get("realized") is not None:
                    realized_values.append(float(savings["realized"]))

        opportunity_counts = defaultdict(lambda: {"count": 0, "potential_savings": 0.0})
        for item in recommendations:
            category = item.category or item.action or "Uncategorized"
            opportunity_counts[category]["count"] += 1
            opportunity_counts[category]["potential_savings"] += float(item.estimated_savings or 0)

        recent = []
        for row, payload in sorted(verified, key=lambda value: value[0].recorded_at or datetime.min, reverse=True)[:10]:
            execution = payload.get("execution", {})
            verification = payload.get("verification", {})
            savings = payload.get("savings", {})
            recent.append({"action": execution.get("action"), "resource_id": row.resource_id, "execution_status": execution.get("status"), "verification_status": verification.get("status"), "realized_savings": savings.get("realized"), "timestamp": row.recorded_at.isoformat() if row.recorded_at else None})
        for row in sorted(executions, key=lambda item: item.executed_at or datetime.min, reverse=True):
            if len(recent) >= 10:
                break
            recent.append({"action": row.action, "resource_id": row.resource_id, "execution_status": row.status, "verification_status": None, "realized_savings": None, "timestamp": row.executed_at.isoformat() if row.executed_at else None})

        alerts = []
        if any(not item.approved for item in recommendations):
            alerts.append({"severity": "PENDING", "title": "Recommendations awaiting approval", "description": f"{sum(not item.approved for item in recommendations)} persisted recommendations are awaiting approval."})
        if monthly is not None and potential > 0:
            alerts.append({"severity": "INFO", "title": "Optimization opportunities available", "description": f"Persisted recommendations identify {potential:.2f} in potential monthly savings."})

        currency = common_cost_value("currency")
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "subscription_id": subscription_id,
            "cost": {"monthly": monthly, "previous": previous, "change_percent": change_percent, "forecast": forecast, "currency": currency, "cost_source": common_cost_value("cost_source"), "cost_type": common_cost_value("cost_type"), "is_estimated": common_cost_value("is_estimated")},
            "savings": {"potential_monthly": potential, "realized_monthly": round(sum(realized_values), 2) if realized_values else None, "verified_actions": len(verified)},
            "resources": {"total": len({item.resource_id for item in costs}) if costs else None, "underutilized": None, "high_risk": None, "optimization_candidates": len(recommendations)},
            "resource_inventory": environment.get("resource_inventory", []),
            "resource_diagnostics": diagnostics,
            "agent": {"status": "MONITORING" if recommendations or outcomes else "NO_PERSISTED_DATA", "recommendations": len(recommendations), "pending_approval": sum(not item.approved for item in recommendations), "executed": len(executions), "verification_pending": sum(1 for item in outcomes if _outcome_payload(item).get("verification", {}).get("status") in {"PENDING_MEASUREMENT", "NOT_EXECUTED"})},
            "cost_overview": {"trend": snapshot_points},
            "cost_by_resource": [
                {
                    "resource_id": resource_id,
                    "resource_name": value["resource_name"],
                    "service_name": value["service_name"],
                    "resource_group": resource_id.split("/")[4] if len(resource_id.split("/")) > 4 and resource_id.split("/")[3].lower() == "resourcegroups" else None,
                    "points": [
                        {"timestamp": timestamp.isoformat(), "monthly_cost": round(total, 2)}
                        for timestamp, total in sorted(value["points"].items())
                    ],
                }
                for resource_id, value in sorted(resource_history.items())
            ],
            "cost_composition": [{"name": name, "monthly_cost": round(value, 2)} for name, value in sorted(by_service.items(), key=lambda entry: entry[1], reverse=True) if value > 0],
            "cost_drivers": [
                {
                    "resource_id": item.resource_id,
                    "resource_name": item.resource_name,
                    "resource_type": _resource_type(item.resource_id),
                    "service_name": item.service_name,
                    "monthly_cost": item.monthly_cost,
                    "cost_status": item.cost_status or ("estimated" if item.is_estimated else "available" if item.monthly_cost is not None else "unavailable"),
                    "cost_source": item.cost_source or "none",
                    "percent_of_total": round(float(item.monthly_cost) / monthly * 100, 2) if monthly and monthly > 0 and item.monthly_cost is not None else None,
                }
                for item in drivers
            ],
            "cost_resources": [
                {
                    "resource_id": item.resource_id,
                    "resource_name": item.resource_name,
                    "resource_type": _resource_type(item.resource_id),
                    "service_name": item.service_name,
                    "resource_group": _resource_group(item.resource_id),
                    "monthly_cost": item.monthly_cost,
                    "cost": item.monthly_cost,
                    "cost_source": item.cost_source or "none",
                    "cost_type": item.cost_type or ("estimated" if item.is_estimated else "actual"),
                    "is_estimated": bool(item.is_estimated),
                    # CostCache does not persist a separate availability flag; a stored
                    # monthly value is the canonical availability signal for this projection.
                    "cost_data_available": item.monthly_cost is not None,
                    "cost_status": item.cost_status or ("estimated" if item.is_estimated else "available" if item.monthly_cost is not None else "unavailable"),
                    "percent_of_total": round(float(item.monthly_cost) / monthly * 100, 2) if monthly and monthly > 0 else None,
                }
                for item in sorted(
                    (item for item in costs if float(item.monthly_cost or 0) > 0),
                    key=lambda item: float(item.monthly_cost or 0),
                    reverse=True,
                )
            ],
            "optimization_opportunities": [{"category": name, **value} for name, value in sorted(opportunity_counts.items())],
            "recommendations": [{"recommendation_id": item.recommendation_id, "resource_id": item.resource_id, "resource_name": item.resource_name, "action": item.action, "potential_savings": item.estimated_savings, "confidence": item.confidence, "approved": item.approved} for item in sorted(recommendations, key=lambda item: float(item.estimated_savings or 0), reverse=True)[:3]],
            "recommendations_all": [{"recommendation_id": item.recommendation_id, "resource_id": item.resource_id, "resource_name": item.resource_name, "action": item.action, "potential_savings": item.estimated_savings, "confidence": item.confidence, "approved": item.approved} for item in sorted(recommendations, key=lambda item: float(item.estimated_savings or 0), reverse=True)],
            "security": environment.get("security", {"score": None, "critical": None, "high": None, "total": None}),
            "governance": environment.get("governance", {"compliance": None, "violations": None, "affected_resources": None}),
            "performance": environment.get("performance", {"average_cpu": None, "underutilized": None, "overutilized": None}),
            "recent_actions": recent,
            "alerts": alerts,
        }
