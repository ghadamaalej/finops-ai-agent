from app.database.connection import SessionLocal
from app.database.repositories.cost_cache_repository import CostCacheRepository


def test_cost_cache():

    db = SessionLocal()

    repository = CostCacheRepository()


    test_costs = [

        {
            "resource_id":
                "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-test",

            "resource_name":
                "vm-test",

            "service_name":
                "Virtual Machines",

            "monthly_cost":
                125.50,

            "currency":
                "USD"
        },

        {
            "resource_id":
                "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-test-2",

            "resource_name":
                "vm-test-2",

            "service_name":
                "Virtual Machines",

            "monthly_cost":
                75.25,

            "currency":
                "USD"
        }

    ]


    print("\nSaving test cache...")

    repository.save_cache(
        db,
        subscription_id="test-subscription",
        costs=test_costs,
    )


    print("Reading cache...")

    cached = repository.get_valid_cache(
        db,
        subscription_id="test-subscription",
        hours=12
    )


    print(
        f"Cached records: {len(cached)}"
    )


    for item in cached:

        print(
            item.resource_name,
            item.monthly_cost,
            item.currency
        )


    assert len(cached) == 2

    assert cached[0].resource_name in [
        "vm-test",
        "vm-test-2"
    ]


    db.close()
