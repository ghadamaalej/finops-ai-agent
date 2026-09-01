from app.services.azure_context_builder import (
    AzureContextBuilder
)

from app.agent.nodes.intelligence_builder import (
    build_intelligence_context
)

from app.agent.analyzers.cost_analyzer import (
    CostAnalyzer
)

from app.agent.analyzers.performance_analyzer import (
    PerformanceAnalyzer
)

from app.agent.analyzers.security_analyzer import (
    SecurityAnalyzer
)

from app.agent.analyzers.governance_analyzer import (
    GovernanceAnalyzer
)


def test_analyzers():

    subscription_id = (
        "6850d94e-3234-463d-aa51-615d3c486939"
    )

    builder = AzureContextBuilder()

    azure_context = builder.build(
        subscription_id
    )

    state = {
        "azure_context": azure_context
    }

    state = build_intelligence_context(
        state
    )

    context = state["finops_context"]

    # ---------------------------------------------------------
    # ANALYZERS
    # ---------------------------------------------------------

    cost_issues = (
        CostAnalyzer().analyze(
            context
        )
    )

    perf_issues = (
        PerformanceAnalyzer().analyze(
            context
        )
    )

    security_issues = (
        SecurityAnalyzer().analyze(
            context
        )
    )

    governance_issues = (
        GovernanceAnalyzer().analyze(
            context
        )
    )

    # ---------------------------------------------------------
    # OUTPUT
    # ---------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)

    print(
        "Cost issues:",
        len(cost_issues)
    )

    print(
        "Performance issues:",
        len(perf_issues)
    )

    print(
        "Security issues:",
        len(security_issues)
    )

    print(
        "Governance issues:",
        len(governance_issues)
    )

    # ---------------------------------------------------------
    # COST DETAILS
    # ---------------------------------------------------------

    print("\n===== COST ISSUES =====")

    for issue in cost_issues:

        print(
            f"\nResource: "
            f"{issue.get('resource_name')}"
        )

        print(
            f"CPU: "
            f"{issue.get('cpu')}"
        )

        print(
            f"Monthly cost: "
            f"{issue.get('current_monthly_cost')}"
        )

        print(
            f"Estimated savings: "
            f"{issue.get('estimated_monthly_savings')}"
        )

        print(
            f"Currency: "
            f"{issue.get('currency')}"
        )

        print(
            f"Source: "
            f"{issue.get('cost_source')}"
        )

        print(
            f"Estimated: "
            f"{issue.get('is_estimated')}"
        )

    # ---------------------------------------------------------
    # ASSERTIONS
    # ---------------------------------------------------------

    assert context.resources

    assert isinstance(
        cost_issues,
        list
    )

    assert isinstance(
        perf_issues,
        list
    )

    assert isinstance(
        security_issues,
        list
    )

    assert isinstance(
        governance_issues,
        list
    )