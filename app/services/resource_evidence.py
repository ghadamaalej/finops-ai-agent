"Canonical resource evidence helpers used by collection and response projections."""

import logging
from typing import Any
logger = logging.getLogger(__name__)

RESOURCE_CAPABILITIES = {
    "microsoft.compute/virtualmachines": {
        "metrics": ["CPU", "memory", "network", "disk IOPS"],
        "fallback": "Collect CPU/memory/utilization metrics and VM configuration evidence before quantifying savings.",
    },
        "microsoft.compute/disks": {
        "metrics": ["disk IOPS", "throughput", "attachment state"],
        "supported_metrics": ["Composite Disk Read Operations/sec", "Composite Disk Write Operations/sec", "Composite Disk Read Bytes/sec", "Composite Disk Write Bytes/sec", "DiskPaidBurstIOPS"],
        "unsupported_metrics": ["latency"],
        "fallback": "Collect disk IOPS/throughput and attachment-state evidence before quantifying savings.",
    },
    "microsoft.containerregistry/registries": {
        "metrics": ["storage", "pull transactions", "push transactions"],
        "fallback": "Collect container registry storage, transaction, and usage evidence before quantifying savings.",
    },
    "microsoft.web/sites": {
        "metrics": ["CPU", "memory", "requests", "HTTP errors"],
        "fallback": "Collect App Service CPU/memory/request utilization and plan configuration evidence before quantifying savings.",
    },
    "microsoft.sql/servers/databases": {
        "metrics": ["CPU", "DTU/vCore", "storage", "IO"],
        "fallback": "Collect SQL CPU/DTU/vCore, storage, and IO utilization evidence before quantifying savings.",
    },
    "microsoft.network/publicipaddresses": {
        "metrics": ["association", "allocation method", "SKU"],
        "fallback": "Check Public IP association, allocation method, and SKU state before quantifying savings.",
    },
}


def normalized_resource_id(resource_id: Any) -> str:
    return str(resource_id or "").casefold()


def capability(resource_type: Any) -> dict:
    return RESOURCE_CAPABILITIES.get(normalized_resource_id(resource_type), {
        "metrics": ["resource-specific utilization and configuration"],
        "fallback": "Collect resource-specific utilization and configuration evidence before quantifying savings.",
    })


def fallback_action(resource_type: Any) -> str:
    return capability(resource_type)["fallback"]


def canonical_evidence(resource: dict, cost: dict | None = None, metric: dict | None = None) -> dict:

    cost, metric = cost or {}, metric or {}
    configuration = resource.get("configuration") or {}
    resource_id = resource.get("id") or resource.get("resource_id")
    cost_value = cost.get("monthly_cost", cost.get("cost"))
    cost_available = bool(cost.get("cost_data_available") or cost_value is not None)
    metric_available = bool(metric.get("metric_available"))
    return {
        "resource_id": resource_id,
        "resource_name": resource.get("name") or resource.get("resource_name"),
        "resource_type": resource.get("type") or resource.get("resource_type"),
        "resource_group": resource.get("resource_group"),
        "region": resource.get("location") or resource.get("region"),
        "configuration": configuration,
        "configuration_available": bool(configuration or resource.get("sku") or resource.get("sku_name")),
        "metrics": metric.get("values", {}),
        "metric_details": metric.get("metrics", {}),
        "metric_names": metric.get("metric_names", []),
        "metric_available": metric_available,
        "metric_errors": metric.get("metric_errors", {}),
        "metric_timestamp": metric.get("collected_at") or metric.get("metric_timestamp"),
        "metric_unavailable_reason": metric.get("metric_unavailable_reason"),
        "utilization_available": metric_available,
        "cost": cost_value if cost_available else None,
        "cost_source": cost.get("cost_source"),
        "cost_type": cost.get("cost_type"),
        "is_estimated": bool(cost.get("is_estimated")),
        "cost_data_available": cost_available,
    }


def evidence_audit(evidence: dict, analyzer: str = "none", finding: str | None = None, recommendation: str | None = None):
    logger.info(
        "RESOURCE: %(resource_name)s TYPE: %(resource_type)s RESOURCE_ID: %(resource_id)s COST: %(cost)s COST_SOURCE: %(cost_source)s COST_TYPE: %(cost_type)s CONFIGURATION: %(configuration_available)s METRICS: %(metric_names)s METRIC_AVAILABLE: %(metric_available)s METRIC_TIMESTAMP: %(metric_timestamp)s COST_LINKED: %(cost_data_available)s ANALYZER: %(analyzer)s FINDING: %(finding)s SAVINGS: %(estimated_savings)s RECOMMENDATION: %(recommendation)s",
        {**evidence, "analyzer": analyzer, "finding": finding, "recommendation": recommendation},
    )
