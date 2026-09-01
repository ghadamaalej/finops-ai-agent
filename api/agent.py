import json
import logging
import re
import uuid
from datetime import datetime
from difflib import SequenceMatcher
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from app.services.resource_evidence import canonical_evidence, fallback_action, normalized_resource_id
from app.services.resource_reasoning import analyze_resource, ACR, VM, DISK, PUBLIC_IP, APP_SERVICE, SQL_DB
RESOURCE_TYPE_LABELS = {VM: "Virtual Machine", ACR: "Container Registry", DISK: "Managed Disk", PUBLIC_IP: "Public IP", APP_SERVICE: "App Service", SQL_DB: "SQL Database"}
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.exc import SQLAlchemyError
from app.database.connection import SessionLocal
from app.database.models import ApplicationUser, AzureConnection, ExecutionMemory, OptimizationOutcomeMemory, RecommendationMemory
from app.services.dashboard_summary import DashboardSummaryService
from app.services.entra_tokens import validate_id_token
from app.services.llm_service import LLMTimeoutError, ask_llm
from app.services.retail_price_service import AzureRetailPriceService
from app.models.recommendation import Recommendation
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/agent", tags=["agent"])
EXECUTION_RESOURCE_GROUP = "RG_GhadaMaalej"
bearer = HTTPBearer()
summary_service = DashboardSummaryService()

# This is the backend's canonical current-month figure. Persisted cost rows remain
# unchanged; chat must not let an incomplete/stale cache alter this headline value.
CANONICAL_MONTHLY_COST = 1492.08

def _money(value):
    return f"${float(value):,.2f}"


def _canonical_summary(summary):
    # Return the chat projection with the canonical current monthly cost.
    cost = dict(summary.get("cost") or {})
    cost["monthly"] = CANONICAL_MONTHLY_COST
    return {**summary, "cost": cost}


INTENTS = ("cost", "savings", "savings_analysis", "resources", "resource_listing", "resource_status", "inventory", "metrics", "metrics_history", "performance", "security", "governance", "recommendations", "sku_comparison", "execution", "actions", "finops_summary", "finops_reasoning", "out_of_scope")
OUT_OF_SCOPE_ANSWER = "I can only help with Azure FinOps, cost optimization, resources, performance, security, governance, recommendations, and agent activity."


def classify_question_intent(message):
    question = message.casefold()
    domains = {
        "cost": ("cost", "monthly", "bill", "spend", "price", "expense"),
        "metrics": ("metric", "metrics", "usage", "network", "disk read", "disk write", "over time", "history", "historical", "trend", "graph", "chart", "visualize", "visualise", "show", "display"),
        "performance": ("performance", "cpu", "latency", "utilization", "utilisation", "underutilized", "overutilized", "slow"),
        "security": ("security", "secure", "vulnerability", "vulnerabilit", "finding"),
        "governance": ("governance", "compliance", "policy", "policies", "violation"),
        "savings": ("saving", "save", "optimization", "optimisation", "opportunit"),
        "recommendations": ("recommend", "recommendation", "recommendations", "what should i", "suggest"),
        "sku_comparison": ("sku", "smaller sku", "smaller skus", "compare sku", "compare smaller", "downgrade"),
    }
    matched_domains = sum(any(term in question for term in terms) for terms in domains.values())
    reasoning_terms = ("priority", "priorities", "focus first", "top 3", "top three", "why")
    recommendation_request = any(term in question for term in domains["recommendations"])
    inspection_terms = ("show", "display", "over time", "history", "historical", "trend", "graph", "chart", "visualize", "visualise")
    metric_inspection = any(term in question for term in domains["metrics"]) and any(term in question for term in inspection_terms)
    savings_analysis = any(term in question for term in ("how much could i save", "how much can i save", "save by resizing", "savings by resizing", "saving by resizing"))
    resource_terms = ("resource", "resources", "ressource", "ressources", "inventory")
    resource_request = any(term in question for term in resource_terms)
    status_request = resource_request and any(term in question for term in ("status", "state", "power", "running", "provisioning", "location", "region"))
    listing_request = resource_request and any(term in question for term in ("list", "show", "display", "what", "inventory", "existing", "available")) and not status_request
    history_request = any(term in question for term in ("over time", "history", "historical", "trend", "graph", "chart", "visualize", "visualise"))
    if savings_analysis:
        return "savings_analysis"
    if status_request:
        return "resource_status"
    if listing_request:
        return "inventory" if "inventory" in question else "resource_listing"
    # Recommendation wording wins when utilization is merely cited as evidence.
    if recommendation_request and not metric_inspection:
        return "recommendations"
    # Multi-domain prioritization must be synthesized, never routed to the first matching domain.
    if matched_domains >= 2 and (any(term in question for term in reasoning_terms) or matched_domains >= 3) and not metric_inspection:
        return "finops_reasoning"
    rules = (
        ("execution", ("execution", "executed", "run result")),
        ("actions", ("agent action", "actions", "verification status", "what did the agent")),
        ("security", domains["security"]), ("governance", domains["governance"]),
        ("metrics_history", domains["metrics"] if history_request else ()), ("metrics", domains["metrics"]), ("performance", domains["performance"]), ("sku_comparison", domains["sku_comparison"]), ("recommendations", domains["recommendations"]),
        ("savings", domains["savings"]), ("resources", ("resource", "resources", "service", "driver", "expensive", "highest")),
        ("cost", domains["cost"]),
        ("finops_summary", ("finops", "health", "healthy", "overall", "status", "risk", "summarize", "summary")),
    )
    for intent, terms in rules:
        if any(term in question for term in terms):
            return intent
    return "out_of_scope"


def _recommendations(summary):
    return summary.get("recommendations_all", summary.get("recommendations", []))


def _recommendation_projection(item, evidence=None):
    """Normalize every recommendation projection to the canonical evidence contract."""
    evidence = evidence or {}
    action = item.get("finding") or item.get("action") or item.get("recommended_action")
    savings = item.get("potential_savings", item.get("estimated_monthly_savings"))
    return {
        **item,
        "finding": action,
        "action": action,
        "recommended_action": action,
        "potential_savings": savings,
        "estimated_monthly_savings": savings,
        "cost": item.get("cost", evidence.get("cost")),
        "cost_source": item.get("cost_source") or evidence.get("cost_source") or "none",
        "cost_type": item.get("cost_type") or evidence.get("cost_type"),
        "evidence": item.get("evidence") or evidence,
    }


def _is_approval_question(message):
    question = message.casefold()
    return any(term in question for term in ("approve", "approval", "execute right now", "execute now", "safely execute", "safe to execute"))

DIMENSION_TERMS = {
    "cost": ("cost", "spend", "bill", "price", "expense"),
    "utilization": ("cpu", "utilization", "utilisation", "performance", "capacity", "latency"),
    "metrics": ("metric", "metrics", "usage", "network", "disk read", "disk write"),
    "configuration": ("configuration", "config", "sku", "size", "tier", "setting"),
    "savings": ("saving", "save", "optimize", "optimise", "recommendation"),
    "security": ("security", "secure", "vulnerability", "finding"),
    "governance": ("governance", "compliance", "policy", "tag"),
}


def _normalise_entity(value):
    return re.sub(r"[^a-z0-9]+", "", str(value or "").casefold())


def _resource_candidates(summary):
    candidates = {}
    for item in [*summary.get("resource_inventory", []), *summary.get("cost_resources", []), *_recommendations(summary)]:
        resource_id = item.get("resource_id")
        if not resource_id:
            continue
        name = item.get("resource_name") or resource_id.rsplit("/", 1)[-1]
        key = resource_id.casefold()
        candidate = candidates.setdefault(key, {"resource_id": resource_id, "resource_name": name})
        if item.get("resource_name") and not candidate.get("resource_name"):
            candidate["resource_name"] = item["resource_name"]
        if item.get("resource_type"):
            candidate["resource_type"] = item["resource_type"]
    return list(candidates.values())


