import pytest

from app.Collectors.retail_cost_collector import RetailCostCollector


class FakeRetailPricing:
    def __init__(self):
        self.calls = []

    def get_retail_price(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "retail_price": 0.10,
            "unit_of_measure": "1 Hour",
            "currency": "USD",
            "meter_name": "Test meter",
            "sku_name": kwargs.get("sku_name") or "Test SKU",
            "product_name": "Test product",
            "service_family": "Test service",
        }


RESOURCE_TYPES = [
    "microsoft.network/publicipaddresses",
    "microsoft.containerservice/managedclusters",
    "microsoft.web/serverfarms",
    "microsoft.web/sites",
    "microsoft.sql/servers/databases",
    "microsoft.sql/servers",
    "microsoft.storage/storageaccounts",
    "microsoft.containerregistry/registries",
    "microsoft.keyvault/vaults",
    "microsoft.network/loadbalancers",
    "microsoft.network/natgateways",
    "microsoft.network/virtualnetworkgateways",
    "microsoft.network/virtualnetworks",
    "microsoft.network/networksecuritygroups",
    "microsoft.operationalinsights/workspaces",
    "microsoft.insights/datacollectionendpoints",
    "microsoft.insights/datacollectionrules",
    "microsoft.recoveryservices/vaults",
    "microsoft.dataprotection/backupvaults",
    "microsoft.cognitiveservices/accounts",
    "microsoft.compute/snapshots",
]


@pytest.mark.parametrize("resource_type", RESOURCE_TYPES)
def test_supported_resource_handler_returns_provenance_and_no_missing_strategy_warning(resource_type, capsys):
    collector = RetailCostCollector()
    collector.pricing = FakeRetailPricing()
    resource = {
        "id": f"/subscriptions/sub/resourceGroups/rg/providers/{resource_type}/resource",
        "name": "resource",
        "type": resource_type,
        "location": "westeurope",
        "sku": "Standard",
        "sku_name": "Standard",
        "capacity_gb": 10,
        "ingestion_gb": 10,
        "quantity": 10,
    }

    costs = collector.collect([resource])

    output = capsys.readouterr().out
    assert "No pricing strategy" not in output
    assert len(costs) == 1
    assert costs[0]["cost_source"] == "Azure Retail Prices"
    assert costs[0]["cost_type"] == "estimated"
    assert costs[0]["is_estimated"] is True
    assert "pricing_method" in costs[0]


def test_public_ip_uses_virtual_network_retail_service():
    collector = RetailCostCollector()
    pricing = FakeRetailPricing()
    collector.pricing = pricing

    collector.collect([{
        "id": "/subscriptions/sub/publicIp",
        "name": "publicIp",
        "type": "microsoft.network/publicIPAddresses",
        "location": "westeurope",
        "sku_name": "Standard",
    }])

    assert pricing.calls[0]["service_name"] == "Virtual Network"
    assert pricing.calls[0]["sku_name"] == "Standard IP"


def test_usage_meter_without_quantity_is_explicitly_zero_cost():
    collector = RetailCostCollector()
    collector.pricing = FakeRetailPricing()

    costs = collector.collect([{
        "id": "/subscriptions/sub/workspace",
        "name": "workspace",
        "type": "microsoft.operationalinsights/workspaces",
        "location": "westeurope",
        "sku_name": "PerGB2018",
    }])

    assert costs[0]["monthly_cost"] == 0.0
    assert costs[0]["pricing_method"].endswith("quantity_unavailable")
    assert costs[0]["pricing_warning"] == "Usage quantity unavailable; no cost estimated"


def test_unknown_resource_is_explicitly_zero_cost(capsys):
    collector = RetailCostCollector()

    costs = collector.collect([{
        "id": "/subscriptions/sub/unknown",
        "name": "unknown",
        "type": "microsoft.example/unknownresources",
        "location": "westeurope",
    }])

    assert "No pricing strategy" not in capsys.readouterr().out
    assert costs[0]["monthly_cost"] == 0.0
    assert costs[0]["pricing_method"] == "zero_cost_non_billable"
