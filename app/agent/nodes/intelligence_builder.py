from collections import Counter

from app.models.finops_intelligence import (
    FinOpsIntelligenceContext,
    CostInsight,
    PerformanceInsight,
    SecurityInsight,
    GovernanceInsight,
)


def build_intelligence_context(state):

    azure = state.get(
        "azure_context"
    )

    if azure is None:

        raise ValueError(
            "azure_context is required"
        )

    # ---------------------------------------------------------
    # Performance
    # ---------------------------------------------------------

    high_cpu = []

    low_cpu = []

    for metric in azure.metrics:

        if metric.cpu_average is None:
            continue

        if metric.cpu_average >= 80:

            high_cpu.append(
                metric.resource_id
            )

        if metric.cpu_average <= 10:

            low_cpu.append(
                metric.resource_id
            )

    # ---------------------------------------------------------
    # Cost
    # ---------------------------------------------------------

    total_cost = sum(

        float(
            cost.monthly_cost or 0
        )

        for cost in azure.resource_costs
    )

    sorted_costs = sorted(
        azure.resource_costs,
        key=lambda c: float(
            c.monthly_cost or 0
        ),
        reverse=True
    )

    estimated_cost = sum(
    float(cost.monthly_cost or 0)
    for cost in azure.resource_costs
    if cost.is_estimated
    )

    actual_cost = sum(
    float(cost.monthly_cost or 0)
    for cost in azure.resource_costs
    if not cost.is_estimated
    )

    estimated_cost_count = sum(
    1
    for cost in azure.resource_costs
    if cost.is_estimated
    )

    actual_cost_count = sum(
    1
    for cost in azure.resource_costs
    if not cost.is_estimated
)

    top_cost_drivers = {}

    for cost in sorted_costs[:10]:

        top_cost_drivers[
            cost.resource_id
        ] = float(
            cost.monthly_cost or 0
        )

    # ---------------------------------------------------------
    # Security
    # ---------------------------------------------------------

    severity = Counter()

    for finding in azure.security_findings:

        severity[
            finding.severity
        ] += 1

    # ---------------------------------------------------------
    # Governance
    # ---------------------------------------------------------

    compliance = 100

    violations = []

    if azure.governance:

        compliance = (
            azure.governance.compliance_score
        )

        violations = (
            azure.governance.policy_violations
        )

    # ---------------------------------------------------------
    # Context
    # ---------------------------------------------------------

    finops_context = FinOpsIntelligenceContext(

        subscription_id=
            azure.subscription_id,

        resources=
            azure.resources,

        metrics=
            azure.metrics,

        resource_costs=
            azure.resource_costs,

        security_findings=
            azure.security_findings,

        governance=
            azure.governance,

        cost=CostInsight(

        total_cost=total_cost,

        monthly_forecast=0,

        estimated_cost=estimated_cost,

        actual_cost=actual_cost,

        estimated_cost_count=estimated_cost_count,

        actual_cost_count=actual_cost_count,

        top_cost_drivers=top_cost_drivers,

        cost_trend="stable"
        ),

        performance=PerformanceInsight(

                high_cpu_resources=
                    high_cpu,

                low_cpu_resources=
                    low_cpu
            ),

        security=SecurityInsight(

                findings_by_severity=
                    dict(severity),

                high_risk_count=
                    severity.get(
                        "High",
                        0
                    )
            ),

        governance_summary=GovernanceInsight(

                compliance_score=
                    compliance,

                policy_violations=
                    violations
            )
    )

    return {
        **state,
        "finops_context":
            finops_context
    }