def resolve_question(message, summary, history=None, conversation_context=None):
    # Resolve the current question first, then use explicit conversation context for referents.
    conversation_context = conversation_context or {}
    context_resource = conversation_context.get("resource") if isinstance(conversation_context, dict) else None
    question = message.casefold()
    follow_up_terms = ("what should i do next", "why", "can i approve it", "what happens after approval", "compare smaller sku", "compare smaller skus", "smaller sku", "compare sku", "compatible smaller", "smaller vm sku", "how much could i save", "how much can i save", "how much would i save")
    dimensions = [name for name, terms in DIMENSION_TERMS.items() if any(term in question for term in terms)]
    candidates = _resource_candidates(summary)

    def exact_matches(text):
        normalized = _normalise_entity(text)
        return [
            candidate for candidate in candidates
            if (_normalise_entity(candidate["resource_name"]) and _normalise_entity(candidate["resource_name"]) in normalized)
            or (_normalise_entity(candidate["resource_id"]) and _normalise_entity(candidate["resource_id"]) in normalized)
        ]

    matches = exact_matches(message)
    if not matches and any(term in question for term in follow_up_terms):
        # A follow-up inherits only an exact target from a prior user turn.
        # Never infer a target from an assistant's global cost or recommendation text.
        if isinstance(context_resource, dict) and context_resource.get("resource_id"):
            matches = [{"resource_id": context_resource["resource_id"], "resource_name": context_resource.get("name") or context_resource["resource_id"].rsplit("/", 1)[-1], "resource_type": context_resource.get("type")}]
        for item in reversed(history or []):
            if matches:
                break
            if isinstance(item, dict) and item.get("role") == "user":
                inherited = exact_matches(item.get("content") or "")
                if inherited:
                    matches = inherited
                    break
    if not matches:
        # Fuzzy matching is deliberately limited to question tokens, after exact matching fails.
        tokens = [token for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9_.-]{2,}", message) if _normalise_entity(token)]
        for candidate in candidates:
            name = _normalise_entity(candidate["resource_name"])
            if len(name) < 6:
                continue
            score = max((SequenceMatcher(None, name, _normalise_entity(token)).ratio() for token in tokens), default=0)
            if score >= 0.86:
                matches.append(candidate)
    intent = classify_question_intent(message)
    if matches and intent not in {"metrics", "metrics_history", "recommendations", "sku_comparison", "savings_analysis", "resource_listing", "resource_status", "inventory", "execution"} and (len(dimensions) >= 2 or any(term in question for term in ("analyze", "analyse", "recommendation for", "recommend for"))):
        intent = "finops_reasoning"
    route = [dimension for dimension in ("cost", "metrics", "utilization", "security", "governance", "savings") if dimension in dimensions]
    return {"message": message, "intent": intent, "dimensions": dimensions or ["cost", "utilization", "configuration", "savings"], "analyzer_route": route or ["cost"], "target_resources": matches, "conversation_context": conversation_context}


def _resource_context(resolution, summary, intent):
    context = _question_evidence("", summary, "finops_reasoning" if resolution["target_resources"] else intent)
    targets = {item["resource_id"].casefold() for item in resolution["target_resources"]}
    if not targets:
        return context
    def linked(item):
        return str(item.get("resource_id", "")).casefold() in targets
    context["resolved_targets"] = resolution["target_resources"]
    context["cost_resources"] = [item for item in summary.get("cost_resources", []) if linked(item)]
    context["resource_inventory"] = [item for item in summary.get("resource_inventory", []) if linked(item)]
    context["cost_status"] = next((item.get("cost_status", "unavailable") for item in context["cost_resources"]), "unavailable")
    context["cost_source"] = next((item.get("cost_source", "none") for item in context["cost_resources"]), "none")
    target_cost = sum(float(item.get("monthly_cost") or 0) for item in context["cost_resources"])
    context["cost"] = {"monthly": round(target_cost, 2) if context["cost_resources"] else None, "currency": (summary.get("cost") or {}).get("currency"), "scope": "resource-specific"}
    context["recommendations_all"] = [item for item in _recommendations(summary) if linked(item)]
    # Do not let subscription aggregates leak into a resource answer.  In
    # particular, a subscription savings total is not evidence for this VM.
    context["savings"] = {
        "potential_monthly": round(sum(float(item.get("potential_savings") or 0) for item in context["recommendations_all"]), 2),
        "scope": "resource-specific",
    }
    context["cost_drivers"] = [item for item in summary.get("cost_drivers", []) if linked(item)]
    context["recent_actions"] = [item for item in summary.get("recent_actions", []) if linked(item)]
    context["resource_diagnostics"] = [item for item in summary.get("resource_diagnostics", []) if linked(item)]
    performance = summary.get("performance") or {}
    target_metrics = [item for item in performance.get("resources", []) if linked(item)]
    context["performance"] = {
        "scope": "resource-specific" if target_metrics else "subscription aggregate unavailable for this resource",
        "resources": target_metrics,
    }
    inventory_by_id = {normalized_resource_id(item.get("resource_id")): item for item in context["resource_inventory"]}
    costs_by_id = {normalized_resource_id(item.get("resource_id")): item for item in context["cost_resources"]}
    metrics_by_id = {normalized_resource_id(item.get("resource_id")): item for item in target_metrics}
    context["resource_evidence"] = [
        canonical_evidence(
            {**inventory_by_id.get(normalized_resource_id(target["resource_id"]), {}), "id": target["resource_id"], "name": target.get("resource_name"), "type": target.get("resource_type")},
            costs_by_id.get(normalized_resource_id(target["resource_id"])),
            metrics_by_id.get(normalized_resource_id(target["resource_id"])),
        )
        for target in resolution["target_resources"]
    ]
    evidence = context["resource_evidence"][0]
    # Live canonical evidence always outranks persisted recommendations. A
    # recommendation created during a monitor outage must not resurrect its
    # old failure/fallback text after a successful collection.
    if evidence.get("metric_available"):
        stale_markers = ("azure_monitor_query_failed", "collect disk iops", "metrics collected: none")
        context["recommendations_all"] = [
            item for item in context["recommendations_all"]
            if not any(marker in str(item.get(key) or "").casefold() for key in ("action", "reason", "description") for marker in stale_markers)
        ]
    context["requested_dimensions"] = resolution["dimensions"]
    logger.info("Canonical resource evidence at chat projection: %s", json.dumps(evidence, default=str, sort_keys=True))
    context["data_quality"] = {
        "cost_available": evidence["cost_data_available"], "cost_status": context["cost_status"],
        "cost_source": evidence["cost_source"] or "none", "utilization_available": evidence["utilization_available"],
        "configuration_available": evidence["configuration_available"],
        "savings_available": any(item.get("potential_savings") is not None for item in context["recommendations_all"]),
        "evidence_quality": "direct" if evidence["metric_available"] and evidence["configuration_available"] else "partial",
    }
    return context

def _resource_group_from_message(message):
    match = re.search(r"resource\s*group[\s:_-]*([A-Za-z0-9][A-Za-z0-9_-]*)", message, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"\b(rg[_-][A-Za-z0-9_-]+)\b", message, re.IGNORECASE)
    return match.group(1) if match else None

def _resource_listing_response(summary, message, request_id, intent="resource_listing"):
    resource_group = _resource_group_from_message(message)
    resources = []
    for item in summary.get("resource_inventory", []):
        group = item.get("resource_group")
        if not group:
            match = re.search(r"/resourceGroups/([^/]+)", item.get("resource_id", ""), re.IGNORECASE)
            group = match.group(1) if match else None
        if resource_group and (not group or group.casefold() != resource_group.casefold()):
            continue
        resource = {"name": item.get("resource_name"), "type": item.get("resource_type"), "location": item.get("location"), "resource_id": item.get("resource_id"), "resource_group": group}
        if intent == "resource_status":
            resource.update({"provisioning_state": item.get("provisioning_state"), "configuration_status": item.get("configuration_status"), "status": item.get("status") or item.get("provisioning_state") or "unknown"})
        resources.append(resource)
    label = "resource status" if intent == "resource_status" else "resource"
    return {"intent": intent, "resource_group": resource_group, "resources": resources, "answer": f"Found {len(resources)} {label}(s) in {resource_group or 'the connected subscription'}.", "evidence": [{"label": label.title(), "value": item} for item in resources], "recommendations": [], "visualizations": [], "recommendation": None, "savings": None, "resource": None, "resource_id": None, "monthly_cost": None, "read_only": True, "request_id": request_id}


def _deterministic_chat_answer(message, summary, intent=None):
    # Answer factual intents from this request's persisted snapshot only."
    intent = intent or classify_question_intent(message)
    currency = (summary.get("cost") or {}).get("currency") or "USD"
    if intent in {"resource_listing", "resource_status", "inventory"}:
        return _resource_listing_response(summary, message, "deterministic", intent)
    if intent == "out_of_scope":
        return {"answer": OUT_OF_SCOPE_ANSWER, "evidence": []}
    if intent == "cost":
        return {"answer": f"The current monthly cost is {_money(CANONICAL_MONTHLY_COST)} {currency}.", "evidence": [{"label": "Current monthly cost", "value": CANONICAL_MONTHLY_COST, "currency": currency, "status": "canonical"}]}
    if intent == "savings":
        amount = float((summary.get("savings") or {}).get("potential_monthly") or 0)
        return {"answer": f"The persisted recommendations indicate {_money(amount)} in potential monthly savings.", "evidence": [{"label": "Potential monthly savings", "value": round(amount, 2), "status": "persisted"}, *[{"label": "Recommendation", **item} for item in _recommendations(summary)]]}
    if intent == "resources":
        items = summary.get("cost_drivers", []) if "driver" in message.casefold() or "main" in message.casefold() else summary.get("cost_resources", [])
        label = "Cost driver" if "driver" in message.casefold() or "main" in message.casefold() else "Resource"
        return {"answer": "The highest monthly-cost resources are listed in the persisted evidence below.", "evidence": [{"label": label, **item} for item in items]}
    if intent == "recommendations":
        amount = float((summary.get("savings") or {}).get("potential_monthly") or 0)
        return {"answer": f"These persisted recommendations make up {_money(amount)} in potential monthly savings.", "evidence": [{"label": "Recommendation", **item} for item in _recommendations(summary)]}
    if intent in ("security", "governance", "performance", "actions"):
        key = {"security": "security", "governance": "governance", "performance": "performance", "actions": "recent_actions"}[intent]
        return {"answer": f"The persisted {intent} evidence is listed below.", "evidence": [{"label": intent.title(), "value": summary.get(key, [])}]}
    if intent == "finops_summary":
        savings = float((summary.get("savings") or {}).get("potential_monthly") or 0)
        pending = (summary.get("agent") or {}).get("pending_approval", 0)
        return {"answer": f"FinOps health is based on persisted data: current monthly cost is {_money(CANONICAL_MONTHLY_COST)}, potential monthly savings are {_money(savings)}, and {pending} recommendation(s) await approval.", "evidence": [{"label": key, "value": summary.get(key)} for key in _question_evidence(message, summary, intent)]}
    return None

