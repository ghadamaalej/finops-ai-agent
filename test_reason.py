from app.agent.nodes.reason import reason

state = {
    "issues": [
        {
            "id": "test-vm-001",
            "issue_type": "VM_RIGHTSIZING",
            "resource_type": "Microsoft.Compute/virtualMachines",
            "resource_id": "/subscriptions/test/resourceGroups/test/providers/Microsoft.Compute/virtualMachines/test-vm",
            "resource_name": "test-vm",
            "severity": "Medium",
            "current_monthly_cost": 100.0,
            "estimated_monthly_savings": 30.0,
            "cost_source": "Azure Retail Prices",
            "cost_type": "estimated",
            "is_estimated": True,
            "cost_data_available": True,
            "confidence": 0.9,
            "currency": "USD",
            "evidence": {
                "cpu_average": 8.5,
                "cpu_max": 15.2,
                "vm_size": "Standard_D2s_v6",
                "currency": "USD",
                "cost_source": "Azure Retail Prices",
                "cost_type": "estimated",
                "is_estimated": True,
                "cost_data_available": True,
                "savings_method": "heuristic_rightsizing"
            }
        }
    ]
}

result = reason(state)

print("\n===== REASON TEST =====")
print("Recommendations:", len(result["recommendations"]))
print("Errors:", result["recommendation_error"])

for recommendation in result["recommendations"]:
    if hasattr(recommendation, "model_dump"):
        print(recommendation.model_dump(mode="json"))
    else:
        print(recommendation)
