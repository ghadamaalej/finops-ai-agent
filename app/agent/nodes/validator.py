def _get_value(obj, key, default=None):
    if isinstance(obj, dict):
        return obj.get(key, default)

    return getattr(obj, key, default)


def _get_evidence_value(issue, key, default=None):
    evidence = _get_value(issue, "evidence", {})
    if isinstance(evidence, dict):
        return evidence.get(key, default)
    return default


def validate(state):

    valid = []
    rejected = []

    issues = state.get("issues", [])
    recommendations = state.get("recommendations", [])

    issue_by_id = {}
    issue_by_resource = {}

    for issue in issues:

        issue_id = _get_value(issue, "id")
        resource_id = _get_value(issue, "resource_id")

        if issue_id:
            issue_by_id[str(issue_id)] = issue

        if resource_id:
            normalized_resource_id = str(resource_id).lower()
            issue_by_resource.setdefault(
                normalized_resource_id,
                []
            ).append(issue)

    learned_confidence = (
        state
        .get("recommendation_intelligence", {})
        .get("recommendation_confidence", 0.5)
    )

    try:
        learned_confidence = float(learned_confidence)
    except (TypeError, ValueError):
        learned_confidence = 0.5

    learned_confidence = max(
        0.0,
        min(1.0, learned_confidence)
    )

    for rec in recommendations:

        source_issue_id = _get_value(
            rec,
            "source_issue_id"
        )

        resource_id = _get_value(
            rec,
            "resource_id"
        )
        normalized_resource_id = str(resource_id).lower() if resource_id else None

        resource_name = _get_value(
            rec,
            "resource_name"
        )

        issue = None

        if source_issue_id:

            issue = issue_by_id.get(
                str(source_issue_id)
            )

        if issue is None and normalized_resource_id:

            matching = issue_by_resource.get(
                normalized_resource_id,
                []
            )

            if len(matching) == 1:
                issue = matching[0]

        if issue is None:

            rejected.append({
                "recommendation": rec,
                "reason":
                    "Source issue could not be uniquely identified"
            })

            continue

        issue_resource_id = _get_value(
            issue,
            "resource_id"
        )

        if resource_id != issue_resource_id:

            rejected.append({
                "recommendation": rec,
                "reason":
                    "Recommendation resource_id does not match "
                    "source issue"
            })

            continue

        issue_resource_name = _get_value(
            issue,
            "resource_name"
        )

        if (
            issue_resource_name
            and resource_name != issue_resource_name
        ):

            rejected.append({
                "recommendation": rec,
                "reason":
                    "Recommendation resource_name does not match "
                    "source issue"
            })

            continue

        # CPU values are structured evidence.  Do not attempt to validate
        # prose; reject a recommendation that changes their units or values.
        for recommendation_key, evidence_key, tolerance in (
            ("observed_cpu_average_percent", "cpu_average", 0.001),
            ("observed_cpu_max_percent", "cpu_max", 0.01),
        ):
            source_value = _get_evidence_value(issue, evidence_key)
            if source_value is None:
                continue
            try:
                observed_value = float(
                    _get_value(rec, recommendation_key)
                )
                source_metric = float(source_value)
            except (TypeError, ValueError):
                rejected.append({
                    "recommendation": rec,
                    "reason": f"Missing or invalid {recommendation_key}",
                })
                break
            if abs(observed_value - source_metric) > tolerance:
                rejected.append({
                    "recommendation": rec,
                    "reason": f"{recommendation_key} does not match analyzer evidence",
                })
                break
        else:
            pass

        if rejected and rejected[-1].get("recommendation") is rec:
            continue

        analyzer_cost = float(
            _get_value(
                issue,
                "current_monthly_cost",
                0
            ) or 0
        )

        recommendation_cost = float(
            _get_value(
                rec,
                "current_cost",
                0
            ) or 0
        )

        if analyzer_cost < 0:

            rejected.append({
                "recommendation": rec,
                "reason":
                    "Analyzer contains negative current cost"
            })

            continue

        if recommendation_cost < 0:

            rejected.append({
                "recommendation": rec,
                "reason":
                    "Negative recommendation current cost"
            })

            continue

        estimated_savings = float(
            _get_value(
                rec,
                "estimated_savings",
                0
            ) or 0
        )

        allowed_savings = float(
            _get_value(
                issue,
                "estimated_monthly_savings",
                0
            ) or 0
        )

        if estimated_savings < 0:

            rejected.append({
                "recommendation": rec,
                "reason":
                    "Negative estimated savings"
            })

            continue

        if estimated_savings > allowed_savings:

            rejected.append({
                "recommendation": rec,
                "reason":
                    "Savings estimation exceeds analyzer value"
            })

            continue

        if estimated_savings > analyzer_cost:

            rejected.append({
                "recommendation": rec,
                "reason":
                    "Estimated savings cannot exceed current cost"
            })

            continue

        if abs(
            recommendation_cost - analyzer_cost
        ) > 0.01:

            rejected.append({
                "recommendation": rec,
                "reason":
                    "Current cost does not match analyzer"
            })

            continue

        expected_projected_cost = (
            analyzer_cost - estimated_savings
        )

        recommendation_projected_cost = float(
            _get_value(
                rec,
                "projected_cost",
                0
            ) or 0
        )

        if abs(
            recommendation_projected_cost
            - expected_projected_cost
        ) > 0.01:

            rejected.append({
                "recommendation": rec,
                "reason":
                    "Projected cost does not equal "
                    "current cost - estimated savings"
            })

            continue

        confidence = float(
            _get_value(
                rec,
                "confidence",
                0
            ) or 0
        )

        if not 0 <= confidence <= 1:

            rejected.append({
                "recommendation": rec,
                "reason":
                    "Invalid confidence"
            })

            continue

        final_confidence = min(
            confidence,
            learned_confidence
        )

        if isinstance(rec, dict):
            rec["confidence"] = final_confidence
            rec["currency"] = _get_value(
                issue,
                "currency"
            )
            rec["cost_source"] = _get_value(
                issue,
                "cost_source"
            )
            rec["cost_type"] = _get_value(
                issue,
                "cost_type"
            )
            rec["is_estimated"] = _get_value(
                issue,
                "is_estimated",
                True
            )

        else:
            rec.confidence = final_confidence
            rec.currency = _get_value(
                issue,
                "currency"
            )
            rec.cost_source = _get_value(
                issue,
                "cost_source"
            )
            rec.cost_type = _get_value(
                issue,
                "cost_type"
            )
            rec.is_estimated = _get_value(
                issue,
                "is_estimated",
                True
            )

        valid.append(rec)

    print(
        "\n===== VALIDATION RESULT ====="
    )

    print(
        f"Valid recommendations: {len(valid)}"
    )

    print(
        f"Rejected recommendations: {len(rejected)}"
    )

    for item in rejected:

        print(
            "\nRejected:",
            item["reason"]
        )

    return {
        **state,

        "validated_recommendations":
            valid,

        "validation_errors":
            rejected
    }