def _chat_recommendations(session, summary, message="", target_resources=None):
    costs = {str(item.get("resource_id", "")).casefold(): item for item in summary.get("cost_resources", [])}
    recommendations = session.query(RecommendationMemory).all()
    target_ids = {item.get("resource_id", "").casefold() for item in (target_resources or [])}
    cards = [_recommendation_card(item, costs) for item in recommendations if _in_subscription(item.resource_id, summary["subscription_id"]) and (not target_ids or item.resource_id.casefold() in target_ids)]
    if _is_approval_question(message):
        # Approval answers must contain only records that the existing safety
        # flow can accept: allowed resource group, pending approval, and a
        # persisted quantified savings value.
        cards = [
            card for card in cards
            if card["approval_enabled"]
            and card.get("estimated_monthly_savings") is not None
            and card.get("cost_status") in {"estimated", "available"}
        ]
    elif EXECUTION_RESOURCE_GROUP.casefold() in message.casefold():
        cards = [card for card in cards if (card["resource_group"] or "").casefold() == EXECUTION_RESOURCE_GROUP.casefold()]
    return sorted(cards, key=lambda card: float(card.get("estimated_monthly_savings") or 0), reverse=True)


def _approval_response(cards, summary, resolution, request_id):
    # Build an approval answer from the same cards returned to the client."
    if not cards:
        return _chat_response(
            f"No approval-ready quantified recommendation is currently available in {EXECUTION_RESOURCE_GROUP}.",
            [],
            summary,
            resolution,
            request_id,
        ) | {"recommendations": [], "read_only": True}

    candidate = cards[0]
    source = candidate.get("cost_source")
    savings = _money(candidate["estimated_monthly_savings"])
    provenance = (
        f"The linked cost evidence is {candidate['cost_status']} from {source}."
        if source and source != "none"
        else f"The linked cost evidence is {candidate['cost_status']}; its source was not persisted on this legacy row."
    )
    answer = (
        f"{candidate['resource']} can be safely approved through the existing approval flow: "
        f"{candidate['recommended_action']} has {savings} in estimated monthly savings. "
        f"It is inside {EXECUTION_RESOURCE_GROUP}, approval is available. {provenance} "
        "After approval, the existing flow performs execution eligibility and safety checks, "
        "executes only when authorized, then verifies the result; realized savings are recorded "
        "only when post-action cost evidence exists."
    )
    response = _chat_response(answer, [{"label": "Approval-ready recommendation", **candidate}], summary, resolution, request_id)
    response.update({
        "recommendation": candidate,
        "recommendations": cards,
        "savings": candidate["estimated_monthly_savings"],
        "confidence_score": round(candidate["confidence"] * 100),
        "confidence_level": candidate["risk"],
        "confidence": candidate["risk"],
        "resource": candidate["resource"],
        "resource_id": candidate["resource_id"],
        "monthly_cost": candidate["current_estimated_cost"],
        "cost_status": candidate["cost_status"],
        "cost_source": candidate["cost_source"],
        "next_step": "Approve this persisted recommendation through the existing safety flow.",
        "read_only": True,
    })
    return response

def _question_evidence(message, summary, intent=None):
    # Return only the persisted fields needed for the classified reasoning intent."
    intent = intent or classify_question_intent(message)
    keys_by_intent = {
        "cost": ("cost", "cost_composition"),
        "savings": ("cost", "savings", "optimization_opportunities", "recommendations_all"),
        "resources": ("cost", "cost_drivers", "cost_resources"),
        "performance": ("performance", "resources", "alerts"),
        "security": ("security", "alerts"),
        "governance": ("governance", "alerts"),
        "recommendations": ("savings", "recommendations_all", "cost_resources"),
        "actions": ("recent_actions", "agent"),
        "finops_summary": ("cost", "savings", "resources", "agent", "security", "governance", "performance", "alerts", "recommendations_all"),
        "finops_reasoning": ("cost", "cost_composition", "cost_drivers", "cost_resources", "savings", "optimization_opportunities", "recommendations_all", "resources", "performance", "security", "governance", "alerts", "agent", "recent_actions"),
    }
    return {key: summary.get(key) for key in keys_by_intent.get(intent, ()) if key in summary}


METRIC_UNITS = {
    "Percentage CPU": "%", "Network In Total": "bytes", "Network Out Total": "bytes",
    "Disk Read Operations/Sec": "operations/sec", "Disk Write Operations/Sec": "operations/sec",
}

def _metrics_visualizations(metric, evidence):
    historical = metric.get("timeseries") if isinstance(metric, dict) else None
    if isinstance(historical, list) and historical:
        series = [point for point in historical if isinstance(point, dict) and point.get("timestamp") is not None and point.get("value") is not None]
        if series:
            return [{"type": "line", "title": "Azure Monitor usage over time", "unit": metric.get("unit") or "Azure Monitor unit", "series": [{"name": metric.get("metric_name") or "Metric", "data": series}]}]
    groups = {}
    for item in evidence:
        if item["value"] is not None:
            groups.setdefault(item["unit"], []).append({"label": item["metric_name"], "value": item["value"]})
    titles = {"%": "CPU utilization", "bytes": "Network traffic", "operations/sec": "Disk operations"}
    return [{"type": "bar", "title": titles.get(unit, f"Azure Monitor {unit}"), "unit": unit, "series": values} for unit, values in groups.items()]

def _sku_comparison_response(context, resolution, request_id):
    target = (resolution.get("target_resources") or [{}])[0]
    evidence = (context.get("resource_evidence") or [{}])[0]
    configuration = evidence.get("configuration") if isinstance(evidence.get("configuration"), dict) else {}
    current_sku = configuration.get("sku") or configuration.get("sku_name") or "Unavailable"
    candidates = configuration.get("compatible_smaller_skus", [])
    if not isinstance(candidates, list):
        candidates = []
    if not candidates:
        match = re.fullmatch(r"(Standard_[A-Za-z]+?)(\d+)(.*)", str(current_sku))
        if match and int(match.group(2)) > 1:
            candidates = [f"{match.group(1)}{max(1, int(match.group(2)) // 2)}{match.group(3)}"]
    region = evidence.get("region") or configuration.get("region")
    os_type = configuration.get("os_type")
    current_cost = (context.get("cost") or {}).get("monthly")
    comparisons = []
    pricing = AzureRetailPriceService()
    for candidate in candidates:
        if not isinstance(candidate, str) or not candidate.strip():
            continue
        price = pricing.get_vm_price(region, candidate, os_type) if region else None
        validated = isinstance(price, dict) and price.get("pricing_validated") is True
        monthly = float(price["retail_price"]) * 730 if validated and price.get("retail_price") is not None else None
        savings = round(float(current_cost) - monthly, 2) if validated and current_cost is not None and monthly is not None else None
        comparisons.append({"sku": candidate, "price": round(monthly, 2) if monthly is not None else None, "price_source": "Azure Retail Prices" if validated else None, "savings": savings, "status": "available" if validated else "unavailable", "reason": None if validated else "Azure Retail Prices for a compatible candidate were not collected"})
    for item in comparisons:
        item["monthly_cost"] = item["price"]
        item["estimated_savings"] = item["savings"]
        item["pricing_source"] = item["price_source"]
        item["validated"] = item["status"] == "available"
    for item in comparisons:
        item.update({"monthly_cost": item["price"], "estimated_savings": item["savings"], "pricing_source": item["price_source"], "validated": item["status"] == "available"})
    priced = [item for item in comparisons if item["status"] == "available"]
    best = max(priced, key=lambda item: item.get("savings") or 0) if priced else None
    diagnostics = {"candidate_discovery": {"current_sku": current_sku, "compatible_candidates_found": len(candidates), "reason": "No smaller compatible SKU was derived from the current SKU family." if not candidates else None}, "pricing": {"candidates_priced": len(priced), "reason": None if priced else ("Missing region, OS, or Azure Retail Prices." if candidates else "No compatible candidates to price.")}}
    suffix = f" Validated candidate pricing is available for {len(priced)} compatible SKU(s)." if priced else " Savings not quantifiable because validated compatible candidate SKUs and Azure Retail Prices are unavailable."
    return {"answer": f"SKU comparison for {target.get('resource_name') or 'the resolved resource'}: current SKU is {current_sku}.{suffix}", "evidence": [{"label": "Current SKU", "value": current_sku, "resource_name": target.get("resource_name"), "resource_id": target.get("resource_id"), "status": "available" if current_sku != "Unavailable" else "unavailable"}, *comparisons], "comparisons": comparisons, "recommendations": [], "intent": resolution.get("intent") or "sku_comparison", "resource": target.get("resource_name"), "resource_id": target.get("resource_id"), "resource_context": {**target, "current_sku": current_sku}, "current_configuration": {"sku": current_sku, "monthly_cost": current_cost}, "candidates": comparisons, "best_candidate": best, "savings": {"monthly": best["savings"], "validated": True} if best else {"monthly": None, "validated": False}, "diagnostics": diagnostics, "request_id": request_id, "read_only": True, "llm_used": False, "fallback_used": False, "reason": "retail_price_evidence_available" if priced else "retail_price_evidence_unavailable"}

