from types import SimpleNamespace

from app.learning.history import HistoricalSuccess


def test_historical_success():

    executions = [

        SimpleNamespace(status="SUCCESS"),

        SimpleNamespace(status="SUCCESS"),

        SimpleNamespace(status="FAILED"),

        SimpleNamespace(status="SUCCESS"),

        SimpleNamespace(status="FAILED"),

    ]

    calculator = HistoricalSuccess()

    result = calculator.calculate(
        executions
    )

    print("\nHistorical success:")
    print(result)

    assert result == 0.6

def test_no_historical_executions():

    calculator = HistoricalSuccess()

    result = calculator.calculate([])

    print("\nNo executions:")
    print(result)

    assert result == 0.5