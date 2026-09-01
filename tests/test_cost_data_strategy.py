import sys

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
# RESOURCE COST MODEL
# ============================================================

class ResourceCost:
    """
    Cost information consumed by the FinOps analyzers.

    For Sponsorship subscriptions, the cost is estimated
    using Azure Retail Prices rather than Azure Cost Management.
    """

    def __init__(
        self,
        resource_id,
        resource_name,
        monthly_cost,
        currency,
        cost_source,
        cost_type,
        is_estimated,
    ):

        self.resource_id = resource_id
        self.resource_name = resource_name
        self.monthly_cost = monthly_cost
        self.currency = currency
        self.cost_source = cost_source
        self.cost_type = cost_type
        self.is_estimated = is_estimated

    def __repr__(self):

        return (
            "ResourceCost("
            f"resource_id='{self.resource_id}', "
            f"resource_name='{self.resource_name}', "
            f"monthly_cost={self.monthly_cost}, "
            f"currency='{self.currency}', "
            f"cost_source='{self.cost_source}', "
            f"cost_type='{self.cost_type}', "
            f"is_estimated={self.is_estimated}"
            ")"
        )

    def to_dict(self):

        return {
            "resource_id": self.resource_id,
            "resource_name": self.resource_name,
            "monthly_cost": self.monthly_cost,
            "currency": self.currency,
            "cost_source": self.cost_source,
            "cost_type": self.cost_type,
            "is_estimated": self.is_estimated,
        }


# ============================================================
# STEP 1
# DISCOVER RESOURCE
# ============================================================

def get_resource(credential):

    print("\n" + "=" * 80)
    print("STEP 1 — RESOURCE GRAPH")
    print("=" * 80)

    client = ResourceGraphClient(credential)

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

    response = client.resources(request)

    rows = list(response.data)

    print(f"\nRows returned: {len(rows)}")

    if not rows:
        raise RuntimeError(
            "Target resource was not found in Resource Graph."
        )

    resource = rows[0]

    print("\n✅ RESOURCE FOUND")

    print(f"Resource name : {resource.get('name')}")
    print(f"Resource type : {resource.get('type')}")
    print(f"Region        : {resource.get('location')}")
    print(f"VM SKU        : {resource.get('vmSize')}")
    print(f"OS type       : {resource.get('osType')}")

    return resource


# ============================================================
# STEP 2
# QUERY RETAIL PRICE
# ============================================================

def get_retail_price(
    region,
    sku,
    os_type,
):

    print("\n" + "=" * 80)
    print("STEP 2 — AZURE RETAIL PRICES")
    print("=" * 80)

    region = region.lower()

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

    print("\nQuery parameters:")

    print("Service    : Virtual Machines")
    print(f"Region     : {region}")
    print(f"ARM SKU    : {sku}")
    print("Price type : Consumption")

    print("\nQuerying Azure Retail Prices API...")

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

    if not items:
        raise RuntimeError(
            "No Azure Retail Price was found for "
            f"SKU={sku}, region={region}"
        )

    # --------------------------------------------------------
    # Select a suitable meter.
    #
    # For Linux:
    # prefer a product that is not Windows.
    #
    # For Windows:
    # prefer a Windows product.
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

        # Never select Spot pricing.
        if "spot" in product_name:
            continue

        if "spot" in meter_name:
            continue

        if normalized_os == "windows":

            if "windows" in product_name:
                selected = item
                break

        else:

            if "windows" not in product_name:
                selected = item
                break

    # Fallback
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

        raise RuntimeError(
            "Unable to select a suitable retail price meter."
        )

    hourly_price = selected.get("retailPrice")

    if hourly_price is None:
        raise RuntimeError(
            "Retail price record does not contain retailPrice."
        )

    currency = selected.get("currencyCode")
    unit = selected.get("unitOfMeasure")
    meter_name = selected.get("meterName")
    product_name = selected.get("productName")

    return {
        "hourly_price": float(hourly_price),
        "currency": currency,
        "unit": unit,
        "meter_name": meter_name,
        "product_name": product_name,
    }


# ============================================================
# STEP 3
# BUILD ResourceCost
# ============================================================

def build_resource_cost(
    resource,
    price_data,
):

    print("\n" + "=" * 80)
    print("STEP 3 — BUILD ResourceCost")
    print("=" * 80)

    hourly_price = price_data["hourly_price"]

    monthly_cost = hourly_price * MONTHLY_HOURS

    resource_cost = ResourceCost(
        resource_id=resource["id"],
        resource_name=resource["name"],
        monthly_cost=round(monthly_cost, 2),
        currency=price_data["currency"],
        cost_source="Azure Retail Prices",
        cost_type="estimated",
        is_estimated=True,
    )

    print("\n✅ ResourceCost CREATED")

    print("\nResourceCost:")
    print(resource_cost)

    return resource_cost


# ============================================================
# VALIDATION
# ============================================================

