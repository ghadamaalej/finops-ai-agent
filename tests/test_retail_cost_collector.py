from app.Collectors.retail_cost_collector import (
    RetailCostCollector
)


def main():

    resources = [

        {
            "id": "/subscriptions/test/resourceGroups/test/providers/Microsoft.Compute/disks/test-premium",

            "name": "test-premium-disk",

            "type":
                "microsoft.compute/disks",

            "location":
                "westeurope",

            "sku":
                "Premium_LRS",

            "sku_name":
                "Premium_LRS",

            "disk_size_gb":
                128,
        },

        {
            "id": "/subscriptions/test/resourceGroups/test/providers/Microsoft.Compute/disks/test-standardssd",

            "name": "test-standardssd-disk",

            "type":
                "microsoft.compute/disks",

            "location":
                "westeurope",

            "sku":
                "StandardSSD_LRS",

            "sku_name":
                "StandardSSD_LRS",

            "disk_size_gb":
                128,
        },

        {
            "id": "/subscriptions/test/resourceGroups/test/providers/Microsoft.Compute/disks/test-hdd",

            "name": "test-standard-disk",

            "type":
                "microsoft.compute/disks",

            "location":
                "westeurope",

            "sku":
                "Standard_LRS",

            "sku_name":
                "Standard_LRS",

            "disk_size_gb":
                128,
        },
    ]

    collector = RetailCostCollector()

    costs = collector.collect(
        resources
    )

    print("\n")
    print("=" * 70)
    print("COLLECTED COSTS")
    print("=" * 70)

    for cost in costs:

        print("\n")

        print(
            f"Resource       : "
            f"{cost['resource_name']}"
        )

        print(
            f"SKU            : "
            f"{cost['sku']}"
        )

        print(
            f"Disk tier      : "
            f"{cost.get('disk_tier')}"
        )

        print(
            f"Pricing SKU    : "
            f"{cost.get('pricing_sku')}"
        )

        print(
            f"Monthly cost   : "
            f"{cost['monthly_cost']:.2f}"
        )

        print(
            f"Currency       : "
            f"{cost['currency']}"
        )

        print(
            f"Cost source    : "
            f"{cost['cost_source']}"
        )

        print(
            f"Estimated      : "
            f"{cost['is_estimated']}"
        )

    print("\n")
    print("=" * 70)
    print(
        f"TOTAL RECORDS: {len(costs)}"
    )
    print("=" * 70)


if __name__ == "__main__":
    main()