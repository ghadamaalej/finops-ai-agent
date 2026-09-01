from datetime import datetime, timedelta, timezone

from azure.identity import AzureCliCredential
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.costmanagement.models import (
    QueryDefinition,
    QueryDataset,
    QueryAggregation,
    QueryGrouping,
    QueryTimePeriod,
)


SUBSCRIPTION_ID = "6850d94e-3234-463d-aa51-615d3c486939"

TARGET_RESOURCE = (
    "/subscriptions/6850d94e-3234-463d-aa51-615d3c486939"
    "/resourceGroups/RG_GhadaMaalej"
    "/providers/Microsoft.Compute/virtualMachines/finops-test-vm"
)


def print_result(result, test_name):
    print("\n" + "=" * 80)
    print(f"{test_name} — RESULT")
    print("=" * 80)

    if result is None:
        print("Result: None")
        return

    print("\nColumns:")

    for index, column in enumerate(result.columns or []):
        name = column.get("name")
        column_type = column.get("type")

        print(
            f"  [{index}] {name} ({column_type})"
        )

    rows = result.rows or []

    print(f"\nRows returned: {len(rows)}")

    if not rows:
        print("\n❌ ZERO ROWS")
        return

    print("\nRows:")

    for index, row in enumerate(rows[:20]):
        print(f"  [{index}] {row}")

    if len(rows) > 20:
        print(
            f"\n... {len(rows) - 20} additional rows "
            "not displayed."
        )


def run_query(
    client,
    scope,
    query_type,
    grouping=None,
):
    """
    Execute one Cost Management query.

    query_type:
        Usage
        ActualCost

    grouping:
        None
        OR [QueryGrouping(...)]
    """

    end_date = datetime.now(
        timezone.utc
    )

    start_date = (
        end_date - timedelta(days=30)
    )

    dataset_kwargs = {
        "granularity": "None",

        "aggregation": {
            "totalCost": QueryAggregation(
                name="PreTaxCost",
                function="Sum",
            )
        },
    }

    if grouping:
        dataset_kwargs["grouping"] = grouping

    dataset = QueryDataset(
        **dataset_kwargs
    )

    definition = QueryDefinition(
        type=query_type,
        timeframe="Custom",

        time_period=QueryTimePeriod(
            from_property=start_date,
            to=end_date,
        ),

        dataset=dataset,
    )

    return client.query.usage(
        scope=scope,
        parameters=definition,
    )


def test_1_usage_total(client, scope):
    """
    TEST 1

    Usage
    +
    PreTaxCost
    +
    NO grouping

    Question:

    Does the subscription have ANY
    Cost Management data?
    """

    print("\n")
    print("#" * 80)
    print("TEST 1 — USAGE + TOTAL SUBSCRIPTION COST")
    print("#" * 80)

    print(
        "\nConfiguration:"
        "\n  Type      : Usage"
        "\n  Grouping  : None"
        "\n  Period    : Last 30 days"
        "\n  Aggregate : PreTaxCost / Sum"
    )

    try:

        result = run_query(
            client=client,
            scope=scope,
            query_type="Usage",
            grouping=None,
        )

        print_result(
            result,
            "TEST 1"
        )

        return result

    except Exception as exc:

        print("\n❌ TEST 1 FAILED")
        print(
            f"Exception: {type(exc).__name__}"
        )
        print(f"Message  : {exc}")

        return None


def test_2_usage_resource(client, scope):
    """
    TEST 2

    Usage
    +
    PreTaxCost
    +
    ResourceId grouping

    Question:

    Does Azure have resource-level
    cost attribution?
    """

    print("\n")
    print("#" * 80)
    print("TEST 2 — USAGE + RESOURCE ID")
    print("#" * 80)

    print(
        "\nConfiguration:"
        "\n  Type      : Usage"
        "\n  Grouping  : ResourceId"
        "\n  Period    : Last 30 days"
        "\n  Aggregate : PreTaxCost / Sum"
    )

    grouping = [
        QueryGrouping(
            name="ResourceId",
            type="Dimension",
        )
    ]

    try:

        result = run_query(
            client=client,
            scope=scope,
            query_type="Usage",
            grouping=grouping,
        )

        print_result(
            result,
            "TEST 2"
        )

        rows = result.rows or []

        target_found = False

        target_lower = TARGET_RESOURCE.lower()

        for row in rows:

            row_text = " ".join(
                str(value)
                for value in row
            ).lower()

            if (
                "finops-test-vm"
                in row_text
            ):
                target_found = True

            if target_lower in row_text:
                target_found = True

        print("\nTarget resource check:")

        print(
            f"  Target: {TARGET_RESOURCE}"
        )

        if target_found:

            print(
                "\n✅ FINOPS-TEST-VM FOUND"
            )

        else:

            print(
                "\n❌ FINOPS-TEST-VM NOT FOUND"
            )

        return result

    except Exception as exc:

        print("\n❌ TEST 2 FAILED")
        print(
            f"Exception: {type(exc).__name__}"
        )
        print(f"Message  : {exc}")

        return None


