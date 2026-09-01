import uuid

from app.models.issue import Issue
from app.services.savings_calculator import SavingsCalculator


class PerformanceAnalyzer:

    def __init__(self):

        self.savings_calculator = (
            SavingsCalculator()
        )

    @staticmethod
    def normalize_resource_id(
        resource_id
    ):

        if not resource_id:
            return None

        return (
            str(resource_id)
            .strip()
            .rstrip("/")
            .lower()
        )

    def analyze(self, context):

        issues = []

        resources_by_id = {

            self.normalize_resource_id(
                r.id
            ): r

            for r in context.resources

            if r.id
        }

        costs_by_resource_id = {

            self.normalize_resource_id(
                c.resource_id
            ): c

            for c in context.resource_costs

            if c.resource_id
        }

        print()
        print(
            "================ PERFORMANCE ANALYZER "
            "================"
        )

        print(
            f"Performance metrics : "
            f"{len(context.metrics)}"
        )

        print(
            f"Azure cost records  : "
            f"{len(context.resource_costs)}"
        )

        for metric in context.metrics:

            if metric.cpu_average is None:

                continue

            resource_id = (
                self.normalize_resource_id(
                    metric.resource_id
                )
            )

            if not resource_id:

                continue

            resource = (
                resources_by_id.get(
                    resource_id
                )
            )

            if not resource:

                print(
                    f"[WARNING] Resource not found: "
                    f"{metric.resource_id}"
                )

                continue

            resource_cost = (
                costs_by_resource_id.get(
                    resource_id
                )
            )

            # Keep high-CPU findings valid even when no retail-cost record
            # exists for the resource.
            monthly_cost = 0.0
            currency = None

            if resource_cost is None:

                print(
                    f"[NO COST] "
                    f"{resource.name} | "
                    f"CPU={metric.cpu_average:.2f}%"
                )

                if metric.cpu_average > 85:

                    issues.append(
                        Issue(

                            id=str(
                                uuid.uuid4()
                            ),

                            category="Performance",

                            issue_type="HighCPU",

                            severity="Medium",

                            confidence=0.90,

                            resource_id=resource.id,

                            resource_name=resource.name,

                            resource_type=resource.type,

                            description=(
                                "Resource consistently "
                                "has high CPU usage"
                            ),

                            evidence={

                            "cpu_average":
                                metric.cpu_average,

                            "cpu_max":
                                metric.cpu_max,

                            "monthly_cost":
                                monthly_cost,

                            "currency":
                                currency,

                            "cost_source":
                                getattr(
                                    resource_cost,
                                    "cost_source",
                                    None
                                ),

                            "cost_type":
                                getattr(
                                    resource_cost,
                                    "cost_type",
                                    None
                                ),

                            "is_estimated":
                                getattr(
                                    resource_cost,
                                    "is_estimated",
                                    True
                                ),

                            "cost_data_available":
                                getattr(
                                    resource_cost,
                                    "cost_data_available",
                                    True
                                )

                        },

                        current_monthly_cost=
                            monthly_cost,

                        estimated_monthly_savings=0,

                        cost_source=
                            getattr(
                                resource_cost,
                                "cost_source",
                                None
                            ),

                        cost_type=
                            getattr(
                                resource_cost,
                                "cost_type",
                                None
                            ),

                        is_estimated=
                            getattr(
                                resource_cost,
                                "is_estimated",
                                True
                            ),

                        currency=
                            currency,

                        cost_data_available=
                            getattr(
                                resource_cost,
                                "cost_data_available",
                                True
                            ),

                        hourly_price=
                            getattr(
                                resource_cost,
                                "hourly_price",
                                None
                            ),

                        estimated_hours=
                            getattr(
                                resource_cost,
                                "estimated_hours",
                                None
                            ),

                        business_impact=(
                            "Application performance "
                            "degradation"
                        ),

                        risk_score=40,

                        detected_by=(
                            "performance_analyzer"
                        )
                    )
                )

                continue

            monthly_cost = float(
                resource_cost.monthly_cost or 0
            )

            currency = (
                resource_cost.currency
            )

            print(
                f"[Performance] "
                f"{resource.name} | "
                f"CPU={metric.cpu_average:.2f}% | "
                f"Cost={monthly_cost:.2f} "
                f"{currency or ''}"
            )

            if metric.cpu_average > 85:

                issues.append(

                    Issue(

                        id=str(
                            uuid.uuid4()
                        ),

                        category="Performance",

                        issue_type="HighCPU",

                        severity="Medium",

                        confidence=0.90,

                        resource_id=resource.id,

                        resource_name=resource.name,

                        resource_type=resource.type,

                        description=(
                            "Resource consistently "
                            "has high CPU usage"
                        ),

                        evidence={

                            "cpu_average":
                                metric.cpu_average,

                            "cpu_max":
                                metric.cpu_max,

                            "monthly_cost":
                                monthly_cost,

                            "currency":
                                currency,

                            "cost_available":
                                True

                        },

                        estimated_monthly_savings=0,

                        business_impact=(
                            "Application performance "
                            "degradation"
                        ),

                        risk_score=40,

                        detected_by=(
                            "performance_analyzer"
                        )
                    )
                )

            elif metric.cpu_average < 10:

                if monthly_cost <= 0:

                    print(
                        f"[SKIP SAVINGS] "
                        f"{resource.name} | "
                        f"CPU={metric.cpu_average:.2f}% | "
                        f"Cost={monthly_cost:.2f}"
                    )

                    continue

                savings_result = (
                    self.savings_calculator
                    .estimate_rightsize_savings(

                        monthly_cost=
                            monthly_cost,

                        utilization=
                            metric.cpu_average
                    )
                )

                estimated_savings = float(
                    savings_result.get(
                        "estimated_savings",
                        0
                    ) or 0
                )

                confidence = float(
                    savings_result.get(
                        "confidence",
                        0
                    ) or 0
                )

                print(
                    f"[Savings] "
                    f"{resource.name} | "
                    f"Cost={monthly_cost:.2f} "
                    f"{currency or ''} | "
                    f"CPU={metric.cpu_average:.2f}% | "
                    f"Estimated Savings="
                    f"{estimated_savings:.2f}"
                )
                if estimated_savings <= 0:

                    continue

                issues.append(

    Issue(

        # -----------------------------------------------------
        # Identity
        # -----------------------------------------------------

        id=str(
            uuid.uuid4()
        ),

        category="Performance",

        issue_type="VM_RIGHTSIZING",

        severity="Medium",

        confidence=confidence,

        resource_id=resource.id,

        resource_name=resource.name,

        resource_type=resource.type,

        description=(
            "Resource capacity exceeds "
            "workload needs"
        ),

        # -----------------------------------------------------
        # Detailed evidence
        # -----------------------------------------------------

        evidence={

            "cpu_average":
                metric.cpu_average,

            "cpu_max":
                metric.cpu_max,

            "vm_size": resource.sku,

            "region": resource.location,

            "monthly_cost":
                monthly_cost,

            "currency":
                currency,

            "cost_source":
                getattr(
                    resource_cost,
                    "cost_source",
                    None
                ),

            "cost_type":
                getattr(
                    resource_cost,
                    "cost_type",
                    None
                ),

            "is_estimated":
                getattr(
                    resource_cost,
                    "is_estimated",
                    True
                ),

            "cost_data_available":
                getattr(
                    resource_cost,
                    "cost_data_available",
                    True
                ),

            "hourly_price":
                getattr(
                    resource_cost,
                    "hourly_price",
                    None
                ),

            "estimated_hours":
                getattr(
                    resource_cost,
                    "estimated_hours",
                    None
                ),

            "savings_method": savings_result.get(
                "savings_method", "heuristic_rightsizing"
            ),

        },

        # =====================================================
        # IMPORTANT:
        # Canonical machine-readable cost fields
        # =====================================================

        current_monthly_cost=
            monthly_cost,

        estimated_monthly_savings=
            estimated_savings,

        cost_source=
            getattr(
                resource_cost,
                "cost_source",
                None
            ),

        cost_type=
            getattr(
                resource_cost,
                "cost_type",
                None
            ),

        is_estimated=
            getattr(
                resource_cost,
                "is_estimated",
                True
            ),

        currency=
            currency,

        cost_data_available=
            getattr(
                resource_cost,
                "cost_data_available",
                True
            ),

        hourly_price=
            getattr(
                resource_cost,
                "hourly_price",
                None
            ),

        estimated_hours=
            getattr(
                resource_cost,
                "estimated_hours",
                None
            ),

        # -----------------------------------------------------
        # Business / risk
        # -----------------------------------------------------

        business_impact=(
            "Opportunity for "
            "right-sizing"
        ),

        risk_score=30,

        detected_by=(
            "performance_analyzer"
        )
    )
)

        print()
        print(
            f"Performance issues generated: "
            f"{len(issues)}"
        )

        return issues
