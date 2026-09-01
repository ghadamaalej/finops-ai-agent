from app.Collectors.retail_cost_collector import RetailCostCollector
from app.services.retail_price_service import AzureRetailPriceService


class FakeResponse:
    def __init__(self, status_code=200, items=None, headers=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._items = items or []

    def json(self):
        return {"Items": self._items}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise AssertionError(f"unexpected HTTP status {self.status_code}")


class CountingSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, url, params=None, timeout=None):
        self.calls.append((url, params, timeout))
        return self.responses.pop(0)


def retail_item():
    return {
        "type": "Consumption",
        "retailPrice": 0.01,
        "unitOfMeasure": "1/GB/Month",
        "currencyCode": "USD",
        "meterName": "Snapshot Capacity",
        "skuName": "Standard_ZRS",
        "productName": "Managed Disks",
        "serviceName": "Storage",
        "armRegionName": "northeurope",
    }


def test_twenty_identical_snapshots_generate_one_retail_api_request():
    pricing = AzureRetailPriceService()
    session = CountingSession([FakeResponse(items=[retail_item()])])
    pricing.session = session
    collector = RetailCostCollector()
    collector.pricing = pricing
    resources = [
        {
            "id": f"/subscriptions/sub/snapshots/snapshot-{index}",
            "name": f"snapshot-{index}",
            "type": "microsoft.compute/snapshots",
            "location": "northeurope",
            "sku_name": "Standard_ZRS",
            "disk_size_gb": 100,
        }
        for index in range(20)
    ]

    costs = collector.collect(resources)

    assert len(costs) == 20
    assert len(session.calls) == 1
    assert all(cost["cost_source"] == "Azure Retail Prices" for cost in costs)
    assert all(cost["cost_type"] == "estimated" for cost in costs)
    assert all(cost["is_estimated"] is True for cost in costs)


def test_retail_api_retries_429_using_retry_after(monkeypatch):
    pricing = AzureRetailPriceService()
    session = CountingSession([
        FakeResponse(status_code=429, headers={"Retry-After": "7"}),
        FakeResponse(items=[retail_item()]),
    ])
    pricing.session = session
    sleeps = []
    monkeypatch.setattr(pricing, "_sleep_before_retry", lambda attempt, retry_after: sleeps.append((attempt, retry_after)))

    result = pricing.get_retail_price(
        service_name="Storage",
        region="northeurope",
        sku_name="Standard_ZRS",
    )

    assert result is not None
    assert len(session.calls) == 2
    assert sleeps == [(0, "7")]


def test_confirmed_missing_price_is_cached():
    pricing = AzureRetailPriceService()
    session = CountingSession([FakeResponse(items=[])])
    pricing.session = session

    assert pricing.get_retail_price("Storage", region="northeurope", sku_name="Missing") is None
    assert pricing.get_retail_price("Storage", region="northeurope", sku_name="Missing") is None
    assert len(session.calls) == 1
