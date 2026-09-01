from app.services.azure_context_builder import (
    AzureContextBuilder
)

from app.agent.nodes.intelligence_builder import (
    build_intelligence_context
)

from app.agent.analyzers.cost_analyzer import (
    CostAnalyzer
)


SUBSCRIPTION_ID = (
    "6850d94e-3234-463d-aa51-615d3c486939"
)


def test_cost_analyzer_has_estimated_costs():

    builder = AzureContextBuilder()

    azure_context = builder.build(
        SUBSCRIPTION_ID
    )

    state = {
        "azure_context":
            azure_context
    }

    state = build_intelligence_context(
        state
    )

    context = state[
        "finops_context"
    ]

    issues = CostAnalyzer().analyze(
        context
    )

    print("\n")
    print("=" * 70)
    print("COST ANALYZER VALIDATION")
    print("=" * 70)

    print(
        f"Cost issues: {len(issues)}"
    )

    for issue in issues:

        print("\n-------------------------")

        print(
            "Resource:",
            issue["resource_name"]
        )

        print(
            "CPU:",
            issue["cpu"]
        )

        print(
            "Current monthly cost:",
            issue["current_monthly_cost"]
        )

        print(
            "Estimated savings:",
            issue["estimated_monthly_savings"]
        )

        print(
            "Currency:",
            issue["currency"]
        )

        print(
            "Source:",
            issue["cost_source"]
        )

        print(
            "Estimated:",
            issue["is_estimated"]
        )

        print(
            "Pricing validated:",
            issue["pricing_validated"]
        )

    # There should be cost data in the context
    assert context.resource_costs

    # At least one cost record should have a positive price
    positive_costs = [
        cost
        for cost in context.resource_costs
        if float(
            cost.monthly_cost or 0
        ) > 0
    ]

    assert positive_costs

    # At least one metric exists
    assert context.metrics

    # Analyzer must return a list
    assert isinstance(
        issues,
        list
    )

    # Every savings recommendation must
    # have positive estimated savings
    for issue in issues:

        assert (
            issue["estimated_monthly_savings"]
            > 0
        )

        assert (
            issue["current_monthly_cost"]
            > 0
        )

        # Retail pricing is estimated
        assert (
            issue["is_estimated"]
            is True
        )

        assert (
            issue["cost_source"]
            == "Azure Retail Prices"
        )