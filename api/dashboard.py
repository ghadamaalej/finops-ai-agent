from fastapi import APIRouter, Depends, HTTPException, Query
from app.Collectors.resource_collector import ResourceCollector
from app.services.resource_evidence import normalized_resource_id
from pydantic import BaseModel, Field
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import SessionLocal
from app.database.models import ApplicationUser, AzureConnection, CostCache, CostHistory, LearningMetricMemory, RecommendationMemory
from app.services.dashboard_summary import DashboardSummaryService
from app.services.entra_tokens import validate_azure_management_token, validate_id_token
from app.services.azure_context_builder import AzureContextBuilder
from app.services.learning_service import LearningService
from app.agent.nodes.intelligence_builder import build_intelligence_context
from app.agent.analyzers.cost_analyzer import CostAnalyzer
from app.agent.nodes.merge import merge_issues
from app.agent.nodes.reason import reason
from app.agent.nodes.validator import validate

import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])
bearer = HTTPBearer()
summary_service = DashboardSummaryService()


def create_cost_refresh_builder():
    return AzureContextBuilder()


def _detail_evidence(value, source, period=None, collected_at=None, reason=None):
    available = value is not None
    return {"value": value, "status": "available" if available else "unavailable", "source": source if available else None, "period": period, "collected_at": collected_at, "reason": None if available else (reason or "Metric not supported or not collected for this resource type")}


def _latest_environment(session, subscription_id):
    for row in session.query(LearningMetricMemory).order_by(LearningMetricMemory.calculated_at.desc()).all():
        payload = row.metrics if isinstance(row.metrics, dict) else {}
        if payload.get("subscription_id") == subscription_id:
            return payload.get("environment", payload), row.calculated_at
    return {}, None

