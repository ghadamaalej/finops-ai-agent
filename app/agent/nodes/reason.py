"""Build safe FinOps recommendations from authoritative analyzer evidence."""

import json
from typing import Any

from app.models.recommendation import Recommendation
from app.services.llm_service import ask_llm


def _float(value: Any, default: float = 0.0) -> float:
    try:
        return default if value is None else float(value)
    except (TypeError, ValueError):
        return default


def _issue(value: Any) -> dict:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value if isinstance(value, dict) else {}


def _evidence(issue: dict) -> dict:
    evidence = issue.get("evidence", {})
    return evidence if isinstance(evidence, dict) else {}


def _cost(issue: dict) -> float:
    return _float(issue.get("current_monthly_cost", issue.get("monthly_cost", 0)))


def _savings(issue: dict) -> float:
    return _float(issue.get("estimated_monthly_savings", issue.get("estimated_savings", 0)))


def _source(issue: dict):
    return issue.get("cost_source") or _evidence(issue).get("cost_source")


def _type(issue: dict):
    return issue.get("cost_type") or _evidence(issue).get("cost_type")


def _estimated(issue: dict) -> bool:
    value = issue.get("is_estimated")
    return bool(_evidence(issue).get("is_estimated", False) if value is None else value)


def _available(issue: dict) -> bool:
    value = issue.get("cost_data_available")
    return bool(_evidence(issue).get("cost_data_available", False) if value is None else value)


def _actionable(issues: list[dict]) -> list[dict]:
    """Keep one cost-backed finding per resource, preferring CPU evidence."""
    output: dict[str, dict] = {}
    for issue in issues:
        if not issue.get("resource_id") or _cost(issue) <= 0 or _savings(issue) <= 0:
            continue
        if not (_available(issue) or (_estimated(issue) and _source(issue))):
            continue
        key = str(issue["resource_id"]).lower()
        current = output.get(key)
        if current is None or (_evidence(issue).get("cpu_average") is not None and _evidence(current).get("cpu_average") is None):
            output[key] = issue
    return list(output.values())


def _prompt(issue: dict) -> str:
    evidence = _evidence(issue)
    context = {
        "issue_type": issue.get("issue_type"),
        "resource_type": issue.get("resource_type"),
        "severity": issue.get("severity", "Medium"),
        "has_cpu_evidence": evidence.get("cpu_average") is not None,
        "has_peak_cpu_evidence": evidence.get("cpu_max") is not None,
    }
    return f'''You write concise Azure FinOps recommendation wording.
Return only JSON with: title, action, priority, implementation_risk,
execution_plan, explanation. execution_plan must be an array of strings.
Do not state or infer numbers, costs, savings, names, IDs, utilization, or a
target SKU. Do not recommend deletion. Require approval before any resize.
CONTEXT: {json.dumps(context, separators=(",", ":"))}'''


def _parse(response: Any) -> dict:
    text = str(response or "").strip()
    if text.startswith("```"):
        text = "\n".join(text.splitlines()[1:-1]).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("LLM response does not contain a JSON object")
    value = json.loads(text[start:end + 1])
    if not isinstance(value, dict):
        raise ValueError("LLM response must be a JSON object")
    return value


def _wording(issue: dict, value: dict | None) -> dict:
    default = {
        "title": "Review resource capacity",
        "action": "Review and resize capacity",
        "priority": issue.get("severity", "Medium"),
        "implementation_risk": "Medium",
        "execution_plan": [
            "Review observed utilization and the current VM SKU.",
            "Evaluate compatible smaller SKUs and retail prices.",
            "Validate application compatibility and obtain approval.",
            "Perform a dry run before an approved resize.",
        ],
        "explanation": "The analyzer identified a potential rightsizing opportunity.",
    }
    if not isinstance(value, dict):
        return default
    result = default.copy()
    for key in default:
        if key in value and (key != "execution_plan" or isinstance(value[key], list)):
            result[key] = value[key]
    return result


