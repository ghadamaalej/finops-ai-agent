"Deterministic, exact-resource Azure Monitor metric capability service."""
from datetime import datetime, timedelta, timezone
import logging
try:
    from azure.monitor.querymetrics import MetricsClient
except ImportError:
    MetricsClient = None
from app.services.azure_credential import get_azure_credential
RESOURCE_METRIC_CAPABILITIES = {
    "microsoft.compute/virtualmachines": ("Percentage CPU", "Network In Total", "Network Out Total", "Disk Read Operations/Sec", "Disk Write Operations/Sec"),
    "microsoft.compute/disks": ("Composite Disk Read Operations/sec", "Composite Disk Write Operations/sec", "Composite Disk Read Bytes/sec", "Composite Disk Write Bytes/sec", "DiskPaidBurstIOPS"),
    "microsoft.network/networkinterfaces": ("Bytes Received", "Bytes Sent", "Packets Received", "Packets Sent"),
    "microsoft.containerregistry/registries": ("StorageUsed", "TotalPullCount", "TotalPushCount"),
    "microsoft.sql/servers/databases": ("cpu_percent", "dtu_consumption_percent", "storage_percent", "sessions_percent", "physical_data_read_percent"),
}

class AzureMetricsService:
    """Queries only the supplied resource ID and its type's metric catalog."""
    def __init__(self, credential=None, client_factory=None, days=30):
        self.credential = credential or get_azure_credential()
        self.client_factory = client_factory or self._default_client
        self.days = days
        self.clients = {}

    @staticmethod
    def _default_client(region, credential):
        if MetricsClient is None:
            raise RuntimeError("azure-monitor-querymetrics SDK is not installed")
        return MetricsClient(f"https://{region}.metrics.monitor.azure.com", credential)

    def _client(self, region):
        region = str(region or "").strip().lower()
        if region not in self.clients:
            self.clients[region] = self.client_factory(region, self.credential)
        return self.clients[region]

    @staticmethod
    def _type(resource_type):
        return str(resource_type or "").strip().casefold()

    def get_resource_metrics(self, resource_id, resource_type, metric_names=None, timespan=None, interval=None, region=None, resource_name=None):
        resource_type_text = str(resource_type or "").strip()
        supported = list(RESOURCE_METRIC_CAPABILITIES.get(self._type(resource_type), ()))
        if not supported:
            return {"resource_id": resource_id, "resource_name": resource_name, "resource_type": resource_type_text, "available": False, "status": "metrics_unavailable", "metrics": [], "reason": "Azure Monitor does not expose supported metrics for this resource type."}
        requested = list(metric_names) if metric_names else supported
        requested = [name for name in requested if name in supported]
        if not requested:
            return {"resource_id": resource_id, "resource_name": resource_name, "resource_type": resource_type_text, "available": False, "status": "metrics_unavailable", "metrics": [], "reason": "No requested metrics are supported for this resource type."}
        if not resource_id or not region:
            return {"resource_id": resource_id, "resource_name": resource_name, "resource_type": resource_type_text, "available": False, "status": "metrics_unavailable", "metrics": [], "reason": "Resource ID or Azure region is unavailable."}
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=self.days)
        span = timespan or (start, end)
        values = []
        try:
            client = self._client(region)
            response = client.query_resources(resource_ids=[resource_id], metric_namespace=resource_type_text, metric_names=requested, timespan=span, granularity=interval or timedelta(hours=1), aggregations=["Average", "Minimum", "Maximum", "Total"])
            for result in response or []:
                for metric in getattr(result, "metrics", []) or []:
                    points = [point for series in (getattr(metric, "timeseries", []) or []) for point in (getattr(series, "data", []) or [])]
                    averages = [float(point.average) for point in points if getattr(point, "average", None) is not None]
                    minimums = [float(point.minimum) for point in points if getattr(point, "minimum", None) is not None]
                    maximums = [float(point.maximum) for point in points if getattr(point, "maximum", None) is not None]
                    totals = [float(point.total) for point in points if getattr(point, "total", None) is not None]
                    if averages or minimums or maximums or totals:
                        values.append({"name": metric.name, "display_name": metric.name, "average": round(sum(averages) / len(averages), 4) if averages else None, "minimum": min(minimums) if minimums else None, "maximum": max(maximums) if maximums else None, "total": round(sum(totals), 4) if totals else None, "unit": getattr(metric, "unit", None), "timespan": str(span)})
        except Exception as exc:
            return {"resource_id": resource_id, "resource_name": resource_name, "resource_type": resource_type_text, "available": False, "status": "metrics_unavailable", "metrics": [], "reason": str(exc)}
        return {"resource_id": resource_id, "resource_name": resource_name, "resource_type": resource_type_text, "available": bool(values), "status": "available" if values else "metrics_unavailable", "metrics": values, "reason": None if values else "Azure Monitor returned no datapoints for supported metrics."}
