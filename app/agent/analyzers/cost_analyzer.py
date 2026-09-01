import logging
from app.services.savings_calculator import SavingsCalculator
class CostAnalyzer:
    logger = logging.getLogger(__name__)

    def __init__(self):
        self.calculator = SavingsCalculator()

    def analyze(self, intelligence):
        """
        Analyze FinOps intelligence context for
        underutilized resources with measurable
        estimated cost savings.

        IMPORTANT:
        Cost values from Azure Retail Prices are
        ESTIMATES, not actual Azure consumption costs.
        """

        if intelligence is None:
            return []

        issues = []

        cost_lookup = {
            str(cost.resource_id).lower(): cost
            for cost in intelligence.resource_costs
            if cost.resource_id
        }

        resource_lookup = {
            str(resource.id).lower(): resource
            for resource in intelligence.resources
            if resource.id
        }

        for metric in intelligence.metrics:

            resource_id = metric.resource_id
            normalized_resource_id = str(resource_id).lower() if resource_id else None

            if not resource_id:
                continue

            resource = resource_lookup.get(normalized_resource_id)
            resource_type = (resource.type if resource else metric.resource_type or "").casefold()
            resource_cost = cost_lookup.get(normalized_resource_id)
            configuration_available = bool(resource and (resource.sku or resource.configuration))
            self.logger.info(
                "finops evidence: resource_id=%s resource_type=%s metrics_collected=%s configuration_collected=%s cost_linked=%s analyzer=cost_analyzer",
                resource_id, resource_type, metric.metric_available, configuration_available, resource_cost is not None,
            )
            # VM CPU is evidence for VM rightsizing only. Other resource types
            # require their own analyzers and must never be treated as VMs.
            if resource_type != "microsoft.compute/virtualmachines" or not metric.metric_available or not configuration_available or metric.cpu_average is None:
                continue
            cpu_average = float(metric.cpu_average)

            cpu_max = (
                float(metric.cpu_max)
                if metric.cpu_max is not None
                else None
            )

            if cpu_average >= 15:
                continue

            if resource_cost is None or not resource_cost.cost_data_available or resource_cost.monthly_cost is None:

                issues.append(
                    {
                        "resource_id": resource_id,

                        "resource_name": (
                            resource.name
                            if resource
                            else ""
                        ),

                        "resource_type": (
                            resource.type
                            if resource
                            else None
                        ),

                        "issue": "VM_RIGHTSIZING",

                        "issue_type": "VM_RIGHTSIZING",

                        "category":
                            "Cost Optimization",

                        "description":
                            (
                                "Resource CPU utilization "
                                "is below the configured "
                                "threshold, but no cost "
                                "data is available."
                            ),

                        "cpu":
                            cpu_average,

                        "cpu_max":
                            cpu_max,

                        "monthly_cost":
                            0.0,

                        "current_monthly_cost":
                            0.0,

                        "estimated_savings":
                            0.0,

                        "estimated_monthly_savings":
                            0.0,

                        "currency":
                            None,

                        "cost_source":
                            "Unavailable",

                        "cost_type":
                            "unavailable",

                        "is_estimated":
                            False,

                        "cost_data_available":
                            False,

                        "cost_warning":
                            "No cost data available",

                        "severity":
                            "Low",

                        "confidence":
                            0.4,

                        "detected_by":
                            "cost_analyzer",
                    }
                )

                continue

            monthly_cost = float(
                resource_cost.monthly_cost or 0.0
            )

            if monthly_cost <= 0:
                continue

            savings_result = (
                self.calculator.estimate_rightsize_savings(
                    monthly_cost,
                    cpu_average
                )
            )

            estimated_savings = round(
                float(
                    savings_result.get(
                        "estimated_savings",
                        0.0
                    )
                ),
                2
            )

            savings_confidence = float(
                savings_result.get(
                    "confidence",
                    0.0
                )
            )

            if estimated_savings <= 0:
                continue



            savings_ratio = (
                estimated_savings / monthly_cost
                if monthly_cost > 0
                else 0.0
            )

            if estimated_savings >= 100:
                severity = "High"

            elif estimated_savings >= 25:
                severity = "Medium"

            else:
                severity = "Low"


            issue = {
                "resource_id":
                    resource_id,

                "resource_name":
                    resource_cost.resource_name,

                "resource_type":
                    resource_cost.resource_type,

                "issue": "VM_RIGHTSIZING",

                "issue_type": "VM_RIGHTSIZING",

                "category":
                    "Cost Optimization",

                "description":
                    (
                        "Virtual machine CPU utilization "
                        "is below the configured threshold."
                    ),

                "cpu":
                    cpu_average,

                "cpu_max":
                    cpu_max,

                "evidence": {
                    "cpu_average": cpu_average,
                    "cpu_max": cpu_max,
                    "vm_size": (
                        resource.sku
                        if resource
                        else resource_cost.sku
                    ),
                    "region": (
                        resource.location
                        if resource
                        else resource_cost.region
                    ),
                    "savings_method": savings_result.get(
                        "savings_method",
                        "heuristic_rightsizing",
                    ),
                },

                "utilization":
                    savings_result.get(
                        "utilization",
                        cpu_average
                    ),

                "monthly_cost":
                    monthly_cost,

                "current_monthly_cost":
                    monthly_cost,

                "current_cost":
                    savings_result.get(
                        "current_cost",
                        monthly_cost
                    ),

                "estimated_savings":
                    estimated_savings,

                "estimated_monthly_savings":
                    estimated_savings,

                "savings_ratio":
                    round(
                        savings_ratio,
                        3
                    ),

                "savings_confidence":
                    savings_confidence,

                "savings_method": savings_result.get(
                    "savings_method",
                    "heuristic_rightsizing",
                ),

                "currency":
                    resource_cost.currency,

                "cost_source":
                    resource_cost.cost_source,

                "cost_type":
                    resource_cost.cost_type,

                "is_estimated":
                    resource_cost.is_estimated,

                "cost_data_available":
                    resource_cost.cost_data_available,

                "hourly_price":
                    resource_cost.hourly_price,

                "estimated_hours":
                    resource_cost.estimated_hours,

                "estimated_quantity":
                    resource_cost.estimated_quantity,

                "pricing_method":
                    resource_cost.pricing_method,

                "pricing_unit":
                    resource_cost.pricing_unit,

                "meter_name":
                    resource_cost.meter_name,

                "arm_sku_name":
                    resource_cost.arm_sku_name,

                "product_name":
                    resource_cost.product_name,

                "sku":
                    resource_cost.sku,

                "region":
                    resource_cost.region,

                "pricing_validated":
                    resource_cost.pricing_validated,


                "severity":
                    severity,

                "confidence":
                    savings_confidence,

                "detected_by":
                    "cost_analyzer",
            }

            issues.append(issue)
            self.logger.info(
                "finops evidence: resource_id=%s resource_type=%s metrics_collected=%s configuration_collected=%s cost_linked=%s analyzer_result=%s",
                resource_id, resource_type, metric.metric_available, configuration_available, True, issue["issue_type"],
            )

        return issues
