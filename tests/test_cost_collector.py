from app.Collectors.cost_collector import CostCollector


def test_cost_collection():

    subscription_id = (
        "6850d94e-3234-463d-aa51-615d3c486939"
    )

    collector = CostCollector()

    costs = collector.collect(
        subscription_id
    )

    print()
    print("=" * 70)
    print("COST COLLECTION TEST")
    print("=" * 70)

    print(
        f"Number of cost records: "
        f"{len(costs)}"
    )

    for cost in costs[:20]:
        print(cost)

    assert isinstance(
        costs,
        list
    )

    assert len(costs) > 0, (
        "Azure Cost Management returned "
        "no resource-level costs. "
        "Check Cost Management data availability "
        "and subscription billing scope."
    )

    positive_costs = [
        cost
        for cost in costs
        if float(
            cost.get(
                "monthly_cost",
                0
            )
        ) > 0
    ]

    print()
    print(
        f"Resources with positive cost: "
        f"{len(positive_costs)}"
    )

    assert len(positive_costs) > 0, (
        "Cost records exist but all "
        "monthly_cost values are zero."
    )