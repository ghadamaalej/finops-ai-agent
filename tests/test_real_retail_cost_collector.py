from app.Collectors.resource_collector import ResourceCollector
from app.Collectors.retail_cost_collector import RetailCostCollector


SUBSCRIPTION_ID = (
    "6850d94e-3234-463d-aa51-615d3c486939"
)


def main():

    print()
    print("=" * 70)
    print("REAL RETAIL COST COLLECTOR TEST")
    print("=" * 70)

    # ---------------------------------------------------------
    # 1. Discover resources
    # ---------------------------------------------------------

    resource_collector = ResourceCollector()

    resources = resource_collector.collect(
        SUBSCRIPTION_ID
    )

    print(
        f"\nResources discovered: {len(resources)}"
    )

    # ---------------------------------------------------------
    # 2. Show pricing candidates
    # ---------------------------------------------------------

    pricing_resources = []

    for resource in resources:

        resource_type = (
            resource.get("type", "")
            .lower()
        )

        if resource_type in {
            "microsoft.compute/virtualmachines",
            "microsoft.compute/disks",
        }:

            pricing_resources.append(resource)

    print(
        f"Pricing candidates: "
        f"{len(pricing_resources)}"
    )

    print()
    print("=" * 70)
    print("PRICING CANDIDATES")
    print("=" * 70)

    for resource in pricing_resources:

        print()

        print(
            f"Name     : "
            f"{resource.get('name')}"
        )

        print(
            f"Type     : "
            f"{resource.get('type')}"
        )

        print(
            f"Region   : "
            f"{resource.get('location')}"
        )

        print(
            f"SKU      : "
            f"{resource.get('sku')}"
        )

        print(
            f"SKU name : "
            f"{resource.get('sku_name')}"
        )

        if resource_type := (
            resource.get("type", "")
            .lower()
        ) == "microsoft.compute/disks":

            print(
                f"Disk size: "
                f"{resource.get('disk_size_gb')}"
            )

    # ---------------------------------------------------------
    # 3. Collect Retail prices
    # ---------------------------------------------------------

    collector = RetailCostCollector()

    costs = collector.collect(
        pricing_resources
    )

    print()
    print("=" * 70)
    print("RETAIL COST RESULTS")
    print("=" * 70)

    if not costs:

        print()
        print("❌ NO COST RECORDS WERE RETURNED")
        print()
        print("This means the problem is inside")
        print("RetailCostCollector.collect().")
        return

    # ---------------------------------------------------------
    # 4. Print every cost
    # ---------------------------------------------------------

    for cost in costs:

        print()
        print("-" * 70)

        print(
            f"Resource       : "
            f"{cost.get('resource_name')}"
        )

        print(
            f"Type           : "
            f"{cost.get('resource_type')}"
        )

        print(
            f"SKU            : "
            f"{cost.get('sku')}"
        )

        print(
            f"Region         : "
            f"{cost.get('region')}"
        )

        print(
            f"Monthly cost   : "
            f"{cost.get('monthly_cost')}"
        )

        print(
            f"Currency       : "
            f"{cost.get('currency')}"
        )

        print(
            f"Source         : "
            f"{cost.get('cost_source')}"
        )

        print(
            f"Cost type      : "
            f"{cost.get('cost_type')}"
        )

        print(
            f"Estimated      : "
            f"{cost.get('is_estimated')}"
        )

        print(
            f"Pricing method : "
            f"{cost.get('pricing_method')}"
        )

        print(
            f"Pricing SKU    : "
            f"{cost.get('pricing_sku')}"
        )

        print(
            f"Unit price     : "
            f"{cost.get('unit_price')}"
        )

        print(
            f"Unit           : "
            f"{cost.get('unit_of_measure')}"
        )

        print(
            f"Disk tier      : "
            f"{cost.get('disk_tier')}"
        )

    # ---------------------------------------------------------
    # 5. Summary
    # ---------------------------------------------------------

    total = sum(
        float(
            cost.get("monthly_cost") or 0
        )
        for cost in costs
    )

    estimated = [
        cost
        for cost in costs
        if cost.get("is_estimated") is True
    ]

    actual = [
        cost
        for cost in costs
        if cost.get("is_estimated") is not True
    ]

    print()
    print("=" * 70)
    print("COST SUMMARY")
    print("=" * 70)

    print(
        f"Resources discovered : "
        f"{len(resources)}"
    )

    print(
        f"Pricing candidates    : "
        f"{len(pricing_resources)}"
    )

    print(
        f"Cost records          : "
        f"{len(costs)}"
    )

    print(
        f"Estimated records     : "
        f"{len(estimated)}"
    )

    print(
        f"Actual records        : "
        f"{len(actual)}"
    )

    print(
        f"TOTAL MONTHLY COST    : "
        f"${total:.2f}"
    )

    print("=" * 70)


if __name__ == "__main__":
    main()