class ConfidenceCalculator:

    def calculate(
        self,
        historical_success: float,
        forecast_confidence: float,
        analyzer_confidence: float,
        resource_stability: float
    ):

        values = [

            historical_success,
            forecast_confidence,
            analyzer_confidence,
            resource_stability

        ]

        values = [

            max(
                0.0,
                min(
                    float(value),
                    1.0
                )
            )

            for value in values

        ]

        confidence = sum(values) / 4

        return round(
            confidence,
            2
        )