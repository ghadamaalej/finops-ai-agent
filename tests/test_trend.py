from types import SimpleNamespace

from app.learning.trend_analyzer import TrendAnalyzer


def test_increasing_trend():

    history = [
        SimpleNamespace(monthly_cost=100),
        SimpleNamespace(monthly_cost=120),
        SimpleNamespace(monthly_cost=150),
    ]

    analyzer = TrendAnalyzer()

    result = analyzer.analyze(history)

    print("\nTrend:")
    print(result)

    assert result["current_cost"] == 150

    assert result["previous_cost"] == 120

    assert result["growth_percent"] == 25.0

    assert result["trend"] == "increasing"

def test_decreasing_trend():

    history = [
        SimpleNamespace(monthly_cost=200),
        SimpleNamespace(monthly_cost=150),
        SimpleNamespace(monthly_cost=100),
    ]

    analyzer = TrendAnalyzer()

    result = analyzer.analyze(history)

    print("\nDecreasing trend:")
    print(result)

    assert result["growth_percent"] < 0

    assert result["trend"] == "decreasing"

def test_stable_trend():

    history = [
        SimpleNamespace(monthly_cost=100),
        SimpleNamespace(monthly_cost=105),
        SimpleNamespace(monthly_cost=102),
    ]

    analyzer = TrendAnalyzer()

    result = analyzer.analyze(history)

    print("\nStable trend:")
    print(result)

    assert result["trend"] == "stable"