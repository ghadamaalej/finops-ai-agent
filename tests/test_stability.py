from types import SimpleNamespace

from app.learning.stability import ResourceStability


def test_stable_resource():

    history = [

        SimpleNamespace(monthly_cost=100),

        SimpleNamespace(monthly_cost=101),

        SimpleNamespace(monthly_cost=99),

        SimpleNamespace(monthly_cost=100),

    ]

    calculator = ResourceStability()

    result = calculator.calculate(
        history
    )

    print("\nResource stability:")
    print(result)

    assert 0 <= result <= 1

    assert result > 0.9
def test_unstable_resource():

    history = [

        SimpleNamespace(monthly_cost=20),

        SimpleNamespace(monthly_cost=200),

        SimpleNamespace(monthly_cost=30),

        SimpleNamespace(monthly_cost=250),

    ]

    calculator = ResourceStability()

    result = calculator.calculate(
        history
    )

    print("\nUnstable resource:")
    print(result)

    assert 0 <= result <= 1

    assert result < 0.5