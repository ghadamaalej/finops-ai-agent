from app.services.retail_price_service import (
    AzureRetailPriceService
)


def print_price(
    title: str,
    price: dict | None
):

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)

    if price is None:

        print(
            "❌ No price found"
        )

        return False

    for key, value in price.items():

        print(
            f"{key:20}: {value}"
        )

    return True


def main():

    pricing = (
        AzureRetailPriceService()
    )

    # ==========================================================
    # TEST 1 — GENERIC VM API
    # ==========================================================

    vm_price = (
        pricing.get_retail_price(

            service_name="Virtual Machines",

            region="westeurope",

            arm_sku_name="Standard_D2s_v6"
        )
    )

    if not print_price(
        "TEST 1 — GENERIC VM RETAIL PRICE",
        vm_price
    ):

        return

    print(
        "\n✅ Generic VM pricing works"
    )

    # ==========================================================
    # TEST 2 — VM WRAPPER
    # ==========================================================

    vm_price = (
        pricing.get_vm_price(

            region="westeurope",

            sku="Standard_D2s_v6"
        )
    )

    if not print_price(
        "TEST 2 — VM PRICE WRAPPER",
        vm_price
    ):

        return

    print(
        "\n✅ VM wrapper works"
    )

    # ==========================================================
    # TEST 3 — PREMIUM SSD
    # ==========================================================

    disk_price = (
        pricing.get_managed_disk_price(

            region="westeurope",

            disk_sku="Premium_LRS",

            disk_size_gb=128
        )
    )

    if not print_price(
        "TEST 3 — PREMIUM SSD 128 GB",
        disk_price
    ):

        return

    print(
        "\n✅ Premium Managed Disk pricing works"
    )

    # ==========================================================
    # TEST 4 — PREMIUM SSD 512 GB
    # ==========================================================

    disk_price = (
        pricing.get_managed_disk_price(

            region="westeurope",

            disk_sku="Premium_LRS",

            disk_size_gb=512
        )
    )

    if not print_price(
        "TEST 4 — PREMIUM SSD 512 GB",
        disk_price
    ):

        return

    print(
        "\n✅ Premium 512 GB pricing works"
    )

    # ==========================================================
    # TEST 5 — STANDARD SSD
    # ==========================================================

    disk_price = (
        pricing.get_managed_disk_price(

            region="westeurope",

            disk_sku="StandardSSD_LRS",

            disk_size_gb=128
        )
    )

    if not print_price(
        "TEST 5 — STANDARD SSD 128 GB",
        disk_price
    ):

        return

    print(
        "\n✅ Standard SSD pricing works"
    )

    # ==========================================================
    # TEST 6 — STANDARD HDD
    # ==========================================================

    disk_price = (
        pricing.get_managed_disk_price(

            region="westeurope",

            disk_sku="Standard_LRS",

            disk_size_gb=128
        )
    )

    if not print_price(
        "TEST 6 — STANDARD HDD 128 GB",
        disk_price
    ):

        return

    print(
        "\n✅ Standard HDD pricing works"
    )

    print()
    print("=" * 70)
    print(
        "ALL MANAGED DISK PRICING TESTS PASSED"
    )
    print("=" * 70)


if __name__ == "__main__":

    main()