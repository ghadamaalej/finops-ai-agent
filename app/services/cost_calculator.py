class CostCalculator:

    HOURS_PER_MONTH = 730

    @staticmethod
    def hourly_to_monthly(
        hourly_price: float
    ) -> float:

        return round(
            hourly_price *
            CostCalculator.HOURS_PER_MONTH,
            2
        )

    @staticmethod
    def monthly_gb_price(
        price_per_gb: float,
        size_gb: int
    ) -> float:

        if price_per_gb <= 0:
            return 0.0

        if size_gb <= 0:
            return 0.0

        return round(
            price_per_gb * size_gb,
            2
        )