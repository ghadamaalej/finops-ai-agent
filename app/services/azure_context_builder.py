from datetime import datetime, timezone
import json
import logging
from app.Collectors.resource_collector import (
    ResourceCollector
)

from app.Collectors.retail_cost_collector import (
    RetailCostCollector
)

from app.database.connection import SessionLocal
from app.database.models import CostCache, CostHistory, CostRecord, LearningMetricMemory
from app.database.repositories.cost_cache_repository import CostCacheRepository
from app.services.cost_service import CostService
from app.services.azure_credential import DelegatedArmCredential
from app.services.resource_evidence import canonical_evidence, evidence_audit, normalized_resource_id

from app.Collectors.monitor_collector import (
    MonitorCollector
)

from app.Collectors.security_collector import (
    SecurityCollector
)

from app.Collectors.governance_collector import (
    GovernanceCollector
)

def _governance_resource_ids(value):
    # Normalize producer output without treating counts as resource IDs."
    if not isinstance(value, (list, tuple, set)):
        return [], value if isinstance(value, int) else 0
    resource_ids = [item for item in value if isinstance(item, str) and item]
    return resource_ids, len(set(resource_ids))

from app.models.azure import (
    AzureContext,
    AzureResource,
    ResourceCost,
    PerformanceMetric,
    SecurityFinding,
    GovernanceState,
)


