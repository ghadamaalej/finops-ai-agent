from app.services.retail_price_service import (
    AzureRetailPriceService
)


def test_vm_candidate_rejects_low_priority():

    service = AzureRetailPriceService()

    item = {
        "armSkuName": "Standard_B2s_v2",
        "skuName": "B2s v2 Low Priority",
        "meterName": "B2s v2 Low Priority",
        "productName": "Virtual Machines",
        "retailPrice": 0.01,
    }

    reason = (
        service._validate_vm_price_candidate(
            item=item,
            requested_sku="Standard_B2s_v2",
            os_type="Linux",
        )
    )

    assert reason == (
        "Low Priority pricing"
    )


def test_vm_candidate_rejects_spot():

    service = AzureRetailPriceService()

    item = {
        "armSkuName": "Standard_B2s_v2",
        "skuName": "B2s v2",
        "meterName": "B2s v2 Spot",
        "productName": "Virtual Machines",
        "retailPrice": 0.01,
    }

    reason = (
        service._validate_vm_price_candidate(
            item=item,
            requested_sku="Standard_B2s_v2",
            os_type="Linux",
        )
    )

    assert reason == (
        "Spot pricing"
    )


def test_vm_candidate_accepts_standard():

    service = AzureRetailPriceService()

    item = {
        "armSkuName": "Standard_B2s_v2",
        "skuName": "B2s v2",
        "meterName": "B2s v2",
        "productName": "Virtual Machines",
        "retailPrice": 0.096,
        "isPrimaryMeterRegion": True,
    }

    reason = (
        service._validate_vm_price_candidate(
            item=item,
            requested_sku="Standard_B2s_v2",
            os_type="Linux",
        )
    )

    assert reason is None