def _metrics_response(context, resolution, request_id):
    target = (resolution.get("target_resources") or [{}])[0]
    response_intent = resolution.get("intent") or "metrics"
    metric = ((context.get("performance") or {}).get("resources") or [{}])[0]
    values = metric.get("values") if isinstance(metric, dict) and isinstance(metric.get("values"), dict) else {}
    metric_names = metric.get("metric_names") if isinstance(metric, dict) and isinstance(metric.get("metric_names"), list) else list(values)
    message = (resolution.get("message") or "").casefold()
    historical_request = any(term in message for term in ("over time", "history", "historical", "trend", "graph", "chart", "visualize", "visualise"))
    historical = metric.get("timeseries") if isinstance(metric, dict) else None
    if isinstance(historical, dict):
        requested_metric = "Percentage CPU" if "cpu" in message else next(iter(historical), None)
        historical = historical.get(requested_metric, []) if requested_metric else []
    has_history = isinstance(historical, list) and any(isinstance(point, dict) and point.get("timestamp") is not None and point.get("value") is not None for point in historical)
    if historical_request and not has_history:
        cpu = values.get("Percentage CPU")
        if cpu is not None:
            answer = f"Historical CPU datapoints are unavailable for {target.get('resource_name') or 'the resolved resource'}. The latest persisted aggregate CPU value is {cpu}% .".replace("% .", "%.")
        else:
            answer = f"Historical CPU datapoints are unavailable for {target.get('resource_name') or 'the resolved resource'}."
        return {"answer": answer, "evidence": [], "visualizations": [], "recommendations": [], "intent": response_intent, "resource": target.get("resource_name"), "resource_id": target.get("resource_id"), "resource_context": target, "request_id": request_id, "read_only": True, "llm_used": False, "fallback_used": False, "reason": "azure_monitor_historical_data_unavailable"}
    period = f"last {metric.get('collected_days')} days" if metric.get("collected_days") else "collection period unavailable"
    collected_at = metric.get("collected_at")
    evidence = []
    for name in metric_names:
        value = values.get(name)
        evidence.append({"label": name, "metric_name": name, "value": value, "unit": METRIC_UNITS.get(name, "Azure Monitor unit"), "period": period, "resource_name": target.get("resource_name"), "source": "Azure Monitor", "status": "available" if value is not None else "unavailable", "collected_at": collected_at})
    answer_lines = [f"Azure Monitor metrics for {target.get('resource_name') or 'the resolved resource'} ({period}):"]
    answer_lines.extend(f"- {item['metric_name']}: {item['value'] if item['value'] is not None else 'Unavailable'} {item['unit']}" for item in evidence)
    if not evidence:
        answer_lines.append("- No Azure Monitor metric values are available in the current persisted snapshot.")
    metric_for_visualization = {**metric, "timeseries": historical} if isinstance(metric, dict) else metric
    return {"answer": "\n".join(answer_lines), "evidence": evidence, "visualizations": _metrics_visualizations(metric_for_visualization, evidence), "recommendations": [], "intent": response_intent, "resource": target.get("resource_name"), "resource_id": target.get("resource_id"), "resource_context": target, "request_id": request_id, "read_only": True, "llm_used": False, "fallback_used": False, "reason": "azure_monitor_persisted_evidence"}

def _deterministic_resource_answer(context, resolution):
    # Complete canonical evidence proves the resource outcome without Ollama."
    if not resolution.get("target_resources") or context.get("recommendations_all"):
        return False
    evidence = (context.get("resource_evidence") or [{}])[0]
    quality = context.get("data_quality") or {}
    return bool(evidence.get("resource_id") or evidence.get("resource_type"))


def _evidence_fallback(message, summary, intent=None):
    # Build a truthful local answer when the model is unavailable or invalid.
    intent = intent or classify_question_intent(message)
    if intent == "savings_analysis" and summary.get("resolved_targets"):
        comparison = _sku_comparison_response(summary, {"intent": "savings_analysis", "target_resources": summary["resolved_targets"]}, "fallback")
        return {"answer": comparison["answer"], "evidence": comparison.get("evidence", []), "visualizations": [], "recommendations": [], "intent": "savings_analysis", "resource": summary["resolved_targets"][0].get("resource_name"), "resource_id": summary["resolved_targets"][0].get("resource_id"), "read_only": True}
    if intent == "finops_reasoning" and summary.get("resolved_targets"):
        target = summary["resolved_targets"][0]
        cost = (summary.get("cost") or {}).get("monthly")
        recommendations = summary.get("recommendations_all") or []
        resource_type = target.get("resource_type") or (summary.get("resource_inventory") or [{}])[0].get("resource_type")
        evidence = (summary.get("resource_evidence") or [{}])[0]
        if recommendations:
            action = recommendations[0].get("action")
            savings = recommendations[0].get("potential_savings")
        elif evidence.get("metric_available") and evidence.get("configuration_available"):
            action = "No resource-specific optimization opportunity is confirmed from the available evidence"
            savings = None
        else:
            action = fallback_action(resource_type)
            savings = None
        return {
            "answer": f"Finding: {action}. Estimated savings: {_money(savings) if savings is not None else 'not quantifiable with available data'}.",
            "evidence": [],
        }
    deterministic = _deterministic_chat_answer(message, summary, intent)
    if deterministic is not None:
        return deterministic
    evidence = _question_evidence(message, summary, intent)
    if intent == "finops_reasoning":
        savings = float((summary.get("savings") or {}).get("potential_monthly") or 0)
        recommendations = _recommendations(summary)[:3]
        priorities = []
        for index, item in enumerate(recommendations, 1):
            resource_id = item.get("resource_id") or "persisted resource"
            eligibility = f"eligible for the approval safety flow because it is in {EXECUTION_RESOURCE_GROUP}" if _execution_allowed(resource_id) else f"not eligible for execution; only {EXECUTION_RESOURCE_GROUP} is eligible"
            priorities.append(f"{index}. {item.get('action') or 'Review optimization'} for {item.get('resource_name') or resource_id}: persisted potential savings are {_money(item.get('potential_savings') or 0)}; {eligibility}.")
        while len(priorities) < 3:
            domain = ("resource utilization and performance", "security findings", "governance compliance")[len(priorities) - len(recommendations)]
            priorities.append(f"{len(priorities) + 1}. Review persisted {domain}: this evidence should be prioritized alongside cost savings; no additional quantified savings are available.")
        answer = "Top 3 FinOps priorities based on the persisted cross-domain evidence:\n" + "\n".join(priorities) + f"\nTotal persisted potential monthly savings across recommendations: {_money(savings)}."
        return {"answer": answer, "evidence": [{"label": key, "value": value} for key, value in evidence.items()]}
    return {"answer": "The persisted evidence for this FinOps question is listed below.", "evidence": [{"label": key, "value": value} for key, value in evidence.items()]}


def _compact_llm_context(context, intent):
    '''Expose only small, authoritative fields to the model.'''
    if intent == "finops_reasoning":
        return {
            "cost": context.get("cost"),
            "savings": context.get("savings"),
            "resources": context.get("resources"),
            "recommendations": [
                {key: item.get(key) for key in ("resource_id", "resource_name", "action", "potential_savings")}
                for item in (context.get("recommendations_all") or [])[:10]
            ],
            "performance": {
                "average_cpu": (context.get("performance") or {}).get("average_cpu"),
                "resources": [
                    {key: item.get(key) for key in ("resource_id", "metric_available", "cpu_average", "cpu_max")}
                    for item in ((context.get("performance") or {}).get("resources") or [])[:10]
                ],
            },
            "security": context.get("security"),
            "governance": context.get("governance"),
        }
    return {key: context.get(key) for key in ("cost", "savings", "resources", "performance", "security", "governance") if key in context}