class AzureContextBuilder:
    logger = logging.getLogger(__name__)

    def __init__(self, cost_service=None, session_factory=SessionLocal, resource_collector=None):

        self._resource_collector_injected = resource_collector is not None
        self.resources = resource_collector or ResourceCollector()

        self.cost = (
            RetailCostCollector()
        )

        # This is the one cost path: cache lookup, collection, cache/history
        # persistence, then the same records feed ResourceCost and analyzers.
        self.cost_service = cost_service or CostService(
            self.cost,
            CostCacheRepository(),
        )
        self.session_factory = session_factory

        self.monitor = (
            MonitorCollector()
        )

        self.governance = (
            GovernanceCollector()
        )

    # =========================================================
    # BUILD
    # =========================================================

    def refresh_costs(self, subscription_id: str, azure_access_token: str | None = None) -> dict:
        """Read resource inventory and retail prices, then persist one snapshot.

        This intentionally performs no Azure mutation. It collects the
        read-only environment metrics used by the production dashboard;
        dashboard GET requests remain read-only.
        """
        resource_collector = (
            ResourceCollector(credential=DelegatedArmCredential(azure_access_token))
            if azure_access_token and not self._resource_collector_injected
            else self.resources
        )
        resources_data = resource_collector.collect(subscription_id)
        db = self.session_factory()
        try:
            costs_data = self.cost_service.get_costs(
                db,
                subscription_id=subscription_id,
                resources=resources_data,
                force_refresh=True,
            )
            if azure_access_token:
                environment = self.collect_environment(subscription_id, azure_access_token, resources_data)
                db.add(LearningMetricMemory(metrics=json.loads(json.dumps({"subscription_id": subscription_id, "environment": environment}, default=str))))
                db.commit()
            return {
                "subscription_id": subscription_id,
                "resources_collected": len(resources_data),
                "cost_records_collected": len(costs_data),
                "cost_records_persisted": db.query(CostRecord).filter_by(subscription_id=subscription_id).count(),
                "cache_rows_persisted": db.query(CostCache).filter_by(subscription_id=subscription_id).count(),
                "history_rows_persisted": db.query(CostHistory).filter_by(subscription_id=subscription_id).count(),
                "cost_source": costs_data[0].get("cost_source") if costs_data else None,
                "cost_type": costs_data[0].get("cost_type") if costs_data else None,
                "is_estimated": costs_data[0].get("is_estimated") if costs_data else None,
            }
        finally:
            db.close()

    def collect_environment(self, subscription_id: str, azure_access_token: str, resources_data: list[dict]) -> dict:
        credential = DelegatedArmCredential(azure_access_token)
        metrics = MonitorCollector(credential=credential).collect(resources_data)
        try:
            security = SecurityCollector(subscription_id, credential=credential).collect()
        except Exception:
            security = []
        try:
            governance = GovernanceCollector(credential=credential).collect(subscription_id)
        except Exception:
            governance = {"compliance_score": None, "policy_violations": [], "affected_resources": [], "status": "unavailable"}
        costs_by_id = {}
        db = self.session_factory()
        try:
            costs = self.cost_service.get_costs(db, subscription_id=subscription_id, resources=resources_data)
            costs_by_id = {normalized_resource_id(item.get("resource_id")): item for item in costs}
        finally:
            db.close()
        metrics_by_id = {normalized_resource_id(item.get("resource_id")): item for item in metrics}
        for resource in resources_data:
            evidence_audit(canonical_evidence(resource, costs_by_id.get(normalized_resource_id(resource.get("id"))), metrics_by_id.get(normalized_resource_id(resource.get("id")))))
        cpu_values = [float(item["cpu_average"]) for item in metrics if item.get("cpu_average") is not None]
        critical = sum(item.get("severity", "").lower() == "critical" for item in security)
        high = sum(item.get("severity", "").lower() == "high" for item in security)
        raw_affected_resources = governance.get("affected_resources", []) if isinstance(governance, dict) else []
        affected_resources, affected_resource_count = _governance_resource_ids(raw_affected_resources)
        return {
            "resource_inventory": [
                {
                    "resource_id": resource.get("id"),
                    "resource_name": resource.get("name"),
                    "resource_type": resource.get("type"),
                    "resource_group": resource.get("resource_group"),
                    "location": resource.get("location"),
                    "sku": resource.get("sku") or resource.get("vm_size") or resource.get("sku_name"),
                    "vm_size": resource.get("vm_size"),
                    "configuration": resource.get("configuration", {}),
                    "provisioning_state": resource.get("provisioning_state") or resource.get("power_state"),
                    "configuration_status": "available" if any(resource.get(key) for key in ("sku", "sku_name", "vm_size", "os_type", "kind", "tags", "configuration")) else "unavailable",
                }
                for resource in resources_data
                if resource.get("id")
            ],
            "security": {
            "score": max(0, 100 - (critical * 20) - (high * 10)) if security else 100,
            "critical": critical,
            "high": high,
                "total": len(security),
            },
            # Preserve the resource IDs returned by Defender assessments. The
            # details endpoint filters this list and never attributes the
            # subscription aggregate to an individual resource.
            "security_findings": security,
            "governance": {
                "compliance": governance.get("compliance_score"),
                "violations": len(governance.get("policy_violations", [])),
                "affected_resources": affected_resources,
                "affected_resource_count": affected_resource_count,
            },
            "performance": {
                "average_cpu": round(sum(cpu_values) / len(cpu_values), 2) if cpu_values else None,
                "underutilized": sum(value <= 10 for value in cpu_values),
                "overutilized": sum(value >= 80 for value in cpu_values),
                "resources": [
                    {
                        "resource_id": item.get("resource_id"),
                        "resource_type": item.get("resource_type"),
                        "metric_available": item.get("metric_available", False),
                        "metric_names": item.get("metric_names", []),
                        "values": item.get("values", {}),
                        "metrics": item.get("metrics", item.get("values", {})),
                        "metric_errors": item.get("metric_errors", {}),
                        "configuration": item.get("configuration", {}),
                        "collected_at": item.get("collected_at").isoformat() if item.get("collected_at") else None,
                        "cpu_average": item.get("cpu_average"),
                        "cpu_max": item.get("cpu_max"),
                        "utilization_status": item.get("utilization_status", "unavailable"),
                        "utilization_reason": item.get("utilization_reason"),
                        "metric_unavailable_reason": item.get("metric_unavailable_reason"),
                    }
                    for item in metrics
                    if item.get("resource_id")
                ],
            },
        }

    def build_analysis_context(self, subscription_id: str, azure_access_token: str) -> AzureContext:
        """Collect the cost and CPU evidence needed for rightsizing analysis."""
        credential = DelegatedArmCredential(azure_access_token)
        resources_data = ResourceCollector(credential=credential).collect(subscription_id)
        db = self.session_factory()
        try:
            costs_data = self.cost_service.get_costs(
                db, subscription_id=subscription_id, resources=resources_data, force_refresh=True
            )
        finally:
            db.close()
        metrics_data = MonitorCollector(credential=credential).collect(resources_data)
        return AzureContext(
            subscription_id=subscription_id,
            collected_at=datetime.now(timezone.utc),
            resources=[AzureResource(**resource) for resource in resources_data],
            resource_costs=[ResourceCost(**cost) for cost in costs_data],
            metrics=[PerformanceMetric(**metric) for metric in metrics_data if metric.get("resource_id")],
            security_findings=[],
            governance=None,
        )

    def build(
        self,
        subscription_id: str
    ) -> AzureContext:

        print()

        print(
            "=" * 70
        )

        print(
            "BUILDING AZURE CONTEXT"
        )

        print(
            "=" * 70
        )

        # =====================================================
        # RESOURCES
        # =====================================================

        resources_data = (
            self.resources.collect(
                subscription_id
            )
        )

        print(
            f"Resources collected: "
            f"{len(resources_data)}"
        )

        # =====================================================
        # VM INPUT DIAGNOSTIC
        # =====================================================

        print(
            "\n===== VM COST INPUT DIAGNOSTIC ====="
        )

        for resource in resources_data:

            if (
                resource.get(
                    "type",
                    ""
                ).lower()
                == "microsoft.compute/virtualmachines"
            ):

                print(
                    {
                        "name":
                            resource.get(
                                "name"
                            ),

                        "type":
                            resource.get(
                                "type"
                            ),

                        "location":
                            resource.get(
                                "location"
                            ),

                        "sku":
                            resource.get(
                                "sku"
                            ),

                        "vm_size":
                            resource.get(
                                "vm_size"
                            ),

                        "os_type":
                            resource.get(
                                "os_type"
                            ),

                        "id":
                            resource.get(
                                "id"
                            ),
                    }
                )

        # =====================================================
        # COST
        # =====================================================

        db = self.session_factory()
        try:
            costs_data = self.cost_service.get_costs(
                db,
                subscription_id=subscription_id,
                resources=resources_data,
            )
        finally:
            db.close()

        print()

        print(
            "=" * 70
        )

        print(
            "COST QUALITY VALIDATION"
        )

        print(
            "=" * 70
        )

        for cost in costs_data:

            print()

            print(
                f"Resource : "
                f"{cost.get('resource_name')}"
            )

            print(
                f"Type     : "
                f"{cost.get('resource_type')}"
            )

            print(
                f"SKU      : "
                f"{cost.get('sku')}"
            )

            print(
                f"ARM SKU  : "
                f"{cost.get('arm_sku_name')}"
            )

            print(
                f"Meter    : "
                f"{cost.get('meter_name')}"
            )

            print(
                f"Product  : "
                f"{cost.get('product_name')}"
            )

            print(
                f"Price    : "
                f"{cost.get('hourly_price')}"
            )

            print(
                f"Monthly  : "
                f"{cost.get('monthly_cost')}"
            )

            print(
                f"Validated: "
                f"{cost.get('pricing_validated')}"
            )

            print(
                f"Source   : "
                f"{cost.get('cost_source')}"
            )

            print(
                f"Estimated: "
                f"{cost.get('is_estimated')}"
            )

        print()

        print(
            f"Cost records collected: "
            f"{len(costs_data)}"
        )

        # =====================================================
        # MONITORING
        # =====================================================

        metrics_data = (
            self.monitor.collect(
                resources_data
            )
        )
        metrics_by_resource = {normalized_resource_id(item.get("resource_id")): item for item in metrics_data}
        costs_by_resource = {normalized_resource_id(item.get("resource_id")): item for item in costs_data}
        for resource in resources_data:
            resource_id = normalized_resource_id(resource.get("id"))
            metric = metrics_by_resource.get(resource_id, {})
            cost = costs_by_resource.get(resource_id, {})
            evidence_audit(canonical_evidence(resource, cost, metric), analyzer="pending")

        print(
            f"Metrics collected: "
            f"{len(metrics_data)}"
        )

        # =====================================================
        # SECURITY
        # =====================================================

        security_collector = (
            SecurityCollector(
                subscription_id
            )
        )

        security_data = (
            security_collector.collect()
        )

        print(
            f"Security findings collected: "
            f"{len(security_data)}"
        )

        # =====================================================
        # GOVERNANCE
        # =====================================================

        governance_data = (
            self.governance.collect(
                subscription_id
            )
        )

        # =====================================================
        # BUILD PYDANTIC CONTEXT
        # =====================================================

        context = AzureContext(

            subscription_id=
                subscription_id,

            collected_at=
                datetime.now(
                    timezone.utc
                ),

            resources=[
                AzureResource(
                    **resource
                )
                for resource
                in resources_data
            ],

            resource_costs=[
                ResourceCost(
                    **cost
                )
                for cost
                in costs_data
            ],

            metrics=[

                PerformanceMetric(

                    resource_id=metric.get("resource_id"),
                    resource_type=metric.get("resource_type"),
                    metric_available=metric.get("metric_available", False),
                    metric_names=metric.get("metric_names", []),
                    values=metric.get("values", {}),
                    collected_at=metric.get("collected_at"),

                    cpu_average=
                        metric.get(
                            "cpu_average"
                        ),

                    cpu_max=
                        metric.get(
                            "cpu_max"
                        ),

                    memory_average=
                        metric.get(
                            "memory_average"
                        ),

                    memory_max=
                        metric.get(
                            "memory_max"
                        ),

                    network_in=
                        metric.get(
                            "network_in"
                        ),

                    network_out=
                        metric.get(
                            "network_out"
                        ),

                    disk_read_iops=
                        metric.get(
                            "disk_read_iops"
                        ),

                    disk_write_iops=
                        metric.get(
                            "disk_write_iops"
                        ),

                    availability=
                        metric.get(
                            "availability",
                            100
                        ),

                    collected_days=
                        metric.get(
                            "collected_days",
                            30
                        ),
                )

                for metric
                in metrics_data

                if metric.get(
                    "resource_id"
                )
            ],

            security_findings=[
                SecurityFinding(
                    **finding
                )
                for finding
                in security_data
            ],

            governance=
                GovernanceState(
                    **governance_data
                ),
        )

        # =====================================================
        # COST SUMMARY
        # =====================================================

        total_cost = sum(
            float(
                cost.monthly_cost or 0
            )
            for cost
            in context.resource_costs
        )

        estimated_costs = [
            cost
            for cost
            in context.resource_costs
            if cost.is_estimated
        ]

        actual_costs = [
            cost
            for cost
            in context.resource_costs
            if not cost.is_estimated
        ]

        # =====================================================
        # SUMMARY
        # =====================================================

        print()

        print(
            "=" * 70
        )

        print(
            "AZURE CONTEXT SUMMARY"
        )

        print(
            "=" * 70
        )

        print(
            f"Resources       : "
            f"{len(context.resources)}"
        )

        print(
            f"Cost records    : "
            f"{len(context.resource_costs)}"
        )

        print(
            f"Estimated costs : "
            f"{len(estimated_costs)}"
        )

        print(
            f"Actual costs    : "
            f"{len(actual_costs)}"
        )

        print(
            f"Metrics         : "
            f"{len(context.metrics)}"
        )

        print(
            f"Security        : "
            f"{len(context.security_findings)}"
        )

        print(
            f"Total cost      : "
            f"{total_cost:.2f}"
        )

        # =====================================================
        # COST DETAILS
        # =====================================================

        for cost in (
            context.resource_costs[:10]
        ):

            print()

            print(
                f"  {cost.resource_name}"
            )

            print(
                f"    Monthly : "
                f"{cost.monthly_cost:.2f} "
                f"{cost.currency}"
            )

            print(
                f"    Source  : "
                f"{cost.cost_source}"
            )

            print(
                f"    Type    : "
                f"{cost.cost_type}"
            )

            print(
                f"    Estimated: "
                f"{cost.is_estimated}"
            )

            print(
                f"    Validated: "
                f"{cost.pricing_validated}"
            )

            print(
                f"    Method  : "
                f"{cost.pricing_method}"
            )

        print(
            "=" * 70
        )

        return context
