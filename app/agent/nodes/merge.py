from uuid import uuid4

from app.models.issue import Issue


def _extract_numeric(value, default=0.0):
    """
    Safely convert a value into float.

    Supports:
    - int / float
    - numeric strings
    - nested dictionaries containing common numeric fields
    """

    if value is None:
        return default

    if isinstance(value, bool):
        return float(value)

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    if isinstance(value, dict):

        for key in (
            "estimated_savings",
            "estimated_monthly_savings",
            "current_monthly_cost",
            "monthly_cost",
            "value",
            "amount",
        ):
            if key in value:
                return _extract_numeric(
                    value[key],
                    default
                )

    return default


def _extract_bool(value, default=False):
    """
    Safely convert a value into bool.
    """

    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        return value.lower() in (
            "true",
            "1",
            "yes",
            "y",
        )

    if isinstance(value, (int, float)):
        return bool(value)

    return default


def normalize_issue(issue):
    """
    Normalize analyzer output into the canonical Issue model.

    Important:
    Cost provenance MUST survive normalization.
    """

    if isinstance(issue, Issue):
        return issue

    if not isinstance(issue, dict):
        raise TypeError(
            f"Unsupported issue type: {type(issue)}"
        )

    evidence = issue.get(
        "evidence",
        {}
    )

    if not isinstance(evidence, dict):
        evidence = {}

    def value_from_issue_or_evidence(
        key,
        default=None
    ):
        if key in issue and issue[key] is not None:
            return issue[key]

        if key in evidence and evidence[key] is not None:
            return evidence[key]

        return default

    estimated_savings = _extract_numeric(
        value_from_issue_or_evidence(
            "estimated_monthly_savings",
            value_from_issue_or_evidence(
                "estimated_savings",
                0.0
            )
        )
    )

    monthly_cost = _extract_numeric(
        value_from_issue_or_evidence(
            "current_monthly_cost",
            value_from_issue_or_evidence(
                "monthly_cost",
                0.0
            )
        )
    )

    confidence = _extract_numeric(
        issue.get(
            "confidence",
            0.5
        ),
        0.5
    )

    confidence = max(
        0.0,
        min(1.0, confidence)
    )

    risk_score = _extract_numeric(
        issue.get(
            "risk_score",
            0.0
        )
    )

    issue_id = issue.get("id")

    if not issue_id:
        issue_id = str(uuid4())

    cost_source = value_from_issue_or_evidence(
        "cost_source"
    )

    cost_type = value_from_issue_or_evidence(
        "cost_type"
    )

    is_estimated = _extract_bool(
        value_from_issue_or_evidence(
            "is_estimated",
            False
        )
    )

    currency = value_from_issue_or_evidence(
        "currency"
    )

    cost_data_available = _extract_bool(
        value_from_issue_or_evidence(
            "cost_data_available",
            False
        )
    )

    hourly_price_value = value_from_issue_or_evidence(
        "hourly_price"
    )

    hourly_price = (
        _extract_numeric(hourly_price_value)
        if hourly_price_value is not None
        else None
    )

    estimated_hours_value = value_from_issue_or_evidence(
        "estimated_hours"
    )

    estimated_hours = (
        _extract_numeric(estimated_hours_value)
        if estimated_hours_value is not None
        else None
    )

    return Issue(

        id=str(issue_id),

        category=issue.get(
            "category",
            "Cost"
        ),

        issue_type=issue.get(
            "issue_type",
            issue.get(
                "issue",
                "Unknown"
            )
        ),

        severity=issue.get(
            "severity",
            "Medium"
        ),

        confidence=confidence,

        resource_id=issue.get(
            "resource_id",
            ""
        ),

        resource_name=issue.get(
            "resource_name",
            ""
        ),

        resource_type=issue.get(
            "resource_type",
            ""
        ),

        description=issue.get(
            "description",
            issue.get(
                "issue",
                ""
            )
        ),

        evidence=evidence,

        current_monthly_cost=monthly_cost,

        estimated_monthly_savings=estimated_savings,

        business_impact=issue.get(
            "business_impact",
            ""
        ),

        risk_score=risk_score,

        detected_by=issue.get(
            "detected_by",
            "analyzer"
        ),

        cost_source=cost_source,

        cost_type=cost_type,

        is_estimated=is_estimated,

        currency=currency,

        cost_data_available=cost_data_available,

        hourly_price=hourly_price,

        estimated_hours=estimated_hours,
    )

def merge_issues(state):

    merged = {}

    analyzer_keys = (
        "cost_issues",
        "performance_issues",
        "security_issues",
        "governance_issues",
        "unattached_disk_issues",
    )

    for key in analyzer_keys:

        raw_issues = state.get(
            key,
            []
        )

        for raw_issue in raw_issues:

            try:
                issue = normalize_issue(raw_issue)

            except Exception as exc:

                print(
                    f"⚠️ Could not normalize issue "
                    f"from {key}: {exc}"
                )

                continue

            if not issue.resource_id:
                continue

            dedup_key = (
                str(issue.resource_id or "").lower(),
                issue.issue_type
            )

            existing = merged.get(
                dedup_key
            )

            if existing is None:

                merged[dedup_key] = issue

                continue

            existing_savings = float(
                existing.estimated_monthly_savings or 0
            )

            new_savings = float(
                issue.estimated_monthly_savings or 0
            )

            existing_cost = float(
                existing.current_monthly_cost or 0
            )

            new_cost = float(
                issue.current_monthly_cost or 0
            )

            if (
                not existing.cost_data_available
                and issue.cost_data_available
            ):
                merged[dedup_key] = issue
                continue

            if (
                existing_cost <= 0
                and new_cost > 0
            ):
                merged[dedup_key] = issue
                continue


            if new_savings > existing_savings:
                merged[dedup_key] = issue
                continue

            if issue.confidence > existing.confidence:
                merged[dedup_key] = issue

    issues = list(
        merged.values()
    )

    issues.sort(
        key=lambda x: (
            x.risk_score,
            x.estimated_monthly_savings,
        ),
        reverse=True
    )

    print(
        "\n===== MERGED ISSUES ====="
    )

    print(
        f"Total issues: {len(issues)}"
    )

    for issue in issues:

        print(
            f"""
Issue ID       : {issue.id}
Resource       : {issue.resource_name}
Resource ID    : {issue.resource_id}
Type           : {issue.issue_type}
Monthly Cost   : ${issue.current_monthly_cost:.2f}
Savings        : ${issue.estimated_monthly_savings:.2f}
Cost Source    : {issue.cost_source}
Cost Type      : {issue.cost_type}
Estimated      : {issue.is_estimated}
Cost Available : {issue.cost_data_available}
Confidence     : {issue.confidence}
Severity       : {issue.severity}
"""
        )

    return {
        **state,
        "issues": issues,
    }