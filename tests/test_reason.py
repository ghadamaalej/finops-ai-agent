from app.agent.nodes import reason as reason_node


def test_reason(monkeypatch):
    monkeypatch.setattr(
        reason_node,
        "ask_llm",
        lambda _prompt: (
            '{"title":"Review capacity",'
            '"action":"Review and resize capacity",'
            '"priority":"Medium",'
            '"implementation_risk":"Medium",'
            '"execution_plan":["Obtain approval"],'
            '"explanation":"Review the workload."}'
        ),
    )
    state = {
        "issues": [
            {
                "id": "issue-test",
                "issue_type": "VM_RIGHTSIZING",
                "resource_id": "vm-test",
                "resource_name": "vm-test",
                "monthly_cost": 100,
                "current_monthly_cost": 100,
                "estimated_monthly_savings": 70,
                "severity": "Medium",
                "confidence": 0.6,
                "currency": "USD",
                "cost_source": "Azure Retail Prices",
                "cost_type": "estimated",
                "is_estimated": True,
                "cost_data_available": True,
                "evidence": {
                    "cpu_average": 1.0,
                    "cpu_max": 10.0,
                    "savings_method": "heuristic_rightsizing",
                },
            }
        ],
        "memory_context": [],
    }

    result = reason_node.reason(state)

    assert len(result["recommendations"]) == 1
    recommendation = result["recommendations"][0]
    assert recommendation.current_cost == 100
    assert recommendation.estimated_savings == 70
    assert recommendation.observed_cpu_average_percent == 1.0


def test_cost_baseline_survives_resource_id_match_and_creates_valid_recommendation(monkeypatch):
    monkeypatch.setattr(
        reason_node,
        "ask_llm",
        lambda _prompt: (
            '{"title":"Review capacity",'
            '"action":"Review and resize capacity",'
            '"priority":"Medium",'
            '"implementation_risk":"Medium",'
            '"execution_plan":["Obtain approval"],'
            '"explanation":"Review the workload."}'
        ),
    )

    issue = {
        "id": "issue-low-cpu",
        "issue_type": "VM_RIGHTSIZING",
        "resource_id": "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/VM-LOW-CPU",
        "resource_name": "VM-LOW-CPU",
        "monthly_cost": 88.33,
        "current_monthly_cost": 88.33,
        "estimated_monthly_savings": 44.16,
        "severity": "Medium",
        "confidence": 0.55,
        "currency": "USD",
        "cost_source": "Azure Retail Prices",
        "cost_type": "estimated",
        "is_estimated": True,
        "cost_data_available": True,
        "evidence": {
            "cpu_average": 5.0,
            "cpu_max": 10.0,
            "savings_method": "heuristic_rightsizing",
        },
    }

    result = reason_node.reason({"issues": [issue], "memory_context": []})

    assert len(result["recommendations"]) == 1
    recommendation = result["recommendations"][0]
    assert recommendation.resource_id == issue["resource_id"]
    assert recommendation.current_cost == 88.33
    assert recommendation.estimated_savings == 44.16
    assert recommendation.requires_approval is True
