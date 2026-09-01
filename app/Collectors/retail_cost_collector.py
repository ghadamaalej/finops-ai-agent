from app.services.retail_price_service import (
    AzureRetailPriceService
)

from app.services.cost_calculator import (
    CostCalculator
)


class RetailCostCollector:

    HOURS_PER_MONTH = 730
    COST_SOURCE = "Azure Retail Prices"
    COST_TYPE = "estimated"
    IS_ESTIMATED = True

    PRICING_HANDLERS = {

        "microsoft.compute/virtualmachines":
            "_price_vm",

        "microsoft.web/sites":
            "_price_app_service",

        "microsoft.network/publicipaddresses":
            "_price_public_ip",

        "microsoft.compute/disks":
            "_price_managed_disk",

        "microsoft.sql/servers/databases":
            "_price_sql_database",

        "microsoft.containerservice/managedclusters":
            "_price_aks",

        "microsoft.web/serverfarms":
            "_price_app_service_plan",

        "microsoft.storage/storageaccounts":
            "_price_storage_account",

        "microsoft.containerregistry/registries":
            "_price_container_registry",

        "microsoft.keyvault/vaults":
            "_price_key_vault",

        "microsoft.network/loadbalancers":
            "_price_load_balancer",

        "microsoft.network/natgateways":
            "_price_nat_gateway",

        "microsoft.network/virtualnetworkgateways":
            "_price_network_gateway",

        "microsoft.network/privateendpoints":
            "_price_zero_cost",

        "microsoft.network/virtualnetworks":
            "_price_zero_cost",

        "microsoft.network/networksecuritygroups":
            "_price_zero_cost",

        "microsoft.network/routetables":
            "_price_zero_cost",

        "microsoft.network/networkinterfaces":
            "_price_zero_cost",

        "microsoft.operationalinsights/workspaces":
            "_price_log_analytics",

        "microsoft.insights/datacollectionendpoints":
            "_price_zero_cost",

        "microsoft.insights/datacollectionrules":
            "_price_zero_cost",

        "microsoft.recoveryservices/vaults":
            "_price_zero_cost",

        "microsoft.dataprotection/backupvaults":
            "_price_zero_cost",

        "microsoft.cognitiveservices/accounts":
            "_price_cognitive_service",

        "microsoft.compute/snapshots":
            "_price_snapshot",

        "microsoft.sql/servers":
            "_price_sql_server",

        "microsoft.web/sites/slots":
            "_price_zero_cost",
    }

    def __init__(self):

        self.pricing = (
            AzureRetailPriceService()
        )

    # =========================================================
    # MAIN COLLECTION
    # =========================================================

    def collect(
        self,
        resources: list[dict]
    ) -> list[dict]:

        costs = []

        print(
            "\n" + "=" * 70
        )

        print(
            "RETAIL COST COLLECTION"
        )

        print(
            "=" * 70
        )

        for resource in resources:

            resource_type = (
                resource.get(
                    "type",
                    ""
                )
                .lower()
                .strip()
            )

            handler_name = (
                self.PRICING_HANDLERS.get(
                    resource_type
                )
            )

            if not handler_name:
                print(f"No retail pricing handler for resource type: {resource_type}")
                costs.append(self._unavailable_result(resource, "unsupported", "No retail pricing handler for this resource type"))
                continue

            try:

                handler = getattr(
                    self,
                    handler_name
                )

                cost = handler(
                    resource
                )

                if cost:

                    costs.append(self._with_retail_provenance(cost))

            except Exception as exc:

                print(
                    f"❌ Cost error for "
                    f"{resource.get('name')}: "
                    f"{type(exc).__name__}: "
                    f"{exc}"
                )

        print(
            "\n" + "=" * 70
        )

        print(
            "RETAIL COST SUMMARY"
        )

        print(
            "=" * 70
        )

        print(
            f"Cost records collected: "
            f"{len(costs)}"
        )

        return costs

    @staticmethod
    def _unavailable_result(resource: dict, status: str, reason: str) -> dict:
        return {
            "resource_id": resource.get("id"),
            "resource_name": resource.get("name", ""),
            "resource_type": resource.get("type", "").lower(),
            "service_name": resource.get("type", "").split("/")[0],
            "monthly_cost": None,
            "cost_last_30_days": None,
            "currency": None,
            "cost_data_available": False,
            "cost_status": status,
            "cost_source": "none",
            "cost_type": None,
            "is_estimated": False,
            "pricing_warning": reason,
            "region": (resource.get("location") or "").lower().strip(),
            "sku": resource.get("sku_name") or resource.get("sku") or None,
        }

    @classmethod
    def _with_retail_provenance(cls, cost: dict) -> dict:
        """Apply the collector's declared provenance to every priced record.

        This is the canonical source boundary for retail estimates.  Storage
        layers copy these fields verbatim and never infer them.
        """
        return {
            **cost,
            "cost_source": cost.get("cost_source") or cls.COST_SOURCE,
            "cost_type": cost.get("cost_type") or cls.COST_TYPE,
            "is_estimated": cost.get("is_estimated", cls.IS_ESTIMATED),
            "cost_status": cost.get("cost_status") or "estimated",
        }

    # =========================================================
    # VM
    # =========================================================

    def _price_vm(
        self,
        resource: dict
    ):

        resource_id = (
            resource.get("id")
        )

        resource_name = (
            resource.get(
                "name",
                ""
            )
        )

        region = (
            resource.get("location")
            or ""
        ).lower().strip()

        sku = (
            resource.get("vm_size")
            or resource.get("sku")
            or ""
        ).strip()

        os_type = (
            resource.get("os_type")
            or ""
        ).strip()

        print(
            "\n----------------------------------------"
        )

        print(
            f"VM: {resource_name}"
        )

        print(
            f"Region: {region}"
        )

        print(
            f"SKU: {sku}"
        )

        print(
            f"OS: {os_type}"
        )

        if not region:

            print(
                "⚠️ VM skipped: missing region"
            )

            return None

        if not sku:

            print(
                "⚠️ VM skipped: missing VM size"
            )

            return None

        price = self.pricing.get_vm_price(
            region=region,
            sku=sku,
            os_type=os_type,
        )

        if not price:

            print(
                "⚠️ No valid standard VM "
                "retail price found"
            )

            return None

        hourly_price = float(
            price["retail_price"]
        )

        monthly_cost = (
            CostCalculator.hourly_to_monthly(
                hourly_price
            )
        )

        print(
            f"Hourly price: "
            f"{hourly_price}"
        )

        print(
            f"Estimated monthly: "
            f"{monthly_cost:.2f}"
        )

        return {

            "resource_id":
                resource_id,

            "resource_name":
                resource_name,

            "resource_type":
                "microsoft.compute/virtualmachines",

            "service_name":
                "Virtual Machines",

            "service_family":
                price.get(
                    "service_family"
                ),

            # -------------------------------------------------
            # Cost
            # -------------------------------------------------

            "monthly_cost":
                monthly_cost,

            "cost_last_30_days":
                monthly_cost,

            "currency":
                price["currency"],

            "cost_source":
                "Azure Retail Prices",

            "cost_type":
                "estimated",

            "is_estimated":
                True,

            "cost_data_available":
                True,

            # -------------------------------------------------
            # Pricing provenance
            # -------------------------------------------------

            "pricing_method":
                "retail_price_vm_standard_payg",

            "pricing_unit":
                price.get(
                    "unit_of_measure"
                ),

            "hourly_price":
                hourly_price,

            "estimated_hours":
                self.HOURS_PER_MONTH,

            "estimated_quantity":
                self.HOURS_PER_MONTH,

            "meter_name":
                price.get(
                    "meter_name"
                ),

            "product_name":
                price.get(
                    "product_name"
                ),

            # -------------------------------------------------
            # SKU
            # -------------------------------------------------

            "sku":
                sku,

            "arm_sku_name":
                price.get(
                    "arm_sku_name"
                ),

            "requested_arm_sku":
                price.get(
                    "requested_arm_sku",
                    sku
                ),

            # -------------------------------------------------
            # Region / OS
            # -------------------------------------------------

            "region":
                region,

            "os_type":
                os_type,

            # -------------------------------------------------
            # Validation
            # -------------------------------------------------

            "pricing_validated":
                price.get(
                    "pricing_validated",
                    False
                ),

            "pricing_selection":
                price.get(
                    "pricing_selection",
                    "standard_payg"
                ),

            "pricing_warning":
                price.get(
                    "pricing_warning"
                ),

            "rejected_candidate_count":
                price.get(
                    "rejected_candidate_count",
                    0
                ),
        }

    # =========================================================
    # MANAGED DISK
    # =========================================================

    def _price_managed_disk(
        self,
        resource: dict
    ):

        resource_id = (
            resource.get("id")
        )

        resource_name = (
            resource.get(
                "name",
                ""
            )
        )

        region = (
            resource.get(
                "location"
            )
            or ""
        ).lower().strip()

        disk_size_gb = int(
            resource.get(
                "disk_size_gb"
            )
            or 0
        )

        disk_sku = (
            resource.get("sku_name")
            or resource.get("sku")
            or ""
        ).strip()

        print(
            "\n----------------------------------------"
        )

        print(
            f"Managed Disk: "
            f"{resource_name}"
        )

        print(
            f"Region: {region}"
        )

        print(
            f"SKU: {disk_sku}"
        )

        print(
            f"Size: {disk_size_gb} GB"
        )

        if not region:

            print(
                "⚠️ Managed Disk skipped: "
                "missing region"
            )

            return None

        if not disk_sku:

            print(
                "⚠️ Managed Disk skipped: "
                "missing SKU"
            )

            return None

        if disk_size_gb <= 0:

            print(
                "⚠️ Managed Disk skipped: "
                "missing disk size"
            )

            return None

        price = (
            self.pricing.get_managed_disk_price(
                region=region,
                disk_sku=disk_sku,
                disk_size_gb=disk_size_gb,
            )
        )

        if not price:

            print(
                "⚠️ No Managed Disk "
                "retail price found"
            )

            return None

        monthly_cost = float(
            price["retail_price"]
        )

        print(
            f"Disk tier: "
            f"{price.get('disk_tier')}"
        )

        print(
            f"Pricing SKU: "
            f"{price.get('storage_sku')}"
        )

        print(
            f"Monthly price: "
            f"{monthly_cost:.2f}"
        )

        return {

            "resource_id":
                resource_id,

            "resource_name":
                resource_name,

            "resource_type":
                "microsoft.compute/disks",

            "service_name":
                "Managed Disks",

            "service_family":
                price.get(
                    "service_family"
                ),

            "monthly_cost":
                monthly_cost,

            "cost_last_30_days":
                monthly_cost,

            "currency":
                price["currency"],

            "cost_source":
                "Azure Retail Prices",

            "cost_type":
                "estimated",

            "is_estimated":
                True,

            "cost_data_available":
                True,

            "pricing_method":
                "retail_price_managed_disk_tier",

            "pricing_unit":
                price.get(
                    "unit_of_measure"
                ),

            "hourly_price":
                None,

            "estimated_hours":
                None,

            "estimated_quantity":
                disk_size_gb,

            "meter_name":
                price.get(
                    "meter_name"
                ),

            "product_name":
                price.get(
                    "product_name"
                ),

            "sku":
                disk_sku,

            "arm_sku_name":
                None,

            "pricing_sku":
                price.get(
                    "sku_name"
                ),

            "disk_tier":
                price.get(
                    "disk_tier"
                ),

            "storage_sku":
                price.get(
                    "storage_sku"
                ),

            "disk_size_gb":
                disk_size_gb,

            "region":
                region,

            "pricing_validated":
                True,

            "pricing_selection":
                "managed_disk_tier",

            "pricing_warning":
                None,

            "rejected_candidate_count":
                0,
        }

    # =========================================================
    # OTHER SERVICES
    # =========================================================

    def _price_app_service(
        self,
        resource: dict
    ):
        # App Service application usage is billed by its server farm. Query a
        # retail meter when a plan/SKU is available; do not erase provenance.
        sku = resource.get("sku_name") or resource.get("sku")
        if not sku:
            return self._price_zero_cost(resource)
        return self._price_meter_resource(
            resource,
            service_name="Azure App Service",
            pricing_method="retail_price_app_service",
            sku_name=sku,
        )

    def _price_public_ip(
        self,
        resource: dict
    ):

        sku = (resource.get("sku_name") or resource.get("sku") or "Standard").strip()
        pricing_sku = sku if sku.lower().endswith(" ip") else f"{sku} IP"
        return self._price_meter_resource(
            resource,
            service_name="Virtual Network",
            pricing_method="retail_price_public_ip",
            sku_name=pricing_sku,
            meter_name="IP Addresses",
        )

    def _price_sql_server(self, resource: dict):
        # Logical SQL servers may not carry a direct meter, but retain explicit
        # retail provenance rather than presenting a misleading unknown source.
        return self._price_meter_resource(
            resource,
            service_name="SQL Database",
            pricing_method="retail_price_sql_server",
            sku_name=resource.get("sku_name") or resource.get("sku"),
        )

    def _price_sql_database(
        self,
        resource: dict
    ):

        return self._price_meter_resource(
            resource,
            service_name="SQL Database",
            pricing_method="retail_price_sql_database",
            sku_name=resource.get("sku_name") or resource.get("sku"),
        )

    def _price_aks(self, resource: dict):
        return self._price_meter_resource(
            resource,
            service_name="Azure Kubernetes Service",
            pricing_method="retail_price_aks_cluster",
            sku_name=resource.get("sku_name") or resource.get("sku") or "Free",
        )

    def _price_app_service_plan(self, resource: dict):
        return self._price_meter_resource(
            resource,
            service_name="Azure App Service",
            pricing_method="retail_price_app_service_plan",
            sku_name=resource.get("sku_name") or resource.get("sku"),
        )

    def _price_storage_account(self, resource: dict):
        return self._price_meter_resource(
            resource,
            service_name="Storage",
            pricing_method="retail_price_storage_account",
            sku_name=resource.get("sku_name") or resource.get("sku"),
            meter_name=resource.get("meter_name"),
            quantity=resource.get("capacity_gb"),
            usage_based=True,
        )

    def _price_container_registry(self, resource: dict):
        return self._price_meter_resource(
            resource,
            service_name="Container Registry",
            pricing_method="retail_price_container_registry",
            sku_name=resource.get("sku_name") or resource.get("sku"),
        )

    def _price_load_balancer(self, resource: dict):
        sku = (resource.get("sku_name") or resource.get("sku") or "Standard").strip()
        pricing_sku = sku if "load balancer" in sku.lower() else f"{sku} Load Balancer"
        return self._price_meter_resource(
            resource,
            service_name="Load Balancer",
            pricing_method="retail_price_load_balancer",
            sku_name=pricing_sku,
            meter_name="Load Balancer",
        )

    def _price_key_vault(self, resource: dict):
        return self._price_meter_resource(
            resource,
            service_name="Key Vault",
            pricing_method="retail_price_key_vault",
            sku_name=resource.get("sku_name") or resource.get("sku"),
            quantity=resource.get("quantity"),
            usage_based=True,
        )

    def _price_log_analytics(self, resource: dict):
        return self._price_meter_resource(
            resource,
            service_name="Log Analytics",
            pricing_method="retail_price_log_analytics",
            sku_name=resource.get("sku_name") or "PerGB2018",
            quantity=resource.get("ingestion_gb"),
            usage_based=True,
        )

    def _price_cognitive_service(self, resource: dict):
        return self._price_meter_resource(
            resource,
            service_name="Cognitive Services",
            pricing_method="retail_price_cognitive_service",
            sku_name=resource.get("sku_name") or resource.get("sku"),
            quantity=resource.get("quantity"),
            usage_based=True,
        )

    def _price_snapshot(self, resource: dict):
        return self._price_meter_resource(
            resource,
            service_name="Storage",
            pricing_method="retail_price_snapshot",
            sku_name=resource.get("sku_name") or resource.get("sku"),
            quantity=resource.get("disk_size_gb"),
            usage_based=True,
        )

    def _price_zero_cost(self, resource: dict):
        return self._unavailable_result(resource, "unsupported", "Resource has no direct instance charge")

    @staticmethod
    def _zero_cost_result(resource: dict, reason: str):
        return {
            "resource_id": resource.get("id"),
            "resource_name": resource.get("name", ""),
            "resource_type": resource.get("type", "").lower(),
            "service_name": resource.get("type", "").split("/")[0],
            "monthly_cost": None,
            "cost_last_30_days": None,
            "currency": None,
            "cost_data_available": False,
            "cost_status": "unavailable",
            "cost_source": "none",
            "pricing_method": "cost_unavailable",
            "pricing_unit": "Not applicable",
            "pricing_validated": True,
            "pricing_selection": "non_billable_resource",
            "pricing_warning": reason,
            "region": (resource.get("location") or "").lower().strip(),
            "sku": resource.get("sku_name") or resource.get("sku") or None,
        }

    def _price_nat_gateway(self, resource: dict):
        return self._price_meter_resource(
            resource,
            service_name="Virtual Network",
            pricing_method="retail_price_nat_gateway",
            sku_name=resource.get("sku_name") or resource.get("sku"),
        )

    def _price_network_gateway(self, resource: dict):
        return self._price_meter_resource(
            resource,
            service_name="VPN Gateway",
            pricing_method="retail_price_network_gateway",
            sku_name=resource.get("sku_name") or resource.get("sku"),
        )

    def _price_meter_resource(
        self,
        resource: dict,
        service_name: str,
        pricing_method: str,
        sku_name: str | None = None,
        meter_name: str | None = None,
        quantity: float | None = None,
        usage_based: bool = False,
    ):
        region = (resource.get("location") or "").lower().strip()
        if not region:
            return self._zero_cost_result(resource, "Retail pricing unresolved: region unavailable")
        price = self.pricing.get_retail_price(
            service_name=service_name,
            region=region,
            sku_name=sku_name or None,
            meter_name=meter_name or None,
        )
        if not price:
            return self._zero_cost_result(
                resource,
                f"Retail pricing unresolved: no price match for {service_name}",
            )
        if usage_based and quantity is None:
            result = self._zero_cost_result(
                resource,
                "Usage quantity unavailable; no cost estimated",
            )
            result.update({
                "service_name": service_name,
                "pricing_method": f"{pricing_method}_quantity_unavailable",
                "pricing_warning": "Usage quantity unavailable; no cost estimated",
                "pricing_unit": price.get("unit_of_measure"),
                "meter_name": price.get("meter_name"),
                "product_name": price.get("product_name"),
                "currency": price.get("currency", "USD"),
            })
            return result
        quantity = float(quantity if quantity is not None else self.HOURS_PER_MONTH)
        unit = str(price.get("unit_of_measure") or "").lower()
        monthly_cost = float(price["retail_price"]) * quantity
        if "hour" in unit and quantity == self.HOURS_PER_MONTH:
            monthly_cost = CostCalculator.hourly_to_monthly(float(price["retail_price"]))
        return {
            "resource_id": resource.get("id"),
            "resource_name": resource.get("name", ""),
            "resource_type": resource.get("type", "").lower(),
            "service_name": service_name,
            "service_family": price.get("service_family"),
            "monthly_cost": round(monthly_cost, 2),
            "cost_last_30_days": round(monthly_cost, 2),
            "currency": price.get("currency", "USD"),
            "cost_data_available": True,
            "pricing_method": pricing_method,
            "pricing_unit": price.get("unit_of_measure"),
            "estimated_quantity": quantity,
            "estimated_hours": self.HOURS_PER_MONTH if quantity == self.HOURS_PER_MONTH else None,
            "meter_name": price.get("meter_name"),
            "product_name": price.get("product_name"),
            "sku": resource.get("sku_name") or resource.get("sku") or None,
            "pricing_sku": price.get("sku_name"),
            "region": region,
            "pricing_validated": True,
            "pricing_selection": "retail_meter",
            "pricing_warning": None,
        }
