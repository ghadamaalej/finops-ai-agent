from app.Collectors.monitor_collector import MonitorCollector
from datetime import datetime, timezone
from app.agent.analyzers.cost_analyzer import CostAnalyzer
from app.agent.analyzers.unattached_disk_analyzer import unattached_disk_analyzer
from app.models.azure import AzureContext, AzureResource, PerformanceMetric, ResourceCost
from app.services.resource_evidence import canonical_evidence, fallback_action

def resource(resource_type, name):
    return {
        "id": f"/subscriptions/sub/resourceGroups/rg/providers/{resource_type}/{name}",
        "name": name,
        "type": resource_type,
        "location": "westeurope",
        "resource_group": "rg",
        "subscription_id": "sub",
        "sku": "Standard",
        "configuration": {"sku": "Standard"},
    }


def test_metric_catalog_covers_requested_resource_types():
    expected = {
        "microsoft.compute/virtualmachines",
        "microsoft.compute/disks",
        "microsoft.containerregistry/registries",
        "microsoft.web/sites",
        "microsoft.sql/servers/databases",
    }
    assert expected.issubset(MonitorCollector.METRIC_CATALOG)
    assert "Percentage CPU" in MonitorCollector.METRIC_CATALOG["microsoft.compute/virtualmachines"]
    assert "MemoryWorkingSet" in MonitorCollector.METRIC_CATALOG["microsoft.web/sites"]
    assert "Composite Disk Read Operations/sec" in MonitorCollector.METRIC_CATALOG["microsoft.compute/disks"]
    assert "StorageUsed" in MonitorCollector.METRIC_CATALOG["microsoft.containerregistry/registries"]
    assert "dtu_consumption_percent" in MonitorCollector.METRIC_CATALOG["microsoft.sql/servers/databases"]


def test_collect_queries_the_resource_specific_monitor_catalog(monkeypatch):
    calls = []
    class Client:
        def query_resources(self, **kwargs):
            calls.append(kwargs)
            return []
    collector = MonitorCollector(credential=object())
    monkeypatch.setattr(collector, "_get_client", lambda region: Client())
    resources = [
        resource("microsoft.compute/virtualmachines", "vm"),
        resource("microsoft.compute/disks", "disk"),
        resource("microsoft.containerregistry/registries", "registry"),
        resource("microsoft.web/sites", "app"),
        resource("microsoft.sql/servers/databases", "db"),
        resource("microsoft.network/publicipaddresses", "pip"),
    ]
    metrics = collector.collect(resources)
    assert len(calls) == sum(len(MonitorCollector.METRIC_CATALOG[item["type"]]) for item in resources[:-1])
    assert all(call["resource_ids"] == [next(item for item in resources if item["id"] == call["resource_ids"][0])["id"]] for call in calls)
    assert all(len(call["metric_names"]) == 1 for call in calls)
    assert all(item["resource_id"] in {resource["id"] for resource in resources} for item in metrics)
    public_ip = next(item for item in metrics if item["resource_type"] == "microsoft.network/publicipaddresses")
    assert public_ip["metric_available"] is False
    assert public_ip["utilization_reason"].startswith("Public IP utilization")


def test_canonical_evidence_joins_cost_metrics_and_configuration_by_resource_id():
    disk = resource("microsoft.compute/disks", "disk_os_ulysse_vm")
    evidence = canonical_evidence(
        disk,
        {"resource_id": disk["id"].upper(), "monthly_cost": 1.18, "cost_source": "Azure Retail Prices", "cost_type": "estimated", "is_estimated": True, "cost_data_available": True},
        {"resource_id": disk["id"].upper(), "metric_available": False, "metric_names": ["Composite Disk Read Operations/Sec"], "metric_unavailable_reason": "azure_monitor_returned_no_datapoints"},
    )
    assert evidence["resource_id"] == disk["id"]
    assert evidence["cost"] == 1.18
    assert evidence["cost_data_available"] is True
    assert evidence["configuration_available"] is True
    assert evidence["metric_available"] is False
    assert evidence["metric_unavailable_reason"] == "azure_monitor_returned_no_datapoints"


def test_public_ip_records_explicit_configuration_only_metric_reason():
    item = resource("microsoft.network/publicipaddresses", "pip")
    metric = MonitorCollector._unavailable_metric(item, MonitorCollector.CONFIG_ONLY_TYPES[item["type"]])
    assert metric["resource_id"] == item["id"]
    assert metric["metric_available"] is False
    assert metric["utilization_status"] == "not_applicable"


