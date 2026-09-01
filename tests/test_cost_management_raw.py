from datetime import date, timedelta

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


def main():

    print("=" * 80)
    print("RAW AZURE COST MANAGEMENT DIAGNOSTIC")
    print("=" * 80)

    credential = AzureCliCredential()

    client = CostManagementClient(
        credential=credential
    )

    scope = f"/subscriptions/{SUBSCRIPTION_ID}"

    end_date = date.today()
    start_date = end_date - timedelta(days=30)

    print(f"\nScope      : {scope}")
    print(f"Start date : {start_date}")
    print(f"End date   : {end_date}")

    # ---------------------------------------------------------
    # Query 1
    #
    # Ask Azure for TOTAL subscription cost.
    #
    # No ResourceId grouping yet.
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("QUERY 1 — TOTAL SUBSCRIPTION COST")
    print("=" * 80)

    dataset_total = QueryDataset(
        aggregation={
            "totalCost": QueryAggregation(
                name="PreTaxCost",
                function="Sum",
            )
        },
        granularity="None",
    )

    definition_total = QueryDefinition(
        type="Usage",
        timeframe="Custom",
        time_period=QueryTimePeriod(
            from_property=start_date,
            to_property=end_date,
        ),
        dataset=dataset_total,
    )

    try:

        result = client.query.usage(
            scope=scope,
            parameters=definition_total,
        )

        print("\nColumns:")

        if result.columns:
            for column in result.columns:
                print(
                    f"  - {column.name} "
                    f"({column.type})"
                )

        print(f"\nRows: {len(result.rows or [])}")

        for row in result.rows or []:
            print("\nTOTAL COST ROW:")
            print(row)

    except Exception as e:

        print("\n❌ Query 1 failed")
        print(type(e).__name__)
        print(e)

    # ---------------------------------------------------------
    # Query 2
    #
    # Group by ResourceId.
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("QUERY 2 — COST GROUPED BY RESOURCE ID")
    print("=" * 80)

    dataset_resource = QueryDataset(
        aggregation={
            "totalCost": QueryAggregation(
                name="PreTaxCost",
                function="Sum",
            )
        },
        granularity="None",
        grouping=[
            QueryGrouping(
                name="ResourceId",
                type="Dimension",
            )
        ],
    )

    definition_resource = QueryDefinition(
        type="Usage",
        timeframe="Custom",
        time_period=QueryTimePeriod(
            from_property=start_date,
            to_property=end_date,
        ),
        dataset=dataset_resource,
    )

    try:

        result = client.query.usage(
            scope=scope,
            parameters=definition_resource,
        )

        print("\nColumns:")

        if result.columns:
            for column in result.columns:
                print(
                    f"  [{column.name}] "
                    f"({column.type})"
                )

        rows = result.rows or []

        print(f"\nRows: {len(rows)}")

        target_found = False

        for row in rows:

            print("\nROW:")
            print(row)

            row_text = str(row).lower()

            if "finops-test-vm" in row_text:

                target_found = True

                print(
                    "\n✅ FINOPS-TEST-VM FOUND!"
                )

        if not target_found:

            print(
                "\n❌ finops-test-vm was not found "
                "in the ResourceId results."
            )

    except Exception as e:

        print("\n❌ Query 2 failed")
        print(type(e).__name__)
        print(e)

    print("\n" + "=" * 80)
    print("END DIAGNOSTIC")
    print("=" * 80)


if __name__ == "__main__":
    main()

