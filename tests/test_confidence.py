from app.learning.confidence import ConfidenceCalculator


def test_confidence_calculation():

    calculator = ConfidenceCalculator()

    result = calculator.calculate(

        historical_success=0.92,

        forecast_confidence=0.88,

        analyzer_confidence=0.95,

        resource_stability=0.91
    )

    print("\nRecommendation confidence:")
    print(result)

    # ConfidenceCalculator returns a two-decimal score.
    assert result == 0.92
