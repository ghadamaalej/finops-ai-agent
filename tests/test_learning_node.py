from types import SimpleNamespace

from app.agent.nodes.learning import learn


def test_learning_node():

    history = [

        SimpleNamespace(monthly_cost=100),

        SimpleNamespace(monthly_cost=120),

        SimpleNamespace(monthly_cost=140),

        SimpleNamespace(monthly_cost=160),

    ]


    executions = [

        SimpleNamespace(status="SUCCESS"),

        SimpleNamespace(status="SUCCESS"),

        SimpleNamespace(status="SUCCESS"),

        SimpleNamespace(status="FAILED"),

        SimpleNamespace(status="SUCCESS"),

    ]


    state = {

        "cost_history": history,

        "execution_history": executions,

        "analyzer_confidence": 0.90,

        "verification_report": {

            "expected_savings": 100,

            "realized_savings": 90

        }

    }


    result = learn(state)


    print("\n================ LEARNING RESULT ================")

    print(result["learning"])

    print("==================================================")


    learning = result["learning"]


    assert "savings_accuracy" in learning

    assert "historical_success" in learning

    assert "forecast_confidence" in learning

    assert "resource_stability" in learning

    assert "analyzer_confidence" in learning

    assert "recommendation_confidence" in learning

    assert "trend" in learning

    assert "forecast" in learning


    assert learning["savings_accuracy"] == 0.9

    assert learning["historical_success"] == 0.8

    assert 0 <= learning["recommendation_confidence"] <= 1