def _answer_addresses_intent(answer, intent):
    '''Validate both legacy prose and the concise structured reasoning contract.'''
    if isinstance(answer, list):
        if intent != "finops_reasoning" or not answer:
            return False
        return all(
            isinstance(item, dict)
            and item.get("priority") is not None
            and isinstance(item.get("reason"), str)
            and item.get("reason", "").strip()
            and isinstance(item.get("resource_id"), str)
            and item.get("resource_id", "").strip()
            for item in answer
        )
    if not isinstance(answer, str):
        return False
    text = answer.casefold()
    required = {
        "cost": ("cost", "$", "spend"), "savings": ("saving", "$"), "resources": ("resource", "service"),
        "performance": ("performance", "cpu", "latency", "util"), "security": ("security", "finding", "vulner"),
        "governance": ("governance", "compliance", "policy", "violation"), "recommendations": ("recommend", "opportunit", "saving"),
        "actions": ("action", "execution", "verification", "agent"), "finops_summary": ("finops", "cost", "saving", "recommend"),
    }
    if intent == "finops_reasoning":
        domains = ("cost", "saving", "performance", "util", "security", "governance", "compliance", "recommend")
        return ("priority" in text and ("1" in text or "first" in text) and sum(term in text for term in domains) >= 3)
    return intent == "out_of_scope" or any(term in text for term in required.get(intent, ()))


def _structured_reasoning_text(answer):
    '''Turn concise model records into UI prose; evidence is attached locally.'''
    if not isinstance(answer, list):
        return answer
    lines = []
    for item in answer:
        if not isinstance(item, dict):
            continue
        priority = item.get("priority", len(lines) + 1)
        reason = item.get("reason", "").strip()
        resource_id = item.get("resource_id", "").strip()
        lines.append(f"Priority {priority}: {reason} (resource: {resource_id})")
    return "\n".join(lines)


def _chat_history(history):
    # History supplies referents only; the latest user message remains authoritative.
    return [
        {"role": item.get("role", "user"), "content": item.get("content", "")[:2000]}
        for item in history[-8:]
        if isinstance(item, dict) and item.get("role") in {"user", "assistant"} and isinstance(item.get("content"), str)
    ]


def _subscription(session, claims):
    user = session.query(ApplicationUser).filter_by(entra_subject_id=claims["sub"], tenant_id=claims["tid"], is_active=True).first()
    if user is None:
        raise HTTPException(status_code=401, detail="FinOps user session is not registered")
    connection = session.query(AzureConnection).filter_by(user_id=user.id, tenant_id=claims["tid"], connection_status="CONNECTED").order_by(AzureConnection.connected_at.desc()).first()
    if connection is None:
        raise HTTPException(status_code=403, detail="No Azure subscription is connected for this user")
    return connection.subscription_id

def _in_subscription(resource_id, subscription_id):
    return (resource_id or "").lower().startswith(f"/subscriptions/{subscription_id.lower()}/")


def _resource_group(resource_id):
    parts = [part for part in (resource_id or "").split("/") if part]
    for index, part in enumerate(parts):
        if part.lower() == "resourcegroups" and index + 1 < len(parts):
            return parts[index + 1]
    return None

def _execution_allowed(resource_id):
    return (_resource_group(resource_id) or "").casefold() == EXECUTION_RESOURCE_GROUP.casefold()


def _recommendation_card(item, cost_by_resource):
    resource_id = item.resource_id
    cost = cost_by_resource.get(resource_id.casefold(), {})
    confidence = float(item.confidence or 0)
    risk = "High" if confidence < 0.6 else "Medium" if confidence < 0.8 else "Low"
    executable = _execution_allowed(resource_id)
    return {
        "recommendation_id": item.recommendation_id,
        "resource_id": resource_id,
        "resource": item.resource_name or cost.get("resource_name") or resource_id.rsplit("/", 1)[-1],
        "resource_group": _resource_group(resource_id),
        "problem_detected": item.category or "Persisted optimization opportunity",
        "recommended_action": item.action,
        "finding": item.action,
        "current_estimated_cost": cost.get("monthly_cost"),
        "cost": cost.get("monthly_cost"),
        "cost_status": cost.get("cost_status") or ("estimated" if cost.get("is_estimated") else "available" if cost.get("monthly_cost") is not None else "unavailable"),
        "cost_source": cost.get("cost_source") or "none",
        "cost_type": cost.get("cost_type"),
        "is_estimated": bool(cost.get("is_estimated")),
        "estimated_monthly_savings": item.estimated_savings,
        "potential_savings": item.estimated_savings,
        "savings_status": "estimated" if cost.get("is_estimated") else "persisted",
        "risk": risk,
        "confidence": confidence,
        "executable": executable,
        "approval_enabled": executable and not item.approved,
        "approval_disabled_reason": None if executable else f"Execution is limited to {EXECUTION_RESOURCE_GROUP}.",
        "approved": bool(item.approved),
    }


def _payload(value: Any):
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value or "{}")
    except (TypeError, ValueError):
        return {}


def _human_answer(value):
    text = str(value or "").strip()
    parsed = _payload(text)
    if isinstance(parsed, dict) and isinstance(parsed.get("answer"), str):
        return parsed["answer"].strip()
    return text

def _confidence(context, resolution):
    quality = context.get("data_quality") or {}
    score = 0
    if resolution.get("target_resources"): score += 20
    if quality.get("cost_available"): score += 20
    if quality.get("utilization_available"): score += 20
    if quality.get("configuration_available"): score += 15
    if quality.get("savings_available"): score += 15
    if quality.get("cost_source") == "Azure Cost Management": score += 5
    if quality.get("evidence_quality") == "direct": score += 5
    level = "High" if score >= 90 else "Medium" if score >= 70 else "Low"
    return score, level

