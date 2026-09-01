from types import SimpleNamespace

from app.learning.forecast import CostForecaster


def test_forecast_next_month():

    history = [
        SimpleNamespace(monthly_cost=100),
        SimpleNamespace(monthly_cost=120),
        SimpleNamespace(monthly_cost=140),
        SimpleNamespace(monthly_cost=160),
    ]

    forecaster = CostForecaster()

    result = forecaster.predict_next_month(history)

    print("\nForecast result:")
    print(result)

    assert "predicted_next_month_cost" in result
    assert "confidence" in result

    assert result["predicted_next_month_cost"] > 0

    assert 0 <= result["confidence"] <= 1


def test_forecast_without_enough_history():

    history = [
        SimpleNamespace(monthly_cost=100)
    ]

    forecaster = CostForecaster()

    result = forecaster.predict_next_month(history)

    print("\nInsufficient history:")
    print(result)

    assert result["predicted_next_month_cost"] == 0
    assert result["confidence"] == 0