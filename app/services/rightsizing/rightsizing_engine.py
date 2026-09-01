from app.services.rightsizing.sku_candidate import SkuCandidate
class RightsizingEngine:

    HOURS_PER_MONTH = 730

    def recommend(
        self,
        current_sku,
        current_cost,
        region,
        available_sizes,
        cpu_average,
        memory_average=None,
    ):

        candidates = []

        for sku in available_sizes:

            if sku["name"] == current_sku:
                continue

            if sku["monthly_cost"] >= current_cost:
                continue

            if not self._cpu_safe(
                cpu_average
            ):
                continue

            if (
                memory_average is not None
                and not self._memory_safe(
                    memory_average
                )
            ):
                continue

            savings = (
                current_cost
                - sku["monthly_cost"]
            )

            savings_percent = (
                savings / current_cost
                if current_cost > 0
                else 0
            )

            candidates.append(
                SkuCandidate(
                    sku=sku["name"],
                    hourly_price=sku[
                        "hourly_price"
                    ],
                    monthly_cost=sku[
                        "monthly_cost"
                    ],
                    cpu_compatible=True,
                    memory_compatible=True,
                    savings=savings,
                    savings_percent=savings_percent,
                )
            )

        if not candidates:
            return None

        candidates.sort(
            key=lambda x: x.monthly_cost
        )

        return candidates[0]

    def _cpu_safe(
        self,
        cpu_average,
    ):

        return (
            cpu_average is not None
            and cpu_average < 30
        )

    def _memory_safe(
        self,
        memory_average,
    ):

        return (
            memory_average is not None
            and memory_average < 60
        )