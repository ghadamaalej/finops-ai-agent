import sys
from pathlib import Path

import requests

from azure.identity import AzureCliCredential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest


# ============================================================
# CONFIGURATION
# ============================================================

SUBSCRIPTION_ID = "6850d94e-3234-463d-aa51-615d3c486939"

RESOURCE_ID = (
    "/subscriptions/6850d94e-3234-463d-aa51-615d3c486939"
    "/resourceGroups/RG_GhadaMaalej"
    "/providers/Microsoft.Compute/virtualMachines/finops-test-vm"
)

RETAIL_PRICES_URL = "https://prices.azure.com/api/retail/prices"

MONTHLY_HOURS = 730


# ============================================================
# TEST 5
# ============================================================

def main():

    print("=" * 80)
    print("TEST 5 — AZURE RETAIL PRICE")
    print("=" * 80)

    print("\nSubscription:")
    print(SUBSCRIPTION_ID)

    print("\nTarget resource:")
    print(RESOURCE_ID)

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("STEP 1 — AZURE AUTHENTICATION")
    print("=" * 80)

    try:

        credential = AzureCliCredential()

        token = credential.get_token(
            "https://management.azure.com/.default"
        )

        print("✅ Azure authentication OK")
        print(f"Token length: {len(token.token)}")

    except Exception as e:

        print("❌ Azure authentication failed")
        print(type(e).__name__)
        print(e)

        sys.exit(1)

    # --------------------------------------------------------
    # Resource Graph
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("STEP 2 — RESOURCE GRAPH")
    print("=" * 80)

    print("\nQuerying Azure Resource Graph...")

    try:

        resource_graph = ResourceGraphClient(
            credential
        )

        query = f"""
        Resources
        | where id =~ '{RESOURCE_ID}'
        | project
            id,
            name,
            type,
            location,
            vmSize = tostring(properties.hardwareProfile.vmSize),
            osType = tostring(properties.storageProfile.osDisk.osType)
        """

        request = QueryRequest(
            subscriptions=[SUBSCRIPTION_ID],
            query=query,
        )

        response = resource_graph.resources(request)

        rows = list(response.data)

        print(f"\nRows returned: {len(rows)}")

        if not rows:

            print("\n❌ TARGET VM NOT FOUND")

            sys.exit(1)

        vm = rows[0]

        resource_id = vm.get("id")
        resource_name = vm.get("name")
        resource_type = vm.get("type")
        region = vm.get("location")
        sku = vm.get("vmSize")
        os_type = vm.get("osType")

        print("\n✅ RESOURCE FOUND")

        print(f"\nResource name : {resource_name}")
        print(f"Resource type : {resource_type}")
        print(f"Region        : {region}")
        print(f"VM SKU        : {sku}")
        print(f"OS type       : {os_type}")

    except Exception as e:

        print("\n❌ RESOURCE GRAPH FAILED")
        print(type(e).__name__)
        print(e)

        sys.exit(1)

    # --------------------------------------------------------
    # Validate resource information
    # --------------------------------------------------------

    if not region:

        print("\n❌ Region is missing")
        sys.exit(1)

    if not sku:

        print("\n❌ VM SKU is missing")
        sys.exit(1)

    # Azure Resource Graph normally returns ARM region names
    # such as "westeurope".
    region = region.lower()

    # --------------------------------------------------------
    # Retail Prices query
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("STEP 3 — AZURE RETAIL PRICES API")
    print("=" * 80)

    print("\nQuery parameters:")

    print(f"Service       : Virtual Machines")
    print(f"Region        : {region}")
    print(f"ARM SKU       : {sku}")
    print(f"Price type    : Consumption")

    # Exact region + SKU + consumption price.
    #
    # We intentionally do NOT query only serviceName because
    # that could return thousands of pricing records.

    filter_expression = (
        "serviceName eq 'Virtual Machines' "
        f"and armRegionName eq '{region}' "
        f"and armSkuName eq '{sku}' "
        "and priceType eq 'Consumption'"
    )

    params = {
        "api-version": "2023-01-01-preview",
        "$filter": filter_expression,
    }

    print("\nQuerying Azure Retail Prices API...")

    try:

        response = requests.get(
            RETAIL_PRICES_URL,
            params=params,
            timeout=30,
        )

        print(f"\nHTTP status: {response.status_code}")

        response.raise_for_status()

        data = response.json()

        items = data.get("Items", [])

        print(f"Price records returned: {len(items)}")

    except requests.RequestException as e:

        print("\n❌ RETAIL PRICES API FAILED")
        print(type(e).__name__)
        print(e)

        sys.exit(1)

    except Exception as e:

        print("\n❌ RESPONSE PARSING FAILED")
        print(type(e).__name__)
        print(e)

        sys.exit(1)

    # --------------------------------------------------------
    # No price found
    # --------------------------------------------------------

    if not items:

        print("\n❌ NO RETAIL PRICE FOUND")

        print("\nFilter used:")
        print(filter_expression)

        print(
            "\nThis means Azure Retail Prices did not return "
            "a Consumption meter for this exact region/SKU."
        )

        sys.exit(1)

    # --------------------------------------------------------
    # Select appropriate price
    # --------------------------------------------------------

    selected = None

    normalized_os = (os_type or "").lower()

    for item in items:

        product_name = (
            item.get("productName") or ""
        ).lower()

        meter_name = (
            item.get("meterName") or ""
        ).lower()

        # Avoid Spot pricing.
        if "spot" in product_name or "spot" in meter_name:
            continue

        # Windows VMs normally have Windows in product name.
        if normalized_os == "windows":

            if "windows" in product_name:

                selected = item
                break

        else:

            # Prefer a non-Windows standard consumption meter.
            if "windows" not in product_name:

                selected = item
                break

    # If the OS-specific selection did not work,
    # use the first non-Spot record.
    if selected is None:

        for item in items:

            product_name = (
                item.get("productName") or ""
            ).lower()

            meter_name = (
                item.get("meterName") or ""
            ).lower()

            if (
                "spot" not in product_name
                and "spot" not in meter_name
            ):

                selected = item
                break

    if selected is None:

        print("\n❌ Could not select a suitable price meter")

        print("\nReturned records:")

        for item in items:

            print(
                f"- {item.get('productName')} | "
                f"{item.get('meterName')} | "
                f"{item.get('retailPrice')}"
            )

        sys.exit(1)

    # --------------------------------------------------------
    # Extract price
    # --------------------------------------------------------

    hourly_price = selected.get("retailPrice")
    currency = selected.get("currencyCode")
    unit = selected.get("unitOfMeasure")
    meter_name = selected.get("meterName")
    product_name = selected.get("productName")

    if hourly_price is None:

        print("\n❌ Retail price is missing")

        sys.exit(1)

    monthly_cost = float(hourly_price) * MONTHLY_HOURS

    # --------------------------------------------------------
    # Final result
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("RETAIL PRICE RESULT")
    print("=" * 80)

    print(f"\nResource:")
    print(f"  {resource_name}")

    print(f"\nResource ID:")
    print(f"  {resource_id}")

    print(f"\nType:")
    print(f"  {resource_type}")

    print(f"\nRegion:")
    print(f"  {region}")

    print(f"\nSKU:")
    print(f"  {sku}")

    print(f"\nOS:")
    print(f"  {os_type}")

    print(f"\nProduct:")
    print(f"  {product_name}")

    print(f"\nMeter:")
    print(f"  {meter_name}")

    print(f"\nUnit:")
    print(f"  {unit}")

    print(f"\nHourly price:")
    print(f"  ${float(hourly_price):.6f} {currency}")

    print(f"\nEstimated monthly hours:")
    print(f"  {MONTHLY_HOURS}")

    print(f"\nEstimated monthly cost:")
    print(f"  ${monthly_cost:.2f} {currency}")

    print(f"\nCost source:")
    print("  Azure Retail Prices")

    print(f"\nCost type:")
    print("  estimated")

    print(f"\nIs estimated:")
    print("  True")

    print("\n" + "=" * 80)
    print("🎯 TEST 5 PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()