def _resource_id_collection(value):
    # Return only real resource ID collections from current or legacy snapshots.
    if not isinstance(value, (list, tuple, set)):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _safe_isoformat(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if value is not None:
        return str(value)
    return None

def _normalize_environment(environment):
    environment = environment if isinstance(environment, dict) else {}
    performance = environment.get("performance")
    performance = performance if isinstance(performance, dict) else {}
    resources = performance.get("resources", [])
    resources = resources if isinstance(resources, list) else []
    security_findings = environment.get("security_findings", [])
    security_findings = security_findings if isinstance(security_findings, list) else []
    governance = environment.get("governance", {})
    governance = governance if isinstance(governance, dict) else {}
    affected_resources = _resource_id_collection(governance.get("affected_resources", []))
    policy_violations = governance.get("policy_violations", [])
    policy_violations = policy_violations if isinstance(policy_violations, list) else []
    return environment, performance, resources, security_findings, governance, affected_resources, policy_violations

def analyze_context(context, session):
    intelligence_state = build_intelligence_context({"azure_context": context})
    raw_issues = CostAnalyzer().analyze(intelligence_state["finops_context"])
    merged_state = merge_issues({**intelligence_state, "cost_issues": raw_issues})
    recommendation_state = reason(merged_state)
    validated_state = validate({**recommendation_state, "recommendation_intelligence": {"recommendation_confidence": 1.0}})
    recommendations = validated_state["validated_recommendations"]
    persisted_count = LearningService().save_recommendations(recommendations, db=session)
    matches = {
        metric.resource_id.lower()
        for metric in context.metrics
        if metric.resource_id and any(cost.resource_id.lower() == metric.resource_id.lower() for cost in context.resource_costs)
    }
    return {
        "resources_collected": len(context.resources),
        "priced_resources": len(context.resource_costs),
        "vm_metrics_collected": len(context.metrics),
        "cost_metric_resource_id_matches": len(matches),
        "low_cpu_candidates": sum(1 for metric in context.metrics if metric.cpu_average is not None and metric.cpu_average < 15),
        "analyzer_issues": len(raw_issues),
        "persisted_recommendations": persisted_count,
        "rejected_recommendations": len(validated_state["validation_errors"]),
    }


def connected_subscription(session, claims):
    user = session.query(ApplicationUser).filter_by(entra_subject_id=claims["sub"], tenant_id=claims["tid"], is_active=True).first()
    if user is None:
        raise HTTPException(status_code=401, detail="FinOps user session is not registered")
    connection = session.query(AzureConnection).filter_by(user_id=user.id, tenant_id=claims["tid"], connection_status="CONNECTED").order_by(AzureConnection.connected_at.desc()).first()
    if connection is None:
        raise HTTPException(status_code=403, detail="No Azure subscription is connected for this user")
    return connection.subscription_id


class DashboardRefreshRequest(BaseModel):
    azure_access_token: str = Field(min_length=20)


def _unavailable_summary(subscription_id):
    # Stable dashboard shape when optional persisted evidence is unavailable.
    return {
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "subscription_id": subscription_id,
        "data_status": "partial",
        "data_warning": "Optional dashboard evidence is temporarily unavailable.",
        "cost": {"monthly": None, "previous": None, "change_percent": None, "forecast": None, "currency": None, "cost_source": None, "cost_type": None, "is_estimated": None},
        "savings": {"potential_monthly": 0, "realized_monthly": None, "verified_actions": 0},
        "resources": {"total": None, "underutilized": None, "high_risk": None, "optimization_candidates": 0},
        "resource_inventory": [], "resource_diagnostics": [],
        "agent": {"status": "DATA_UNAVAILABLE", "recommendations": 0, "pending_approval": 0, "executed": 0, "verification_pending": 0},
        "cost_overview": {"trend": []}, "cost_by_resource": [], "cost_composition": [], "cost_drivers": [],
        "optimization_opportunities": [], "recommendations": [], "recommendations_all": [],
        "security": {"score": None, "critical": None, "high": None, "total": None},
        "governance": {"compliance": None, "violations": None, "affected_resources": None},
        "performance": {"average_cpu": None, "underutilized": None, "overutilized": None},
        "recent_actions": [], "alerts": [{"severity": "WARNING", "title": "Dashboard data unavailable", "description": "Retry later; no Azure resources were changed."}],
    }

def _runtime_status(resource):
    """Return only a real runtime state; provisioning is not runtime state."""
    resource_type = (resource.get("type") or "").lower()
    if resource_type == "microsoft.compute/virtualmachines":
        code = resource.get("power_state")
        return code.rsplit("/", 1)[-1].lower() if code else "N/A"
    return "N/A"

@router.get("/resources/details")
async def resource_details(resource_id: str = Query(...), credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    claims = validate_id_token(credentials.credentials)
    session = SessionLocal()
    try:
        subscription_id = connected_subscription(session, claims)
        resources = ResourceCollector().collect(subscription_id)
        resource = next((item for item in resources if normalized_resource_id(item.get("id")) == normalized_resource_id(resource_id)), None)
        if resource is None:
            raise HTTPException(status_code=404, detail="Resource not found in the connected subscription")
        environment, snapshot_at = _latest_environment(session, subscription_id)
        environment, performance, performance_resources, security_findings, governance, affected_resources, policy_violations = _normalize_environment(environment)
        rid = normalized_resource_id(resource.get("id"))
        metric = next((item for item in performance_resources if isinstance(item, dict) and normalized_resource_id(item.get("resource_id")) == rid), {})
        logger.info("Resource details snapshot types: environment=%s snapshot_at=%s metric=%s collected_at=%s metric_names=%s values=%s metric_errors=%s governance=%s performance=%s security_findings=%s", type(environment).__name__, type(snapshot_at).__name__, type(metric).__name__, type(metric.get("collected_at")).__name__, type(metric.get("metric_names")).__name__, type(metric.get("values")).__name__, type(metric.get("metric_errors")).__name__, type(governance).__name__, type(performance).__name__, type(security_findings).__name__)
        cost = session.query(CostCache).filter(CostCache.subscription_id == subscription_id, CostCache.resource_id == resource.get("id")).order_by(CostCache.collected_at.desc()).first()
        recommendations = session.query(RecommendationMemory).filter(RecommendationMemory.resource_id == resource.get("id")).order_by(RecommendationMemory.created_at.desc()).all()
        metric_names = metric.get("metric_names", [])
        metric_names = metric_names if isinstance(metric_names, list) else []
        values = metric.get("values", {})
        values = values if isinstance(values, dict) else {}
        metric_errors = metric.get("metric_errors", {})
        metric_errors = metric_errors if isinstance(metric_errors, dict) else {}
        period = f"last {metric.get('collected_days')} days" if metric.get("collected_days") else None
        collected_at = metric.get("collected_at") or _safe_isoformat(snapshot_at)
        metric_values = {name: _detail_evidence(values.get(name), "Azure Monitor", period, collected_at, (metric_errors.get(name, {}) or {}).get("reason") if isinstance(metric_errors.get(name, {}), dict) else None) for name in metric_names}
        aliases = {"cpu_average": metric.get("cpu_average"), "cpu_max": metric.get("cpu_max"), "memory": values.get("MemoryWorkingSet"), "requests": values.get("Requests"), "http_errors": values.get("Http5xx"), "network_in": values.get("Network In Total"), "network_out": values.get("Network Out Total"), "disk_read_iops": values.get("Composite Disk Read Operations/sec") or values.get("Disk Read Operations/Sec"), "disk_write_iops": values.get("Composite Disk Write Operations/sec") or values.get("Disk Write Operations/Sec"), "storage": values.get("StorageUsed") or values.get("storage_percent"), "dtu": values.get("dtu_consumption_percent")}
        for name, value in aliases.items(): metric_values.setdefault(name, _detail_evidence(value, "Azure Monitor", period, collected_at, metric.get("utilization_reason")))
        linked_security = [item for item in security_findings if isinstance(item, dict) and normalized_resource_id(item.get("resource_id")) == rid]
        affected = {normalized_resource_id(item) for item in affected_resources}
        linked_governance = policy_violations if rid in affected else []
        return {"resource": {"identity": {"id": resource.get("id"), "name": resource.get("name"), "type": resource.get("type"), "resource_group": resource.get("resource_group"), "region": resource.get("location")}, "configuration": {**(resource.get("configuration") or {}), "sku": resource.get("sku"), "sku_tier": resource.get("sku_tier"), "os_type": resource.get("os_type"), "vm_size": resource.get("vm_size"), "tags": resource.get("tags") or {}}, "runtime": {"provisioning_state": resource.get("provisioning_state"), "power_state": resource.get("power_state")}}, "metrics": {"status": metric.get("utilization_status", "unavailable"), "period": period, "source": "Azure Monitor", "collected_at": collected_at, "values": metric_values}, "cost": {"monthly": cost.monthly_cost if cost else None, "hourly_estimated": float(cost.monthly_cost) / 720 if cost and cost.monthly_cost is not None and cost.is_estimated else None, "currency": cost.currency if cost else None, "source": cost.cost_source if cost else None, "type": cost.cost_type if cost else None, "is_estimated": bool(cost.is_estimated) if cost else None, "status": cost.cost_status if cost else "unavailable"}, "finops": {"utilization": metric.get("utilization_status", "unavailable"), "recommendations": [{"action": item.action, "category": item.category, "recommended_action": item.action, "estimated_monthly_savings": item.estimated_savings, "risk": "unknown", "confidence": item.confidence, "evidence": "Persisted FinOps analyzer recommendation"} for item in recommendations]}, "security": {"scope": "resource", "status": "available" if linked_security else "unavailable", "findings": linked_security, "reason": None if linked_security else "No resource-scoped security findings collected"}, "governance": {"scope": "resource", "status": "available" if linked_governance else "unavailable", "policy_violations": linked_governance, "compliance": governance.get("compliance_score") if rid in affected else None, "reason": None if linked_governance else "No resource-scoped governance evidence collected"}, "evidence": {"resource": _detail_evidence(resource.get("id"), "Azure Resource Graph", collected_at=_safe_isoformat(snapshot_at)), "metrics": metric_values}}
    finally:
        session.close()

@router.get("/resources")
def resource_inventory(
    search: str | None = Query(None),
    resource_type: str | None = Query(None),
    resource_group: str | None = Query(None),
    region: str | None = Query(None),
    status: str = Query("all"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
):
    """Return the live Azure inventory, filtered before pagination."""
    claims = validate_id_token(credentials.credentials)
    session = SessionLocal()
    try:
        subscription_id = connected_subscription(session, claims)
        try:
            resources = ResourceCollector().collect(subscription_id)
        except Exception:
            # Preserve read access when Azure is temporarily unavailable.
            summary = summary_service.build(session, subscription_id)
            resources = [{
                "id": item.get("resource_id"), "name": item.get("resource_name"),
                "type": item.get("resource_type"), "resource_group": item.get("resource_group"),
                "location": item.get("location"), "sku": item.get("sku"),
                "power_state": item.get("power_state"), "provisioning_state": item.get("provisioning_state"),
                "configuration": item.get("configuration", {}),
            } for item in summary.get("resource_inventory", [])]
        costs = {normalized_resource_id(item.resource_id): item for item in session.query(CostCache).filter(CostCache.subscription_id == subscription_id).all()}
        needle = (search or "").strip().casefold()
        def project(resource):
            resource_id = resource.get("id")
            cost = costs.get(normalized_resource_id(resource_id))
            return {
                "resource_id": resource_id, "resource_name": resource.get("name"),
                "resource_type": resource.get("type"), "resource_group": resource.get("resource_group"),
                "location": resource.get("location"), "sku": resource.get("sku") or resource.get("vm_size") or resource.get("sku_name"),
                "configuration": resource.get("configuration", {}), "status": _runtime_status(resource),
                "provisioning_state": resource.get("provisioning_state"), "power_state": resource.get("power_state"),
                "monthly_cost": cost.monthly_cost if cost else None,
                "cost_source": (cost.cost_source if cost else None) or "none",
                "cost_type": cost.cost_type if cost else None,
                "cost_status": (cost.cost_status if cost else None) or ("estimated" if cost and cost.is_estimated else "available" if cost and cost.monthly_cost is not None else "unavailable"),
                "is_estimated": bool(cost.is_estimated) if cost else False,
            }
        items = [project(resource) for resource in resources if resource.get("id")]
        def matches(item):
            text = " ".join(str(item.get(key) or "") for key in ("resource_id", "resource_name", "resource_type", "resource_group", "location", "sku")).casefold()
            return (not needle or needle in text) and (not resource_type or (item["resource_type"] or "").casefold() == resource_type.casefold()) and (not resource_group or (item["resource_group"] or "").casefold() == resource_group.casefold()) and (not region or (item["location"] or "").casefold() == region.casefold()) and (status == "all" or (status == "active" and item["status"] in {"running", "active", "succeeded", "available"}) or (status == "other" and item["status"] not in {"running", "active", "succeeded", "available"}))
        items = sorted([item for item in items if matches(item)], key=lambda item: item["monthly_cost"] if item["monthly_cost"] is not None else -1, reverse=True)
        total = len(items)
        start = (page - 1) * page_size
        return {"items": items[start:start + page_size], "page": page, "page_size": page_size, "total": total, "has_next": start + page_size < total, "has_previous": page > 1 and start < total + page_size}
    finally:
        session.close()

@router.get("/summary")
def dashboard_summary(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    claims = validate_id_token(credentials.credentials)
    session = SessionLocal()
    try:
        subscription_id = connected_subscription(session, claims)
        try:
            return summary_service.build(session, subscription_id)
        except Exception:
            # SQLAlchemy marks the transaction failed after a database error.
            # Roll back before returning the optional fallback response so this
            # session cannot leak InFailedSqlTransaction to later work.
            session.rollback()
            # Dashboard evidence is a read-only, optional projection.  A broken
            # cache/metrics query must not turn the whole dashboard into a 503.
            logger.exception("Dashboard summary build failed: subscription_id=%s", subscription_id)
            return _unavailable_summary(subscription_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Dashboard summary connection lookup failed")
        raise HTTPException(status_code=503, detail="Dashboard data store unavailable") from exc
    finally:
        session.close()


@router.post("/refresh")
def refresh_dashboard_costs(payload: DashboardRefreshRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    """Explicit, read-only Azure collection for the authenticated connection."""
    claims = validate_id_token(credentials.credentials)
    azure_claims = validate_azure_management_token(payload.azure_access_token)
    if not claims.get("oid") or claims["oid"] != azure_claims.get("oid"):
        raise HTTPException(status_code=401, detail="Azure access token does not belong to the signed-in user")
    session = SessionLocal()
    try:
        subscription_id = connected_subscription(session, claims)
    except SQLAlchemyError as exc:
        logger.exception("Dashboard connection lookup failed")
        raise HTTPException(status_code=503, detail="Dashboard data store unavailable") from exc
    finally:
        session.close()

    try:
        result = create_cost_refresh_builder().refresh_costs(subscription_id, payload.azure_access_token)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("POST /api/dashboard/refresh failed: subscription_id=%s root_error=%s", subscription_id, exc)
        # refresh_costs commits only after a complete successful collection;
        # do not clear or overwrite the prior persisted snapshot on failure.
        raise HTTPException(status_code=502, detail="Azure cost collection failed; existing persisted data was preserved") from exc
    logger.info("POST /api/dashboard/refresh succeeded: subscription_id=%s records=%s", subscription_id, result.get("cost_records_collected"))
    return {**result, "status": "success", "message": "Azure cost data collected and persisted successfully."}


@router.post("/analyze")
def analyze_dashboard_costs(payload: DashboardRefreshRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    """Run read-only cost/CPU analysis and persist validated recommendations."""
    claims = validate_id_token(credentials.credentials)
    azure_claims = validate_azure_management_token(payload.azure_access_token)
    if not claims.get("oid") or claims["oid"] != azure_claims.get("oid"):
        raise HTTPException(status_code=401, detail="Azure access token does not belong to the signed-in user")
    session = SessionLocal()
    try:
        subscription_id = connected_subscription(session, claims)
        context = create_cost_refresh_builder().build_analysis_context(subscription_id, payload.azure_access_token)
        result = analyze_context(context, session)
        result["subscription_id"] = subscription_id
        session.commit()
        return result
    except SQLAlchemyError as exc:
        session.rollback()
        raise HTTPException(status_code=503, detail="Dashboard data store unavailable") from exc
    except Exception as exc:
        session.rollback()
        logger.exception("Dashboard analysis failed")
        raise HTTPException(status_code=502, detail="Azure analysis failed; no Azure resources were changed") from exc
    finally:
        session.close()