def test_non_vm_metric_cannot_trigger_vm_rightsizing():
    disk = AzureResource(**resource("microsoft.compute/disks", "disk"))
    cost = ResourceCost(resource_id=disk.id, monthly_cost=20, cost_data_available=True)
    metric = PerformanceMetric(resource_id=disk.id, resource_type=disk.type, metric_available=True, values={"Composite Disk Read Operations/Sec": 0})
    intelligence = type("Intelligence", (), {"resources": [disk], "resource_costs": [cost], "metrics": [metric]})()
    assert CostAnalyzer().analyze(intelligence) == []


def test_resource_type_fallbacks_never_apply_vm_cpu_ram_to_disks():
    assert "CPU/memory" in fallback_action("microsoft.compute/virtualmachines")
    assert fallback_action("microsoft.compute/disks") == "Collect disk IOPS/throughput and attachment-state evidence before quantifying savings."
    assert "storage, transaction" in fallback_action("microsoft.containerregistry/registries")
    assert "App Service" in fallback_action("microsoft.web/sites")
    assert "SQL CPU/DTU/vCore" in fallback_action("microsoft.sql/servers/databases")
    assert "Public IP association" in fallback_action("microsoft.network/publicipaddresses")


def test_all_supported_types_keep_resource_id_linked_metric_requests(monkeypatch):
    calls = []
    class Client:
        def query_resources(self, **kwargs):
            calls.append(kwargs)
            return []
    collector = MonitorCollector(credential=object())
    monkeypatch.setattr(collector, "_get_client", lambda region: Client())
    types = [
        "microsoft.compute/virtualmachines", "microsoft.compute/disks",
        "microsoft.containerregistry/registries", "microsoft.web/sites",
        "microsoft.sql/servers/databases", "microsoft.network/publicipaddresses",
    ]
    items = [resource(resource_type, resource_type.rsplit("/", 1)[-1]) for resource_type in types]
    metrics = collector.collect(items)
    assert {item["resource_id"] for item in metrics} == {item["id"] for item in items}
    disk_call = next(call for call in calls if "/disks/" in call["resource_ids"][0])
    assert "Percentage CPU" not in disk_call["metric_names"]
    assert disk_call["metric_names"] == ["Composite Disk Read Operations/sec"]


def test_disk_preserves_partial_monitor_results_and_configuration(monkeypatch):
    disk = resource("microsoft.compute/disks", "disk_os_ulysse_vm")
    disk["configuration"].update({"managed_by": "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/ulysse-vm", "disk_state": "Attached", "disk_size_gb": 10})

    class Client:
        def query_resources(self, **kwargs):
            metric_name = kwargs["metric_names"][0]
            if metric_name == "DiskPaidBurstIOPS":
                raise RuntimeError("Metric not supported for this disk")
            point = type("Point", (), {"average": 3.0, "total": None})()
            series = type("Series", (), {"data": [point]})()
            metric = type("Metric", (), {"name": metric_name, "timeseries": [series]})()
            return [type("Result", (), {"metrics": [metric]})()]

    collector = MonitorCollector(credential=object())
    monkeypatch.setattr(collector, "_get_client", lambda region: Client())
    result = collector.collect([disk])[0]

    assert result["metric_available"] is True
    assert result["metrics"]["Composite Disk Read Operations/sec"]["available"] is True
    assert result["metrics"]["DiskPaidBurstIOPS"]["available"] is False
    assert "DiskPaidBurstIOPS" in result["metric_errors"]
    assert result["configuration"]["managed_by"].endswith("/ulysse-vm")
    assert result["configuration"]["disk_state"] == "Attached"
    assert result["configuration"]["disk_size_gb"] == 10


def test_attached_active_disk_is_not_a_deletion_candidate():
    disk = resource("microsoft.compute/disks", "disk_os_ulysse_vm")
    disk["configuration"].update({"managed_by": "/subscriptions/sub/providers/Microsoft.Compute/virtualMachines/vm-ulysse", "disk_state": "Attached", "disk_size_gb": 64})
    context = AzureContext(
        subscription_id="sub",
        collected_at=datetime.now(timezone.utc),
        resources=[AzureResource(**disk)],
        resource_costs=[ResourceCost(resource_id=disk["id"], monthly_cost=1.18, cost_data_available=True)],
        metrics=[PerformanceMetric(resource_id=disk["id"], resource_type=disk["type"], metric_available=True, values={"Composite Disk Read Operations/sec": 2.0977, "Composite Disk Write Operations/sec": 3.8907})],
    )
    result = unattached_disk_analyzer({"finops_context": context})
    assert result["unattached_disk_issues"] == []
