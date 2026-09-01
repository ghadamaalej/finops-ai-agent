from app.services.retail_price_service import (
    AzureRetailPriceService
)


def main():

    pricing = AzureRetailPriceService()

    # ==========================================================
    # TEST 1 — GENERIC API
    # ==========================================================

    print("=" * 70)
    print("TEST 1 — GENERIC AZURE RETAIL PRICE API")
    print("=" * 70)

    price = pricing.get_retail_price(

        service_name="Virtual Machines",

        region="westeurope",

        arm_sku_name="Standard_D2s_v6"
    )

    if price is None:

        print(
            "❌ No price found"
        )

        return

    print("\nPRICE RESULT")
    print("-" * 70)

    for key, value in price.items():

        print(
            f"{key:20}: {value}"
        )

    print(
        "\n✅ Generic pricing API works"
    )

    # ==========================================================
    # TEST 2 — VM WRAPPER
    # ==========================================================

    print()
    print("=" * 70)
    print("TEST 2 — VM PRICE WRAPPER")
    print("=" * 70)

    vm_price = pricing.get_vm_price(

        region="westeurope",

        sku="Standard_D2s_v6"
    )

    if vm_price is None:

        print(
            "❌ VM wrapper returned no price"
        )

        return

    print(
        f"VM hourly price : "
        f"{vm_price['retail_price']}"
    )

    print(
        f"Currency        : "
        f"{vm_price['currency']}"
    )

    print(
        f"SKU             : "
        f"{vm_price['arm_sku_name']}"
    )

    print(
        f"Unit            : "
        f"{vm_price['unit_of_measure']}"
    )

    print(
        "\n✅ VM wrapper works"
    )


if __name__ == "__main__":

    main()