def test_3_actualcost_resource(client, scope):
    """
    TEST 3

    ActualCost
    +
    PreTaxCost
    +
    ResourceId grouping

    Question:

    Does ActualCost behave differently
    from Usage?
    """

    print("\n")
    print("#" * 80)
    print("TEST 3 — ACTUAL COST + RESOURCE ID")
    print("#" * 80)

    print(
        "\nConfiguration:"
        "\n  Type      : ActualCost"
        "\n  Grouping  : ResourceId"
        "\n  Period    : Last 30 days"
        "\n  Aggregate : PreTaxCost / Sum"
    )

    grouping = [
        QueryGrouping(
            name="ResourceId",
            type="Dimension",
        )
    ]

    try:

        result = run_query(
            client=client,
            scope=scope,
            query_type="ActualCost",
            grouping=grouping,
        )

        print_result(
            result,
            "TEST 3"
        )

        rows = result.rows or []

        target_found = False

        target_lower = TARGET_RESOURCE.lower()

        for row in rows:

            row_text = " ".join(
                str(value)
                for value in row
            ).lower()

            if (
                "finops-test-vm"
                in row_text
            ):
                target_found = True

            if target_lower in row_text:
                target_found = True

        print("\nTarget resource check:")

        if target_found:

            print(
                "\n✅ FINOPS-TEST-VM FOUND"
            )

        else:

            print(
                "\n❌ FINOPS-TEST-VM NOT FOUND"
            )

        return result

    except Exception as exc:

        print("\n❌ TEST 3 FAILED")
        print(
            f"Exception: {type(exc).__name__}"
        )
        print(f"Message  : {exc}")

        return None


def main():

    print("=" * 80)
    print("RAW AZURE COST MANAGEMENT — TESTS 1 / 2 / 3")
    print("=" * 80)

    print(
        f"\nSubscription:"
        f"\n  {SUBSCRIPTION_ID}"
    )

    print(
        f"\nTarget resource:"
        f"\n  {TARGET_RESOURCE}"
    )

    credential = AzureCliCredential(
        process_timeout=30
    )

    print("\nTesting Azure authentication...")

    try:

        token = credential.get_token(
            "https://management.azure.com/.default"
        )

        print(
            "✅ Azure authentication OK"
        )

        print(
            f"Token length: {len(token.token)}"
        )

    except Exception as exc:

        print(
            "\n❌ Azure authentication FAILED"
        )

        print(
            f"{type(exc).__name__}: {exc}"
        )

        return

    client = CostManagementClient(
        credential=credential
    )

    scope = (
        f"/subscriptions/{SUBSCRIPTION_ID}"
    )

    # ======================================================
    # TEST 1
    # ======================================================

    result_1 = test_1_usage_total(
        client,
        scope,
    )

    # ======================================================
    # TEST 2
    # ======================================================

    result_2 = test_2_usage_resource(
        client,
        scope,
    )

    # ======================================================
    # TEST 3
    # ======================================================

    result_3 = test_3_actualcost_resource(
        client,
        scope,
    )

    # ======================================================
    # FINAL DIAGNOSIS
    # ======================================================

    print("\n")
    print("=" * 80)
    print("FINAL DIAGNOSIS")
    print("=" * 80)

    rows_1 = (
        len(result_1.rows or [])
        if result_1
        else 0
    )

    rows_2 = (
        len(result_2.rows or [])
        if result_2
        else 0
    )

    rows_3 = (
        len(result_3.rows or [])
        if result_3
        else 0
    )

    print(
        f"\nTEST 1 — Usage + Total:"
        f"       {rows_1} rows"
    )

    print(
        f"TEST 2 — Usage + ResourceId:"
        f" {rows_2} rows"
    )

    print(
        f"TEST 3 — ActualCost + ResourceId:"
        f" {rows_3} rows"
    )

    print("\nInterpretation:")

    if rows_1 > 0 and rows_2 > 0:

        print(
            "\n✅ COST DATA EXISTS"
        )

        print(
            "✅ RESOURCE-LEVEL COST DATA EXISTS"
        )

        print(
            "\nThe Cost Management API is working."
        )

        print(
            "The next problem is inside the "
            "CostCollector parsing/mapping."
        )

    elif rows_1 > 0 and rows_2 == 0:

        print(
            "\n⚠️ SUBSCRIPTION COST EXISTS"
        )

        print(
            "❌ RESOURCE-LEVEL COST IS EMPTY"
        )

        print(
            "\nThis means Azure can return "
            "subscription-level billing data, "
            "but ResourceId attribution is "
            "not returning records."
        )

    elif rows_1 == 0:

        print(
            "\n❌ NO SUBSCRIPTION COST DATA"
        )

        print(
            "\nEven the simplest Usage query "
            "returned zero rows."
        )

        print(
            "Investigate billing scope, "
            "cost-data availability, or "
            "billing permissions."
        )

    if rows_3 > 0:

        print(
            "\nℹ️ ActualCost returned resource "
            "records."
        )

    else:

        print(
            "\nℹ️ ActualCost + ResourceId "
            "returned zero rows."
        )

    print("\n" + "=" * 80)
    print("END OF TESTS 1 / 2 / 3")
    print("=" * 80)


if __name__ == "__main__":
    main()