def _build(issue: dict, wording: dict | None) -> dict:
    evidence = _evidence(issue)
    cost = _cost(issue)
    savings = min(cost, _savings(issue))
    result = _wording(issue, wording)
    issue_type = issue.get("issue_type")
    action_type = (
        "resize_vm"
        if issue_type == "VM_RIGHTSIZING"
        else None
    )
    result.update({
        "source_issue_id": issue.get("id"),
        "issue_type": issue_type,
        "resource_id": issue.get("resource_id"),
        "resource_name": issue.get("resource_name"),
        "current_cost": round(cost, 2),
        "estimated_savings": round(savings, 2),
        "potential_savings": round(savings, 2),
        "projected_cost": round(max(0.0, cost - savings), 2),
        "currency": issue.get("currency") or evidence.get("currency", "USD"),
        "cost_source": _source(issue),
        "cost_type": _type(issue),
        "is_estimated": _estimated(issue),
        "confidence": max(0.0, min(1.0, _float(issue.get("confidence"), 0.5))),
        "requires_approval": True,
        "action_type": action_type,
        # Execution action is deterministic.  The LLM wording above is never
        # allowed to decide which Azure operation will be invoked.
        "action": action_type or "review_configuration",
        "current_state": {
            "sku": evidence.get("vm_size") or evidence.get("sku"),
        } if action_type else {},
        "recommended_state": {},
        "observed_cpu_average_percent": evidence.get("cpu_average"),
        "observed_cpu_max_percent": evidence.get("cpu_max"),
        "savings_method": evidence.get("savings_method", "heuristic_rightsizing"),
    })
    return result


def validate_recommendation(item: dict, actionable_issues: list[dict]):
    source = next((x for x in actionable_issues if x.get("id") == item.get("source_issue_id")), None)
    if source is None:
        return False, "source_issue_id does not match an actionable issue"
    evidence = _evidence(source)
    expected = {
        "resource_id": source.get("resource_id"),
        "resource_name": source.get("resource_name"),
        "cost_source": _source(source),
        "cost_type": _type(source),
        "observed_cpu_average_percent": evidence.get("cpu_average"),
        "observed_cpu_max_percent": evidence.get("cpu_max"),
    }
    for key, value in expected.items():
        if isinstance(value, (int, float)):
            if abs(_float(item.get(key), float("inf")) - float(value)) > 0.001:
                return False, f"{key} does not match analyzer evidence"
        elif item.get(key) != value:
            return False, f"{key} does not match source issue"
    if bool(item.get("is_estimated")) != _estimated(source):
        return False, "is_estimated does not match source issue"
    if item.get("requires_approval") is not True:
        return False, "requires_approval must be true"
    if abs(_float(item.get("current_cost")) - _cost(source)) > 0.01:
        return False, "current_cost does not match analyzer"
    savings = _float(item.get("estimated_savings"), -1)
    if savings < 0 or savings > _savings(source) + 0.01:
        return False, "estimated_savings is outside the analyzer estimate"
    if abs(_float(item.get("projected_cost"), -1) - (_float(item.get("current_cost")) - savings)) > 0.01:
        return False, "projected_cost must equal current_cost - estimated_savings"
    return True, "valid"


def reason(state: dict):
    actionable = _actionable([_issue(value) for value in state.get("issues", [])])
    recommendations, errors = [], []
    for issue in actionable:
        # Recommendation wording is deterministic and evidence-backed.  The graph
        # must not make one provider call per issue (or retry after a successful
        # response); interactive chat owns its single, request-scoped LLM call.
        item = _build(issue, None)
        valid, message = validate_recommendation(item, actionable)
        if valid:
            recommendations.append(Recommendation(**item))
        else:
            errors.append({"resource_name": issue.get("resource_name"), "type": "validation", "error": message})
    return {
        **state,
        "recommendations": recommendations,
        "reasoning": "Generated evidence-backed recommendations; the LLM supplied wording only.",
        "recommendation_error": errors,
    }
