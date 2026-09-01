from app.services.resource_evidence import canonical_evidence, evidence_audit, normalized_resource_id

def unattached_disk_analyzer(state):

    intelligence = state.get(
        "finops_context"
    )

    if intelligence is None:

        return {
            **state,
            "unattached_disk_issues": []
        }

    resources = intelligence.resources
    resource_costs = intelligence.resource_costs

    cost_lookup = {
        normalized_resource_id(cost.resource_id): cost
        for cost in resource_costs
        if cost.resource_id
    }
    metric_lookup = {
        normalized_resource_id(metric.resource_id): metric
        for metric in intelligence.metrics
        if metric.resource_id
    }

    issues = []

    for resource in resources:

        resource_type = (
            getattr(
                resource,
                "type",
                ""
            )
            or ""
        ).lower().strip()

        if resource_type != (
            "microsoft.compute/disks"
        ):
            continue

        configuration = resource.configuration or {}
        managed_by = configuration.get("managed_by")
        disk_state = str(configuration.get("disk_state") or "").lower().strip()
        # Configuration evidence is authoritative for attachment. Monitor
        # activity is descriptive evidence and is never a deletion signal.
        if managed_by and disk_state not in {"unattached", "unattachedstate"}:
            continue
        metric = metric_lookup.get(normalized_resource_id(resource.id))

        # -----------------------------------------------------
        # Azure's managedBy is the strongest signal.
        # -----------------------------------------------------

        unattached = (
            not managed_by
        )

        # -----------------------------------------------------
        # diskState can provide a second signal.
        # -----------------------------------------------------

        if disk_state:

            if disk_state in {
                "unattached",
                "unattachedstate",
            }:
                unattached = True

        if not unattached:
            continue

        cost = cost_lookup.get(normalized_resource_id(resource.id))

        if cost:

            monthly_cost = float(
                cost.monthly_cost or 0
            )

            currency = (
                cost.currency
                or "USD"
            )

            estimated_savings = (
                monthly_cost
            )

            cost_available = (
                cost.cost_data_available
                and monthly_cost > 0
            )

            cost_source = (
                cost.cost_source
            )

            cost_type = (
                cost.cost_type
            )

            is_estimated = (
                cost.is_estimated
            )

        else:

            monthly_cost = 0.0
            estimated_savings = 0.0
            currency = "USD"

            cost_available = False

            cost_source = (
                "Unavailable"
            )

            cost_type = (
                "unavailable"
            )

            is_estimated = False

        evidence = canonical_evidence(
            resource.model_dump(),
            cost.model_dump() if cost else {},
            metric.model_dump() if metric else {},
        )
        evidence["configuration"]["attachment_state"] = disk_state or ("attached" if managed_by else "unattached")
        evidence["configuration"]["attached_vm"] = managed_by or None
        issue = {
                "resource_id":
                    resource.id,

                "resource_name":
                    resource.name,

                "resource_type":
                    resource.type,

                "issue":
                    "Unattached managed disk",

                "issue_type":
                    "Unattached managed disk",

                "category":
                    "Cost Optimization",

                "description":
                    (
                        "Managed disk is not attached "
                        "to a virtual machine and may "
                        "be generating unnecessary "
                        "storage cost."
                    ),

                "finding": "Managed Disk is unattached and incurs storage cost.",
                "recommendation": "Review the unattached disk for approved deletion; no Azure action is executed by this analysis.",
                "reason": "Attachment-state configuration evidence identifies an unattached Managed Disk.",
                "savings_available": cost_available,
                "configuration_evidence": evidence["configuration"],
                "utilization_evidence": evidence["metrics"],
                "cost_evidence": {key: evidence[key] for key in ("cost", "cost_source", "cost_type", "is_estimated", "cost_data_available")},
                "evidence": evidence,
                "disk_state": disk_state,

                "monthly_cost":
                    monthly_cost,

                "current_monthly_cost":
                    monthly_cost,

                "estimated_savings":
                    estimated_savings,

                "estimated_monthly_savings":
                    estimated_savings,

                "currency":
                    currency,

                "cost_source":
                    cost_source,

                "cost_type":
                    cost_type,

                "is_estimated":
                    is_estimated,

                "cost_data_available":
                    cost_available,

                "pricing_method":
                    (
                        cost.pricing_method
                        if cost
                        else None
                    ),

                "pricing_unit":
                    (
                        cost.pricing_unit
                        if cost
                        else None
                    ),

                "hourly_price":
                    (
                        cost.hourly_price
                        if cost
                        else None
                    ),

                "disk_size_gb":
                    (
                        cost.disk_size_gb
                        if cost
                        else getattr(
                            resource,
                            "disk_size_gb",
                            None
                        )
                    ),

                "sku":
                    (
                        cost.sku
                        if cost
                        else getattr(
                            resource,
                            "sku",
                            None
                        )
                    ),

                "region":
                    (
                        cost.region
                        if cost
                        else resource.location
                    ),

                "severity":
                    "Medium",

                "confidence":
                    0.95
                    if unattached
                    else 0.5,

                "detected_by": "managed_disk_analyzer",
            }
        evidence_audit(evidence, "managed_disk_analyzer", issue["finding"], issue["recommendation"])
        issues.append(issue)

    return {
        **state,
        "unattached_disk_issues": issues
    }