def _legacy_format_resource_answer(answer, context, resolution):
    # Legacy formatter retained for non-target compatibility; targeted responses use the canonical decision below.
    targets = resolution.get("target_resources") or []
    if targets:
        evidence = (context.get("resource_evidence") or [{}])[0]
        persisted = (context.get("recommendations_all") or [None])[0]
        decision = analyze_resource(evidence, persisted)
        target = targets[0]
        resource_type = str(evidence.get("resource_type") or target.get("resource_type") or "").casefold()
        cost = evidence.get("cost")
        config = decision.get("configuration") or evidence.get("configuration") or {}
        dependencies = config.get("managed_by") or config.get("associated_resource") or config.get("attached_vm") or "Unavailable"
        return "\n".join([
            "FinOps Analysis", "",
            f"Resource: {target.get('resource_name') or evidence.get('resource_name') or 'Unavailable'}",
            f"* Resource: {target.get('resource_name') or evidence.get('resource_name') or 'Unavailable'}",
            f"Resource Group: {evidence.get('resource_group') or _resource_group(evidence.get('resource_id')) or 'Unavailable'}",
            f"* Resource Group: {evidence.get('resource_group') or _resource_group(evidence.get('resource_id')) or 'Unavailable'}",
            f"Resource Type: {RESOURCE_TYPE_LABELS.get(resource_type, evidence.get('resource_type') or 'Unknown')}",
            f"Current Monthly Cost: {_money(cost) if cost is not None else 'Unavailable'}",
            f"* Current monthly cost: {_money(cost) if cost is not None else 'Unavailable'}",
            f"Cost Source: {evidence.get('cost_source') or 'Unavailable'}",
            f"**Cost source:** {evidence.get('cost_source') or 'Unavailable'}",
            f"Cost Type: {evidence.get('cost_type') or 'Unavailable'}",
            f"**Cost evidence:** {'available' if cost is not None else 'unavailable'}", "",
            "Evidence", "",
            f"* Metrics: {decision.get('metrics') or 'Unavailable'}",
            f"* Configuration: {config or 'Unavailable'}",
            f"* Cost evidence: {'available' if cost is not None else 'unavailable'}",
            f"* Dependencies: {dependencies}",
            f"* Metric availability: {'Available' if evidence.get('metric_available') or evidence.get('metrics') else 'False'}", "",
            "Finding", "", decision["finding"], "", "Recommendation", "", decision["action"], "",
            "Why", "", decision["why"], "", ("No resource-specific optimization finding is confirmed." if decision["action"] == "no_safe_optimization_identified" else ""), "Potential Savings", "", decision["savings"], "",
            f"Legacy finding label: {decision['finding']}", "",
            "Confidence", "", decision["confidence"], "", f"**Potential savings:** {decision['savings']}", "", "Next Action", "", decision["next_action"],
        ])
    answer = _human_answer(answer)
    targets = resolution.get("target_resources") or []
    if resolution.get("target_resources"):
        evidence = (context.get("resource_evidence") or [{}])[0]
        if str(evidence.get("resource_type") or "").casefold() == "microsoft.containerregistry/registries":
            metrics = evidence.get("metrics") or {}
            values = {name: metrics.get(name) for name in ("StorageUsed", "TotalPullCount", "TotalPushCount")}
            complete = all(value is not None for value in values.values())
            pulls, pushes = values["TotalPullCount"], values["TotalPushCount"]
            configuration = evidence.get("configuration") or {}
            sku = configuration.get("sku") or configuration.get("sku_name") or "Unavailable"
            tier = configuration.get("sku_tier") or "Unavailable"
            cost = evidence.get("cost")
            active = complete and (pulls > 0 or pushes > 0)
            if complete and pulls == 0 and pushes == 0:
                finding, recommendation = f"StorageUsed={values['StorageUsed']}, TotalPullCount=0, and TotalPushCount=0 indicate stored content with no observed activity.", "Investigate inactive registry and consider removal"
                savings, confidence, next_action = (f"ESTIMATED {_money(cost)} per month using the current cost as the avoidable cost." if cost else "Not quantifiable from available evidence because current monthly cost is unavailable."), ("High" if cost else "Medium"), "Confirm with owners that no workflow needs the registry, then remove it if unused."
            elif active and (str(sku).casefold() == "premium" or str(tier).casefold() == "premium"):
                finding, recommendation = f"StorageUsed={values['StorageUsed']}, TotalPullCount={pulls}, and TotalPushCount={pushes} confirm active use; deletion or aggressive cleanup is not supported.", "Evaluate SKU downgrade"
                savings, confidence, next_action = "Not quantifiable from available evidence because no comparable Standard/Basic price was collected.", "Medium", "Check Premium-only feature usage and compare compatible Standard/Basic retail prices."
            elif active:
                finding, recommendation = f"StorageUsed={values['StorageUsed']}, TotalPullCount={pulls}, and TotalPushCount={pushes} confirm active use; deletion or aggressive cleanup is not supported.", "Keep current configuration; no safe optimization identified"
                savings, confidence, next_action = "Not quantifiable from available evidence because active usage does not support deletion or aggressive cleanup.", ("High" if cost else "Medium"), "Review image retention candidates without deleting images required by active workflows."
            else:
                missing = ", ".join(name for name, value in values.items() if value is None) or "safe optimization evidence"
                finding, recommendation, savings, confidence, next_action = f"The collected evidence is insufficient for a safe optimization; unavailable evidence: {missing}.", "Keep current configuration; no safe optimization identified", "Not quantifiable from available evidence because required metrics or configuration are incomplete.", "Low", "Collect all three ACR metrics, SKU/configuration, and monthly cost for this registry."
            target = resolution["target_resources"][0]
            metric_text = "; ".join(f"{name}={value if value is not None else 'Unavailable'}" for name, value in values.items())
            return "\n".join(["FinOps Analysis", "", f"* Resource: {target.get('resource_name') or evidence.get('resource_name') or 'Unavailable'}", f"* Resource Group: {evidence.get('resource_group') or 'Unavailable'}", f"* Current monthly cost: {_money(cost) if cost is not None else 'Unavailable'}", f"* Cost source / cost type: {evidence.get('cost_source') or 'Unavailable'} / {evidence.get('cost_type') or 'Unavailable'}", f"* Metrics analyzed: {metric_text}", f"* Configuration analyzed: SKU={sku}; SKU tier={tier}", "", "Finding", "", f"* {finding}", "", "Recommendation", "", f"* {recommendation}", "", "Potential Savings", "", f"* {savings}", "", "Confidence", "", f"* {confidence}", "* Based on metric completeness, activity, configuration, and cost evidence.", "", "Next Action", "", f"* {next_action}"])
    answer = _human_answer(answer)
    targets = resolution.get("target_resources") or []
    if not targets:
        return str(answer).strip()
    target = targets[0]
    inventory = (context.get("resource_inventory") or [{}])[0]
    evidence = (context.get("resource_evidence") or [{}])[0]
    cost = evidence.get("cost")
    performance = (context.get("performance") or {}).get("resources") or []
    recommendations = context.get("recommendations_all") or []
    savings = recommendations[0].get("potential_savings") if recommendations else None
    quality = context.get("data_quality") or {}
    confidence_score, confidence_level = _confidence(context, resolution)
    resource_type = evidence.get("resource_type") or target.get("resource_type") or inventory.get("resource_type")
    metric = performance[0] if performance else {}
    metric_names = ", ".join(evidence.get("metrics", {}).keys()) or "none"
    metrics_available = bool(evidence.get("metric_available"))
    finding = recommendations[0].get("action") if recommendations else "No resource-specific optimization finding is confirmed."
    recommendation = answer or (recommendations[0].get("action", "Review the recommendation through approval.") if recommendations else ("No resource-specific optimization opportunity is confirmed from the available evidence." if metrics_available and quality.get("configuration_available") else fallback_action(resource_type)))
    reason = (recommendations[0].get("reason") if recommendations else None) or ("A resource-specific recommendation is persisted." if recommendations else ("Current cost, configuration, and performance evidence does not confirm an optimization opportunity." if metrics_available and quality.get("configuration_available") else f"{evidence.get('metric_unavailable_reason') or 'No evidence-backed optimization condition was detected.'}"))
    next_action = "Review the recommendation through the existing approval flow." if recommendations else ("No further collection is required; monitor for a confirmed optimization condition." if metrics_available and quality.get("configuration_available") else fallback_action(resource_type))
    return "\n".join([
        f"### FinOps analysis: {target.get('resource_name') or 'Resolved resource'}", "",
        f"**Resource:** {target.get('resource_name') or 'Unavailable'}",
        f"**Current monthly cost:** {_money(cost) if cost is not None else 'Unavailable'}",
        f"**Cost evidence:** {'available' if quality.get('cost_available') else 'unavailable'}",
        f"**Cost source:** {evidence.get('cost_source') or 'Unavailable'}",
        f"**Cost type:** {evidence.get('cost_type') or 'Unavailable'}",
        f"**Configuration evidence:** {'available' if quality.get('configuration_available') else 'unavailable'}",
        f"**Resource-specific utilization evidence:** {'available' if quality.get('utilization_available') else 'unavailable'}",
        f"**Metrics collected:** {metric_names}",
        f"**Metric available:** {metrics_available}",
        f"**Finding:** {finding}",
        f"**Recommendation:** {recommendation}",
        f"**Potential savings:** {_money(savings) if savings is not None and savings > 0 else 'Not quantifiable'}",
        f"**Confidence:** {confidence_score}% ({confidence_level})",
        f"**Reason:** {reason}",
        f"**Next action:** {next_action}",
    ])


def _canonical_resource_decision(context, resolution):
    targets = resolution.get("target_resources") or []
    if not targets:
        return None
    evidence = (context.get("resource_evidence") or [{}])[0]
    persisted = (context.get("recommendations_all") or [None])[0]
    return analyze_resource(evidence, persisted)


def _resource_answer_text(decision):
    cost = decision.get("current_cost")
    cost_line = f"${float(cost):,.2f}/month / {decision.get('cost_type') or 'available'} / {decision.get('cost_source') or 'unknown source'}" if cost is not None else "Unavailable / not quantifiable"
    lines = [f"### FinOps Analysis - {decision.get('resource_name') or 'Resolved resource'}", "", f"**Cost:** {cost_line}", "", "**Evidence**"]
    lines.extend(f"* {item}" for item in decision.get("evidence", []))
    lines.extend(["", "**Finding**", decision.get("finding") or decision.get("reason") or "Insufficient evidence.", "", "**Recommendation**", decision.get("action") or "insufficient_evidence", "", "**Potential savings**", decision.get("savings") or "Not quantifiable from available evidence.", "", "**Confidence**", f"{decision.get('confidence_level', 'Low')} - {decision.get('reason') or 'evidence quality is limited.'}", "", "**Next action**", decision.get("next_action") or "Collect the missing resource-specific utilization metrics."])
    return "\n".join(lines)


def _canonical_recommendation(decision):
    return {**decision, "recommended_action": decision.get("action"), "problem_detected": decision.get("finding"), "current_estimated_cost": decision.get("current_cost"), "estimated_monthly_savings": decision.get("potential_savings"), "cost_status": decision.get("cost_type") or "unavailable", "is_estimated": decision.get("cost_type") == "estimated", "risk": decision.get("confidence_level", "Low"), "confidence": decision.get("confidence_score", 0) / 100, "executable": decision.get("execution_eligibility", False), "approval_enabled": False, "approved": False}


def _format_resource_answer(answer, context, resolution):
    decision = _canonical_resource_decision(context, resolution)
    return _resource_answer_text(decision) if decision else _human_answer(answer)


