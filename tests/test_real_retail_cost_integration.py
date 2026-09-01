from app.services.azure_context_builder import AzureContextBuilder


SUBSCRIPTION_ID = "6850d94e-3234-463d-aa51-615d3c486939"


def main():

    print()
    print("=" * 70)
    print("REAL AZURE RETAIL COST INTEGRATION TEST")
    print("=" * 70)

    builder = AzureContextBuilder()

    context = builder.build(
        SUBSCRIPTION_ID
    )

    print()
    print("=" * 70)
    print("RESOURCE COST RESULTS")
    print("=" * 70)

    for cost in context.resource_costs:

        print()
        print(f"Resource       : {cost.resource_name}")
        print(f"Type           : {cost.resource_type}")
        print(f"Monthly cost   : {cost.monthly_cost:.2f}")
        print(f"Currency       : {cost.currency}")
        print(f"Source         : {cost.cost_source}")
        print(f"Type           : {cost.cost_type}")
        print(f"Estimated      : {cost.is_estimated}")
        print(f"Pricing method : {cost.pricing_method}")
        print(f"SKU            : {cost.sku}")
        print(f"Region         : {cost.region}")

    print()
    print("=" * 70)

    total = sum(
        float(cost.monthly_cost or 0)
        for cost in context.resource_costs
    )

    print(
        f"TOTAL ESTIMATED MONTHLY COST: "
        f"{total:.2f}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()