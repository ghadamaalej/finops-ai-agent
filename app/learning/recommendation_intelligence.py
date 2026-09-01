from app.learning.confidence import ConfidenceCalculator
from app.learning.forecast import CostForecaster
from app.learning.history import HistoricalSuccess
from app.learning.stability import ResourceStability


class RecommendationIntelligence:

    def __init__(self):

        self.confidence = ConfidenceCalculator()

        self.forecaster = CostForecaster()

        self.history = HistoricalSuccess()

        self.stability = ResourceStability()


    def analyze(
        self,
        cost_history,
        execution_history,
        analyzer_confidence=0.5
    ):

        historical_success = (
            self.history.calculate(
                execution_history
            )
        )


        forecast = (
            self.forecaster.predict_next_month(
                cost_history
            )
        )


        resource_stability = (
            self.stability.calculate(
                cost_history
            )
        )


        final_confidence = (
            self.confidence.calculate(

                historical_success,

                forecast.get(
                    "confidence",
                    0.5
                ),

                analyzer_confidence,

                resource_stability

            )
        )


        return {

            "historical_success":
                historical_success,

            "forecast":
                forecast,

            "resource_stability":
                resource_stability,

            "analyzer_confidence":
                analyzer_confidence,

            "recommendation_confidence":
                final_confidence

        }