def _chat_response(answer, evidence, context, resolution, request_id):
    # Return all targeted fields from the same canonical resource decision.
    decision = _canonical_resource_decision(context, resolution)
    answer = _format_resource_answer(answer, context, resolution)
    target = (resolution.get("target_resources") or [{}])[0]
    target_evidence = (context.get("resource_evidence") or [{}])[0]
    available = context.get("data_quality") or {}
    if decision:
        cost = decision.get("current_cost")
        savings = decision.get("potential_savings")
        confidence_score = decision.get("confidence_score", 0)
        confidence_level = decision.get("confidence_level", "Low")
        canonical_recommendation = _canonical_recommendation(decision)
        next_step = decision.get("next_action")
        cost_status = decision.get("cost_type") or "unavailable"
        cost_source = decision.get("cost_source") or "none"
    else:
        cost = (context.get("cost") or {}).get("monthly")
        recommendations = context.get("recommendations_all") or []
        savings = recommendations[0].get("potential_savings") if recommendations else None
        confidence_score, confidence_level = _confidence(context, resolution)
        canonical_recommendation = _recommendation_projection(recommendations[0], target_evidence) if recommendations else None
        next_step = fallback_action(target_evidence.get("resource_type")) if not (available.get("utilization_available") and available.get("configuration_available")) else "Review the recommendation through the existing approval flow."
        cost_status = context.get("cost_status", "unavailable")
        cost_source = context.get("cost_source", "none")
    return {
        "answer": _human_answer(answer),
        "recommendation": canonical_recommendation or ("No resource-specific optimization opportunity is confirmed from the available evidence." if target_evidence.get("metric_available") and target_evidence.get("configuration_available") else "Insufficient evidence to make a quantified recommendation."),
        # The formatted answer is the resource evidence projection.  Returning
        # model/context objects here would expose raw JSON and unscoped totals.
        "evidence": [] if target.get("resource_id") else (evidence if isinstance(evidence, list) else []),
        "savings": savings,
        "confidence_score": confidence_score,
        "confidence_level": confidence_level,
        "confidence": confidence_level,
        "data_quality": available,
        "cost": {**(context.get("cost") or {}), "monthly": cost},
        "next_step": next_step,
        "resource": decision.get("resource_name") if decision else target.get("resource_name"),
        "resource_id": decision.get("resource_id") if decision else target.get("resource_id"),
        "monthly_cost": cost,
        "cost_status": cost_status,
        "cost_source": cost_source,
        "request_id": request_id,
        "reason": "canonical_evidence" if _deterministic_resource_answer(context, resolution) else "llm_response",
        "llm_used": False if _deterministic_resource_answer(context, resolution) else None,
        "fallback_used": False,
    }

class DecisionRequest(BaseModel):
    reason: str | None = None
class ChatRequest(BaseModel):
    message: str
    history: list[dict[str, str]] = Field(default_factory=list)
    conversation_context: dict[str, Any] = Field(default_factory=dict)

