from app.Collectors.retail_cost_collector import RetailCostCollector
from app.Collectors.monitor_collector import MonitorCollector

def test_unknown_resource_cost_is_unavailable_not_zero():
    result = RetailCostCollector._unavailable_result(
        {"id": "/subscriptions/s/resourceGroups/g/providers/Microsoft.Kubernetes/connectedClusters/c", "name": "cluster", "type": "Microsoft.Kubernetes/connectedClusters"},
        "unsupported",
        "No retail pricing handler",
    )
    assert result["monthly_cost"] is None
    assert result["cost_status"] == "unsupported"
    assert result["cost_source"] == "none"


def test_non_vm_utilization_is_not_applicable():
    collector = object.__new__(MonitorCollector)
    result = collector.collect([{"id": "r", "name": "vault", "type": "Microsoft.KeyVault/vaults"}])
    assert result[0]["utilization_status"] == "not_applicable"
    assert result[0]["utilization_reason"] == "metric_not_supported"
    assert result[0]["cpu_average"] is None