def validate_resource_cost(
    resource_cost,
    resource,
    price_data,
):

    print("\n" + "=" * 80)
    print("STEP 4 — VALIDATION")
    print("=" * 80)

    errors = []

    if resource_cost.resource_id != resource["id"]:
        errors.append(
            "resource_id does not match Resource Graph"
        )

    if resource_cost.resource_name != resource["name"]:
        errors.append(
            "resource_name does not match Resource Graph"
        )

    expected_cost = round(
        price_data["hourly_price"] * MONTHLY_HOURS,
        2,
    )

    if resource_cost.monthly_cost != expected_cost:
        errors.append(
            f"monthly_cost expected {expected_cost}, "
            f"got {resource_cost.monthly_cost}"
        )

    if resource_cost.currency != price_data["currency"]:
        errors.append(
            "currency does not match Retail Prices"
        )

    if resource_cost.cost_source != "Azure Retail Prices":
        errors.append(
            "incorrect cost_source"
        )

    if resource_cost.cost_type != "estimated":
        errors.append(
            "incorrect cost_type"
        )

    if resource_cost.is_estimated is not True:
        errors.append(
            "is_estimated must be True"
        )

    if errors:

        print("\n❌ VALIDATION FAILED")

        for error in errors:
            print(f"  - {error}")

        return False

    print("\n✅ ALL VALIDATIONS PASSED")

    return True


# ============================================================
# MAIN TEST
# ============================================================

def main():

    print("=" * 80)
    print("TEST 6 — COST DATA STRATEGY")
    print("=" * 80)

    print("\nSubscription:")
    print(SUBSCRIPTION_ID)

    print("\nTarget resource:")
    print(RESOURCE_ID)

    print("\nCost mode:")
    print("estimated")

    # --------------------------------------------------------
    # Authentication
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("AUTHENTICATION")
    print("=" * 80)

    try:

        credential = AzureCliCredential()

        token = credential.get_token(
            "https://management.azure.com/.default"
        )

        print("\n✅ Azure authentication OK")
        print(f"Token length: {len(token.token)}")

    except Exception as e:

        print("\n❌ AUTHENTICATION FAILED")
        print(type(e).__name__)
        print(e)

        sys.exit(1)

    # --------------------------------------------------------
    # Resource Graph
    # --------------------------------------------------------

    try:

        resource = get_resource(
            credential
        )

    except Exception as e:

        print("\n❌ RESOURCE DISCOVERY FAILED")
        print(type(e).__name__)
        print(e)

        sys.exit(1)

    # --------------------------------------------------------
    # Retail Price
    # --------------------------------------------------------

    try:

        price_data = get_retail_price(
            region=resource["location"],
            sku=resource["vmSize"],
            os_type=resource["osType"],
        )

    except Exception as e:

        print("\n❌ RETAIL PRICE FAILED")
        print(type(e).__name__)
        print(e)

        sys.exit(1)

    # --------------------------------------------------------
    # Display price
    # --------------------------------------------------------

    print("\n" + "=" * 80)
    print("PRICE RESULT")
    print("=" * 80)

    print(
        f"\nProduct        : "
        f"{price_data['product_name']}"
    )

    print(
        f"Meter          : "
        f"{price_data['meter_name']}"
    )

    print(
        f"Unit           : "
        f"{price_data['unit']}"
    )

    print(
        f"Hourly price   : "
        f"${price_data['hourly_price']:.6f} "
        f"{price_data['currency']}"
    )

    print(
        f"Monthly hours  : "
        f"{MONTHLY_HOURS}"
    )

    print(
        f"Monthly estimate: "
        f"${price_data['hourly_price'] * MONTHLY_HOURS:.2f} "
        f"{price_data['currency']}"
    )

    # --------------------------------------------------------
    # ResourceCost
    # --------------------------------------------------------

    try:

        resource_cost = build_resource_cost(
            resource,
            price_data,
        )

    except Exception as e:

        print("\n❌ ResourceCost CREATION FAILED")
        print(type(e).__name__)
        print(e)

        sys.exit(1)

    # --------------------------------------------------------
    # Validation
    # --------------------------------------------------------

    passed = validate_resource_cost(
        resource_cost,
        resource,
        price_data,
    )

    # --------------------------------------------------------
    # Final output
    # --------------------------------------------------------

    print("\n" + "=" * 80)

    if passed:

        print("🎯 TEST 6 PASSED")
        print("=" * 80)

        print("\nFinal cost record:")

        print(
            resource_cost.to_dict()
        )

        print("\nPipeline verified:")

        print(
            """
Resource Graph
      ↓
finops-test-vm
      ↓
SKU + Region + OS
      ↓
Azure Retail Prices
      ↓
Hourly price
      ↓
730 hours
      ↓
ResourceCost
      ↓
CostAnalyzer-ready
"""
        )

    else:

        print("❌ TEST 6 FAILED")
        print("=" * 80)

        sys.exit(1)


if __name__ == "__main__":
    main()