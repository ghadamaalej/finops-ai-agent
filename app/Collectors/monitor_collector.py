from datetime import datetime, timedelta, timezone
import logging
import re
import importlib.metadata
try:
    # Metrics moved out of azure-monitor-query in v2.0.0.  The supported
    # package is azure-monitor-querymetrics (MetricsClient.query_resources).
    from azure.monitor.querymetrics import MetricsClient
    METRICS_SDK_VERSION = importlib.metadata.version("azure-monitor-querymetrics")
except (ImportError, importlib.metadata.PackageNotFoundError):  # Non-monitor tests can run without Azure SDK.
    MetricsClient = None
    METRICS_SDK_VERSION = None

from app.services.azure_credential import (
    get_azure_credential
)
from app.services.resource_evidence import RESOURCE_CAPABILITIES


class MonitorCollector:

    DAYS = 30
    logger = logging.getLogger(__name__)
    METRIC_CATALOG = {
        "microsoft.compute/virtualmachines": ["Percentage CPU", "Network In Total", "Network Out Total", "Disk Read Operations/Sec", "Disk Write Operations/Sec"],
        "microsoft.web/sites": ["CpuPercentage", "MemoryWorkingSet", "Requests", "Http5xx"],
        # These are the platform metric names exposed by Microsoft.Compute/disks.
        # They are queried independently because Azure may support only a subset
        # for a particular disk/SKU/region.
        # Azure's live metric configuration for Microsoft.Compute/disks. The
        # service does not expose latency for this resource type; requesting it
        # produces HTTP 400 and must not poison the other disk metrics.
        "microsoft.compute/disks": ["Composite Disk Read Operations/sec", "Composite Disk Write Operations/sec", "Composite Disk Read Bytes/sec", "Composite Disk Write Bytes/sec", "DiskPaidBurstIOPS"],
        "microsoft.containerregistry/registries": ["StorageUsed", "TotalPullCount", "TotalPushCount"],
        "microsoft.sql/servers/databases": ["cpu_percent", "dtu_consumption_percent", "storage_percent", "sessions_percent", "physical_data_read_percent"],
    }
    CONFIG_ONLY_TYPES = {
        "microsoft.network/publicipaddresses": "Public IP utilization is configuration-based; Azure Monitor does not expose a resource-level utilization metric.",
    }

    def __init__(self, credential=None):

        self.credential = credential or get_azure_credential()

        self.clients = {}


    def _get_client(self, region: str):

        region = (
            region
            or "global"
        ).lower().strip()

        if region in self.clients:
            return self.clients[region]

        endpoint = (
            f"https://{region}.metrics.monitor.azure.com"
        )

        if MetricsClient is None:
            raise RuntimeError("azure-monitor-querymetrics SDK is not installed")
        client = MetricsClient(
            endpoint,
            self.credential
        )

        self.clients[region] = client

        return client

    # ==========================================================
    # COLLECT
    # ==========================================================

    def collect(
        self,
        resources: list[dict]
    ) -> list[dict]:

        metrics = []

        print()
        print("=" * 70)
        print("AZURE MONITOR METRICS COLLECTION")
        print("=" * 70)

        for resource in resources:

            resource_type = (
                resource.get(
                    "type",
                    ""
                )
                .lower()
                .strip()
            )

            try:
                result = self._collect_resource_metrics(resource, resource_type)
                metrics.append(result)
            except Exception as exc:
                # Never hide the Azure exception behind metric_available=False.
                # This log contains the client, request, HTTP status and Azure
                # error details needed to diagnose permissions/API failures.
                self.logger.exception("Azure Monitor query failed: client=azure.monitor.querymetrics.MetricsClient sdk=%s resource_id=%s resource_type=%s error=%s status=%s code=%s message=%s", METRICS_SDK_VERSION, resource.get("id"), resource_type, type(exc).__name__, getattr(exc, "status_code", None), getattr(exc, "error_code", None), str(exc))
                metrics.append(self._unavailable_metric(resource, "azure_monitor_query_failed", exception=exc))

        print()
        print("=" * 70)
        print(
            f"METRICS COLLECTED: {len(metrics)}"
        )
        print("=" * 70)

        return metrics

    def _collect_resource_metrics(self, resource: dict, resource_type: str) -> dict:
        metric_names = self.METRIC_CATALOG.get(resource_type)
        if not metric_names:
            return self._unavailable_metric(resource, self.CONFIG_ONLY_TYPES.get(resource_type, "no_resource_type_metric_catalog"))
        return self._query_metrics(resource, metric_names)

    @staticmethod
    def _configuration(resource: dict) -> dict:
        source = resource.get("configuration") or {}
        return {
            "managed_by": source.get("managed_by", resource.get("managed_by")),
            "disk_state": source.get("disk_state", resource.get("disk_state")),
            "sku": source.get("sku", resource.get("sku") or resource.get("sku_name")),
            "disk_size_gb": source.get("disk_size_gb", resource.get("disk_size_gb")),
        }

    @staticmethod
    def _azure_error(exc: Exception) -> dict:
        response = getattr(exc, "response", None)
        message = str(exc)
        return {
            "exception_type": type(exc).__name__,
            "status_code": getattr(exc, "status_code", None) or getattr(response, "status_code", None),
            "code": getattr(exc, "error_code", None) or (re.search(r"(?:Code|code):\\s*([A-Za-z0-9_.-]+)", message) or [None, None])[1],
            "message": message,
        }

    def _query_metrics(self, resource: dict, metric_names: list[str]) -> dict:
        resource_id = resource.get("id")
        resource_type = resource.get("type")
        region = (resource.get("location") or "").lower().strip()
        if not resource_id or not region:
            return self._unavailable_metric(resource, "resource_id_or_region_missing")
        end_time = datetime.now(timezone.utc)
        values = {}
        metric_errors = {}
        timeseries = {}
        request_base = {
            "resource_ids": [resource_id], "metric_namespace": resource_type,
            "timespan": (end_time - timedelta(days=self.DAYS), end_time),
            "granularity": timedelta(hours=1), "aggregations": ["Average", "Maximum", "Total"],
        }
        client = self._get_client(region)
        for metric_name in metric_names:
            request = {**request_base, "metric_names": [metric_name]}
            self.logger.info("Azure Monitor query: client=azure.monitor.querymetrics.MetricsClient sdk=%s resource_id=%s metric_names=%s namespace=%s aggregation=%s timespan=%s", METRICS_SDK_VERSION, resource_id, [metric_name], resource_type, request["aggregations"], request["timespan"])
            try:
                response = client.query_resources(**request)
                found = False
                for result in response or []:
                    for metric in result.metrics or []:
                        points = [point for series in metric.timeseries or [] for point in series.data or []]
                        averages = [float(point.average) for point in points if point.average is not None]
                        totals = [float(point.total) for point in points if point.total is not None]
                        serialized = []
                        for point in points:
                            value = point.average if point.average is not None else point.total
                            timestamp = getattr(point, "time_stamp", None) or getattr(point, "timestamp", None)
                            if value is not None and timestamp is not None:
                                serialized.append({"timestamp": timestamp.isoformat() if hasattr(timestamp, "isoformat") else str(timestamp), "value": round(float(value), 4)})
                        if serialized:
                            timeseries[metric.name] = serialized
                        if averages:
                            values[metric.name] = round(sum(averages) / len(averages), 4)
                            found = True
                        elif totals:
                            values[metric.name] = round(sum(totals), 4)
                            found = True
                if not found:
                    metric_errors[metric_name] = {"reason": "azure_monitor_returned_no_datapoints"}
            except Exception as exc:
                metric_errors[metric_name] = self._azure_error(exc)
                self.logger.exception("Azure Monitor metric failed: resource_id=%s metric_name=%s namespace=%s error=%s", resource_id, metric_name, resource_type, str(exc))
        cpu = values.get("Percentage CPU", values.get("CpuPercentage", values.get("cpu_percent")))
        return {
            "resource_id": resource_id, "resource_name": resource.get("name"), "resource_type": resource_type,
            "metric_available": bool(values), "metric_names": metric_names, "values": values,
            "metrics": {name: {"available": name in values, "value": values.get(name)} for name in metric_names},
            "metric_errors": metric_errors, "timeseries": timeseries, "configuration": self._configuration(resource),
            "collected_at": end_time, "utilization_status": "available" if values else "unavailable",
            "utilization_reason": None if values else "azure_monitor_returned_no_datapoints",
            "metric_unavailable_reason": None if values else "azure_monitor_returned_no_datapoints",
            "cpu_average": cpu, "cpu_max": None, "collected_days": self.DAYS,
        }

    @staticmethod
    def _unavailable_metric(resource: dict, reason: str, exception: Exception | None = None) -> dict:
        return {
            "resource_id": resource.get("id"), "resource_name": resource.get("name"), "resource_type": resource.get("type"),
            "metric_available": False, "metric_names": [], "values": {}, "metrics": {},
            "metric_errors": {"request": MonitorCollector._azure_error(exception)} if exception else {},
            "configuration": MonitorCollector._configuration(resource),
            "collected_at": datetime.now(timezone.utc),
            "utilization_status": "not_applicable" if reason.startswith("Public IP") or reason == "no_resource_type_metric_catalog" else "unavailable",
            "utilization_reason": reason, "metric_unavailable_reason": reason,
            "cpu_average": None, "cpu_max": None, "collected_days": 0,
        }

    # Backwards-compatible entry point for existing callers/tests.
    def _collect_vm_metrics(
        self,
        resource: dict
    ):

        resource_id = resource.get(
            "id"
        )

        resource_name = resource.get(
            "name",
            ""
        )

        region = (
            resource.get(
                "location"
            )
            or ""
        ).lower().strip()

        if not resource_id:

            return None

        if not region:

            print(
                f"⚠️ Missing region: "
                f"{resource_name}"
            )

            return None

        print()
        print("----------------------------------------")
        print(
            f"VM: {resource_name}"
        )
        print(
            f"Region: {region}"
        )

        client = self._get_client(
            region
        )

        end_time = datetime.now(
            timezone.utc
        )

        start_time = (
            end_time
            - timedelta(
                days=self.DAYS
            )
        )

        # ------------------------------------------------------
        # Azure VM CPU metric
        # ------------------------------------------------------

        response = client.query_resources(
            resource_ids=[
                resource_id
            ],
            metric_namespace=(
                "Microsoft.Compute/virtualMachines"
            ),
            metric_names=[
                "Percentage CPU"
            ],
            timespan=(
                start_time,
                end_time
            ),
            granularity=timedelta(
                hours=1
            ),
            aggregations=[
                "Average",
                "Maximum",
            ],
        )

        if not response:

            print(
                "⚠️ No metric response"
            )

            return self._empty_metric(
                resource_id
            )

        result = response[0]

        cpu_average = None
        cpu_max = None

        # ------------------------------------------------------
        # Extract CPU
        # ------------------------------------------------------

        for metric in result.metrics:

            if metric.name.lower() != (
                "percentage cpu"
            ).lower():

                continue

            averages = []
            maximums = []

            for timeseries in metric.timeseries:

                for point in timeseries.data:

                    if point.average is not None:

                        averages.append(
                            float(
                                point.average
                            )
                        )

                    if point.maximum is not None:

                        maximums.append(
                            float(
                                point.maximum
                            )
                        )

            if averages:

                cpu_average = (
                    sum(averages)
                    / len(averages)
                )

            if maximums:

                cpu_max = max(
                    maximums
                )

        print(
            f"CPU average: "
            f"{cpu_average}"
        )

        print(
            f"CPU max: "
            f"{cpu_max}"
        )

        return {

            "resource_id": resource_id,
            "resource_type": "Microsoft.Compute/virtualMachines",
            "utilization_status": "available" if cpu_average is not None else "unavailable",
            "utilization_reason": None if cpu_average is not None else "no_data",

            "cpu_average":
                cpu_average,

            "cpu_max":
                cpu_max,

            "memory_average":
                0,

            "memory_max":
                0,

            "network_in":
                0,

            "network_out":
                0,

            "disk_read_iops":
                0,

            "disk_write_iops":
                0,

            "availability":
                100,

            "collected_days":
                self.DAYS,
        }

    @staticmethod
    def _empty_metric(
        resource_id: str
    ):

        return {

            "resource_id": resource_id,
            "utilization_status": "unavailable",
            "utilization_reason": "no_data",

            "cpu_average":
                None,

            "cpu_max":
                None,

            "memory_average":
                0,

            "memory_max":
                0,

            "network_in":
                0,

            "network_out":
                0,

            "disk_read_iops":
                0,

            "disk_write_iops":
                0,

            "availability":
                100,

            "collected_days":
                30,
        }

    def close(self):

        for client in self.clients.values():

            try:
                client.close()

            except Exception:
                pass

        self.clients.clear()
