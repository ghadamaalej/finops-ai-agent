from app.services.azure_context_builder import AzureContextBuilder
from app.agent.analyzers.cost_analyzer import CostAnalyzer


SUBSCRIPTION_ID = "6850d94e-3234-463d-aa51-615d3c486939"


def main():

    print()
    print("=" * 70)
    print("COST ANALYZER + RETAIL PRICING TEST")
    print("=" * 70)

    builder = AzureContextBuilder()

    context = builder.build(
        SUBSCRIPTION_ID
    )

    state = {
        "finops_context": context
    }

    cost_analyzer = CostAnalyzer()
    result = cost_analyzer.analyze(state)

    issues = result.get(
        "cost_issues",
        []
    )

    print()
    print("=" * 70)
    print("COST ISSUES")
    print("=" * 70)

    for issue in issues:

        print()
        print(
            f"Resource       : "
            f"{issue.get('resource_name')}"
        )

        print(
            f"CPU            : "
            f"{issue.get('cpu')}"
        )

        print(
            f"Monthly cost   : "
            f"{issue.get('monthly_cost')}"
        )

        print(
            f"Savings        : "
            f"{issue.get('estimated_savings')}"
        )

        print(
            f"Currency       : "
            f"{issue.get('currency')}"
        )

        print(
            f"Cost source    : "
            f"{issue.get('cost_source')}"
        )

        print(
            f"Cost type      : "
            f"{issue.get('cost_type')}"
        )

        print(
            f"Estimated      : "
            f"{issue.get('is_estimated')}"
        )

        print(
            f"Confidence     : "
            f"{issue.get('confidence')}"
        )

    print()
    print("=" * 70)

    print(
        f"TOTAL COST ISSUES: {len(issues)}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()