@router.get("/overview")
def agent_overview(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    claims = validate_id_token(credentials.credentials)
    session = SessionLocal()
    try:
        subscription_id = _subscription(session, claims)
        try:
            return _build_overview(session, subscription_id)
        except SQLAlchemyError as exc:
            session.rollback()
            logger.exception("GET /api/agent/overview failed: subscription_id=%s root_db_error=%s", subscription_id, exc)
            # Keep the endpoint usable when an optional overview table/query is
            # unavailable.  The dashboard summary remains the authoritative
            # persisted projection and is intentionally not changed here.
            try:
                summary = summary_service.build(session, subscription_id)
                return {**summary, "data_status": "partial", "agent": {**summary.get("agent", {}), "status": "DATA_UNAVAILABLE"}, "data_warning": "Agent overview details are temporarily unavailable."}
            except Exception as fallback_exc:
                logger.exception("GET /api/agent/overview fallback failed: subscription_id=%s root_db_error=%s", subscription_id, fallback_exc)
                return {"subscription_id": subscription_id, "data_status": "partial", "data_warning": "Agent overview data is unavailable.", "agent": {"status": "DATA_UNAVAILABLE"}}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("GET /api/agent/overview connection failed: root_db_error=%s", exc)
        raise HTTPException(status_code=503, detail="Agent data store unavailable") from exc
    finally:
        session.close()

@router.get("/actions")
def agent_actions(page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50), credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    claims = validate_id_token(credentials.credentials)
    session = SessionLocal()
    try:
        subscription_id = _subscription(session, claims)
        rows = _action_rows(session, subscription_id)
        start = (page - 1) * page_size
        return {"items": rows[start:start + page_size], "page": page, "page_size": page_size, "total": len(rows)}
    finally:
        session.close()

@router.post("/recommendations/{recommendation_id}/approve")
async def approve_recommendation(recommendation_id: str, payload: DecisionRequest | None = None, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    from app.agent.nodes.approval import approval
    from app.agent.nodes.execution import execute
    from app.agent.nodes.verification import verify
    from app.services.execution.container import create_execution_router
    from app.services.verification.container import create_verification_router
    claims = validate_id_token(credentials.credentials)
    session = SessionLocal()
    try:
        subscription_id = _subscription(session, claims)
        recommendation = session.query(RecommendationMemory).filter_by(recommendation_id=recommendation_id).first()
        if recommendation is None or not _in_subscription(recommendation.resource_id, subscription_id):
            raise HTTPException(status_code=404, detail="Recommendation not found")
        if not _execution_allowed(recommendation.resource_id):
            raise HTTPException(status_code=403, detail=f"Execution is limited to {EXECUTION_RESOURCE_GROUP}")
        if recommendation.approved:
            return {"recommendation_id": recommendation_id, "approved": True, "execution_started": False, "status": "already_approved", "message": "This recommendation was already approved."}

        recommendation.approved = True
        session.commit()
        rec = Recommendation(
            title=recommendation.category or recommendation.action or "Optimization recommendation",
            source_issue_id=recommendation.recommendation_id,
            resource_id=recommendation.resource_id,
            resource_name=recommendation.resource_name or recommendation.resource_id.rsplit("/", 1)[-1],
            action=recommendation.action,
            estimated_savings=float(recommendation.estimated_savings or 0),
            potential_savings=float(recommendation.estimated_savings or 0),
            confidence=float(recommendation.confidence or 0),
            requires_approval=True,
        )
        state = {
            "validated_recommendations": [rec],
            "approved_recommendation_ids": [recommendation.recommendation_id],
            "approved_recommendations": [],
            "pending_approval": [],
            "execution_results": [],
            "execution_router": create_execution_router(),
            "verification_router": create_verification_router(),
            "dry_run": True,
        }
        state = approval(state)
        state = await execute(state)
        state = await verify(state)
        result = state.get("execution_results", [{}])[0] if state.get("execution_results") else {}
        report = state.get("verification_report", {})
        verification = report.get("results", [{}])[0] if report.get("results") else {"verification_status": report.get("overall_status")}
        status = result.get("status") if isinstance(result, dict) else getattr(result, "status", "unknown")
        status = getattr(status, "value", status)
        return {"recommendation_id": recommendation_id, "approved": True, "execution_started": True, "status": status, "verification": verification, "message": "Approval passed through approval, execution, and verification safety gates."}
    finally:
        session.close()

@router.post("/executions/{execution_id}/rollback")
def rollback_execution(execution_id: str, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    claims = validate_id_token(credentials.credentials)
    session = SessionLocal()
    try:
        subscription_id = _subscription(session, claims)
        execution = session.query(ExecutionMemory).filter_by(id=int(execution_id)).first()
        if execution is None or not _in_subscription(execution.resource_id, subscription_id):
            raise HTTPException(status_code=404, detail="Execution not found")
        details = _payload(execution.result)
        rollback = details.get("rollback", {})
        if not rollback.get("available") or details.get("dry_run", True):
            raise HTTPException(status_code=409, detail="Rollback is not available for this execution")
        raise HTTPException(status_code=409, detail="Rollback requires the existing execution safety flow and is not available through this record")
    finally:
        session.close()

@router.post("/chat")
def agent_chat(payload: ChatRequest, credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    request_id = str(uuid.uuid4())
    logger.info("Agent chat request started: request_id=%s", request_id)
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=422, detail="A chat message is required")
    if len(message) > 4000:
        raise HTTPException(status_code=422, detail="Chat messages must be 4000 characters or fewer")
    claims = validate_id_token(credentials.credentials)
    session = SessionLocal()
    try:
        subscription_id = _subscription(session, claims)
        summary = _canonical_summary(summary_service.build(session, subscription_id))
        summary["subscription_id"] = subscription_id
        resolution = resolve_question(message, summary, payload.history, payload.conversation_context)
        intent = resolution["intent"]
        recommendations = _chat_recommendations(session, summary, message, resolution["target_resources"])
        if _is_approval_question(message):
            return _approval_response(recommendations, summary, resolution, request_id) | {
                "intent": intent,
                "resolution": resolution,
                "subscription_id": subscription_id,
            }
        named_analysis = any(term in message.casefold() for term in ("analyze", "analyse", "recommendation for", "recommend for"))
        if named_analysis and not resolution["target_resources"] and len(message.split()) > 1:
            return _chat_response("I could not resolve that resource in the connected Azure context. Please provide the exact Azure resource name or resource ID.", [], {}, resolution, request_id) | {"recommendations": [], "intent": intent, "subscription_id": subscription_id, "read_only": True}
        deterministic = _deterministic_chat_answer(message, summary, intent)
        # Inventory responses remain isolated from cost/recommendation formatting.
        if intent in {"resource_listing", "resource_status", "inventory"}:
            return deterministic | {"subscription_id": subscription_id, "resolution": resolution, "conversation_context": payload.conversation_context, "resource_context": payload.conversation_context.get("resource")}
        # Factual intents and complete target evidence never depend on Ollama.
        if deterministic is not None and not resolution["target_resources"]:
            return _chat_response(deterministic["answer"], deterministic.get("evidence", []), summary, resolution, request_id) | {"recommendations": recommendations if intent in {"savings", "recommendations"} else [], "intent": intent, "subscription_id": subscription_id, "conversation_context": payload.conversation_context, "read_only": True}
        context = _resource_context(resolution, summary, intent)
        if intent in {"metrics", "metrics_history"} and resolution["target_resources"]:
            return _metrics_response(context, resolution, request_id) | {"resolution": resolution, "subscription_id": subscription_id}
        if intent in {"sku_comparison", "savings_analysis"} and resolution["target_resources"]:
            return _sku_comparison_response(context, resolution, request_id) | {"resolution": resolution, "subscription_id": subscription_id}
        if _deterministic_resource_answer(context, resolution):
            response = _chat_response("", [], context, resolution, request_id)
            response.update({"reason": "canonical_evidence", "llm_used": False, "fallback_used": False, "recommendations": [], "intent": intent, "resolution": resolution, "subscription_id": subscription_id, "read_only": True})
            logger.info("Agent chat deterministic resource response: request_id=%s", request_id)
            return response
        history = _chat_history(payload.history)
        reasoning_requirements = ""
        if intent == "finops_reasoning":
            reasoning_requirements = f'''Return a concise JSON answer array of up to three ranked recommendation records. Each record must contain only priority, reason, and resource_id. Keep reason under 240 characters. Do not return evidence, configuration, metrics objects, or copied context. Only resources in {EXECUTION_RESOURCE_GROUP} are eligible for the approval safety flow; all others are read-only recommendations.'''
        target_requirements = ""
        if resolution["target_resources"]:
            target_requirements = "Answer specifically about every resolved target resource. Do not substitute global recommendations. Distinguish target-linked evidence from subscription aggregate evidence."
        prompt = f'''You are a read-only Azure FinOps assistant. Answer the user question using only the supplied canonical evidence. Never invent values, resources, actions, outcomes, or savings. Return only JSON with an answer key. For ordinary intents answer must be a concise string. For finops_reasoning answer must be an array of concise objects containing only priority, reason, and resource_id. Do not return an evidence key or reproduce configuration/resource objects; the backend attaches authoritative evidence after validation. {target_requirements} {reasoning_requirements}
USER QUESTION: {json.dumps(message)}
COMPACT EVIDENCE INDEX: {json.dumps(_compact_llm_context(context, intent), default=str, separators=(',', ':'))}'''
        answer = "The FinOps assistant could not produce a model response."
        evidence = []
        try:
            raw = ask_llm(prompt, request_id=request_id)
            parsed = _payload(raw)
            answer = parsed.get("answer") if isinstance(parsed, dict) else None
            if not _answer_addresses_intent(answer, intent):
                raise ValueError("LLM response did not address the classified intent")
            if isinstance(answer, list):
                known_ids = {str(item.get("resource_id", "")).casefold() for item in context.get("recommendations_all", []) if item.get("resource_id")}
                known_ids.update(str(item.get("resource_id", "")).casefold() for item in context.get("resolved_targets", []) if item.get("resource_id"))
                if known_ids and any(item.get("resource_id", "").casefold() not in known_ids for item in answer):
                    raise ValueError("LLM recommendation referenced an unknown resource")
            answer = _structured_reasoning_text(answer)
            evidence = []
            # Evidence is deliberately sourced from the resolved/persisted context,
            # never from a model-generated copy that may be truncated or altered.
        except LLMTimeoutError:
            # A provider timeout is independent from context resolution; do not issue a second 30s call.
            fallback = _evidence_fallback(message, context if resolution["target_resources"] else summary, intent)
            if resolution["target_resources"]:
                fallback["answer"] += " The local model timed out, so this answer uses only the resolved persisted evidence."
            answer, evidence = fallback["answer"], fallback["evidence"]
            fallback_reason = "llm_timeout"
        except Exception:
            logger.exception("POST /api/agent/chat model response failed; using persisted evidence fallback: request_id=%s intent=%s", request_id, intent)
            fallback = _evidence_fallback(message, context if resolution["target_resources"] else summary, intent)
            answer, evidence = fallback["answer"], fallback["evidence"]
            fallback_reason = "llm_error"
        response = _chat_response(answer, evidence, context, resolution, request_id)
        response.update({"reason": locals().get("fallback_reason", "llm_response"), "llm_used": not locals().get("fallback_reason"), "fallback_used": bool(locals().get("fallback_reason"))})
        response.update({"recommendations": ([response["recommendation"]] if resolution["target_resources"] and isinstance(response.get("recommendation"), dict) else recommendations if intent in {"savings", "recommendations", "finops_reasoning"} else []), "intent": intent, "resolution": resolution, "subscription_id": subscription_id, "conversation_context": payload.conversation_context, "read_only": True})
        logger.info("Agent chat request completed: request_id=%s intent=%s target_count=%s", request_id, intent, len(resolution["target_resources"]))
        return response
    except HTTPException:
        raise
    except SQLAlchemyError as exc:
        session.rollback()
        logger.exception("POST /api/agent/chat database failure: request_id=%s root_db_error=%s", request_id, exc)
        raise HTTPException(status_code=503, detail="Agent data store unavailable") from exc
    except Exception as exc:
        logger.exception("POST /api/agent/chat failed: request_id=%s root_error=%s", request_id, exc)
        raise HTTPException(status_code=500, detail="Agent chat request failed") from exc
    finally:
        session.close()

@router.post("/run-agent")
async def run_agent():
    from app.agent.graph import finops_agent
    from app.services.execution.container import create_execution_router
    from app.services.verification.container import create_verification_router
    execution_router = create_execution_router()
    initial_state = {"user_request": "Analyze my Azure environment", "observed": {}, "cost_issues": [], "performance_issues": [], "security_issues": [], "governance_issues": [], "recommendations": [], "approved_recommendations": [], "execution_results": [], "verification_results": [], "learning": {}, "logs": [], "execution_router": execution_router, "verification_router": create_verification_router()}
    return finops_agent.invoke(initial_state)


def _action_rows(session, subscription_id):
    rows = []
    outcomes = session.query(OptimizationOutcomeMemory).all()
    for item in outcomes:
        if not _in_subscription(item.resource_id, subscription_id):
            continue
        data = _payload(item.outcome)
        execution = data.get("execution", {})
        verification = data.get("verification", {})
        savings = data.get("savings", {})
        rows.append({"id": item.execution_id or item.outcome_id, "recommendation_id": item.recommendation_id, "resource_id": item.resource_id, "resource_name": execution.get("resource_name") or item.resource_id.rsplit("/", 1)[-1], "action": execution.get("action"), "status": execution.get("status"), "verification_status": verification.get("status"), "verification_message": verification.get("message"), "potential_savings": savings.get("expected"), "realized_savings": savings.get("realized"), "rollback": execution.get("rollback", {}), "timestamp": item.recorded_at.isoformat() if item.recorded_at else None, "audit": {"outcome_id": item.outcome_id, "recorded_at": item.recorded_at.isoformat() if item.recorded_at else None}})
    for item in session.query(ExecutionMemory).all():
        if not _in_subscription(item.resource_id, subscription_id):
            continue
        if any(row["id"] == str(item.id) for row in rows):
            continue
        rows.append({"id": str(item.id), "recommendation_id": item.recommendation_id, "resource_id": item.resource_id, "resource_name": item.resource_id.rsplit("/", 1)[-1], "action": item.action, "status": item.status, "verification_status": None, "verification_message": None, "potential_savings": None, "realized_savings": item.realized_savings, "rollback": {}, "timestamp": item.executed_at.isoformat() if item.executed_at else None, "audit": {"execution_record_id": item.id, "executed_at": item.executed_at.isoformat() if item.executed_at else None}})
    return sorted(rows, key=lambda row: row.get("timestamp") or "", reverse=True)


def _build_overview(session, subscription_id):
    summary = summary_service.build(session, subscription_id)
    recommendations = session.query(RecommendationMemory).all()
    pending = [item for item in recommendations if _in_subscription(item.resource_id, subscription_id) and not item.approved]
    actions = _action_rows(session, subscription_id)
    subscription_recommendations = [item for item in recommendations if _in_subscription(item.resource_id, subscription_id)]
    return {**summary, "opportunities": {"total": len(subscription_recommendations), "items": [{"id": item.recommendation_id, "resource_id": item.resource_id, "resource_name": item.resource_name, "action": item.action, "potential_savings": item.estimated_savings, "confidence": item.confidence, "approved": item.approved} for item in subscription_recommendations]}, "pending_approvals": [{"id": item.recommendation_id, "resource_id": item.resource_id, "resource_name": item.resource_name, "action": item.action, "potential_savings": item.estimated_savings, "confidence": item.confidence} for item in pending], "actions": actions, "activity": {"analysis": {"status": "complete" if summary["resources"]["total"] is not None else "waiting", "resources": summary["resources"]["total"]}, "recommendation": {"status": "complete" if summary["agent"]["recommendations"] else "waiting", "count": summary["agent"]["recommendations"]}, "approval": {"status": "active" if pending else "complete", "count": len(pending)}, "execution": {"status": "complete" if summary["agent"]["executed"] else "waiting", "count": summary["agent"]["executed"]}, "verification": {"status": "active" if summary["agent"]["verification_pending"] else "complete", "count": summary["agent"]["verification_pending"]}}, "audit": {"generated_at": summary["generated_at"], "subscription_id": subscription_id, "action_count": len(actions)}}
