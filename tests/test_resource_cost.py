from app.Collectors.cost_collector import CostCollector


SUBSCRIPTION_ID = "6850d94e-3234-463d-aa51-615d3c486939"

TARGET_RESOURCE = (
    "/subscriptions/6850d94e-3234-463d-aa51-615d3c486939"
    "/resourcegroups/rg_ghadamaalej"
    "/providers/microsoft.compute/virtualmachines/finops-test-vm"
)


def main():
    print("=" * 70)
    print("RESOURCE COST DIAGNOSTIC")
    print("=" * 70)

    print(f"\nSubscription: {SUBSCRIPTION_ID}")
    print(f"Target VM:    finops-test-vm")

    # ---------------------------------------------------------
    # 1. Create collector
    # ---------------------------------------------------------

    print("\n[1] Creating CostCollector...")

    collector = CostCollector()

    print("    CostCollector created successfully.")

    # ---------------------------------------------------------
    # 2. Collect costs
    # ---------------------------------------------------------

    print("\n[2] Collecting Azure costs...")

    try:
        costs = collector.collect(SUBSCRIPTION_ID)

    except Exception as e:
        print("\n❌ COST COLLECTION FAILED")
        print(f"Error: {type(e).__name__}: {e}")
        raise

    print(f"\nTotal cost records returned: {len(costs)}")

    # ---------------------------------------------------------
    # 3. Print all resource IDs containing finops-test-vm
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("SEARCHING FOR finops-test-vm")
    print("=" * 70)

    found = False

    for item in costs:

        resource_id = item.get("resource_id", "")

        if "finops-test-vm" in resource_id.lower():

            found = True

            print("\n✅ FOUND TARGET RESOURCE")

            print("-" * 70)
            print(f"resource_id:      {item.get('resource_id')}")
            print(f"monthly_cost:     {item.get('monthly_cost')}")
            print(f"currency:         {item.get('currency')}")
            print(f"cost_source:      {item.get('cost_source')}")
            print("-" * 70)

            print("\nFull record:")
            print(item)

    # ---------------------------------------------------------
    # 4. Exact resource ID comparison
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("EXACT RESOURCE ID CHECK")
    print("=" * 70)

    exact_match = None

    for item in costs:

        if item.get("resource_id") == TARGET_RESOURCE:
            exact_match = item
            break

    if exact_match:

        print("\n✅ EXACT RESOURCE ID MATCH")

        print("\nResource cost:")
        print(exact_match)

    else:

        print("\n❌ NO EXACT RESOURCE ID MATCH")

        print("\nExpected:")
        print(TARGET_RESOURCE)

        # -----------------------------------------------------
        # Show similar resource IDs for debugging
        # -----------------------------------------------------

        print("\nPossible matching resources:")

        similar = [
            item
            for item in costs
            if "finops" in item.get("resource_id", "").lower()
        ]

        if similar:

            for item in similar:
                print(
                    f"\n  {item.get('resource_id')}"
                    f"\n  cost = {item.get('monthly_cost')}"
                    f"\n  currency = {item.get('currency')}"
                )

        else:

            print("  No resource IDs containing 'finops' were returned.")

    # ---------------------------------------------------------
    # 5. Final diagnostic result
    # ---------------------------------------------------------

    print("\n" + "=" * 70)
    print("DIAGNOSTIC RESULT")
    print("=" * 70)

    if found:
        print(
            "\n✅ Cost Management returned a record "
            "containing finops-test-vm."
        )

        print(
            "\nThe next thing to verify is whether "
            "monthly_cost is > 0 and whether the resource ID "
            "matches the IDs returned by Azure Resource Graph."
        )

    else:
        print(
            "\n❌ Cost Management did NOT return "
            "finops-test-vm at resource level."
        )

        print(
            "\nThe problem is BEFORE the analyzer."
        )

        print(
            "\nInvestigate:"
            "\n  1. Cost Management query"
            "\n  2. Query grouping by ResourceId"
            "\n  3. Cost Management date range"
            "\n  4. ResourceId returned by Azure"
            "\n  5. Subscription / billing scope"
        )

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()