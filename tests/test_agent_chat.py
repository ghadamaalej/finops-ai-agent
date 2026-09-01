from api.agent import (
    CANONICAL_MONTHLY_COST,
    _canonical_summary,
    classify_question_intent,
    _deterministic_chat_answer,
    _answer_addresses_intent,
    _chat_history,
    _evidence_fallback,
    _question_evidence,
    _resource_context,
    _approval_response,
    _chat_recommendations,
    _chat_response,
    _format_resource_answer,
    _metrics_response,
    _metrics_visualizations,
    _sku_comparison_response,
    _resource_listing_response,
    _is_approval_question,
    _recommendation_card,
    resolve_question,
)


def summary():
    return {
        "cost": {"monthly": 999, "currency": "USD"},
        "savings": {"potential_monthly": 181.40},
        "resources": {"total": 12},
        "agent": {"pending_approval": 4},
        "security": {"score": 85},
        "governance": {"compliance": 92},
        "performance": {"average_cpu": 31},
        "alerts": [{"title": "Review"}],
        "recommendations": [{"action": "RESIZE"}],
        "recommendations_all": [{"resource_id": "/subscriptions/sub/resourceGroups/RG_GhadaMaalej/providers/Microsoft.Compute/virtualMachines/vm1", "resource_name": "vm1", "action": "RESIZE", "potential_savings": 181.40}, {"resource_id": "/subscriptions/sub/resourceGroups/other/providers/Microsoft.Compute/virtualMachines/TerraformHCPMigration", "resource_name": "TerraformHCPMigration", "action": "STOP", "potential_savings": 42.0}],
        "cost_drivers": [{"service_name": "Compute", "monthly_cost": 100}],
        "cost_resources": [{"resource_id": "/subscriptions/sub/resourceGroups/RG_GhadaMaalej/providers/Microsoft.Compute/virtualMachines/vm1", "resource_name": "vm1", "monthly_cost": 100}, {"resource_id": "/subscriptions/sub/resourceGroups/other/providers/Microsoft.Compute/virtualMachines/TerraformHCPMigration", "resource_name": "TerraformHCPMigration", "monthly_cost": 45}],
    }


def test_chat_route_is_registered_and_cors_preflight_allows_vite_origin():
    from main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)
    schema = client.get("/openapi.json").json()
    response = client.options(
        "/api/agent/chat",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )

    assert "post" in schema["paths"]["/api/agent/chat"]
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
    assert response.headers["access-control-allow-credentials"] == "true"
    assert all(method in response.headers["access-control-allow-methods"] for method in ("GET", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"))
    assert "authorization" in response.headers["access-control-allow-headers"].casefold()
    assert "content-type" in response.headers["access-control-allow-headers"].casefold()


def test_resource_details_route_uses_query_parameter_for_full_azure_resource_ids():
    from main import app
    from fastapi.testclient import TestClient
    resource_id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/disks/OS_disk_winserv2019"
    paths = app.openapi()["paths"]
    assert "/api/dashboard/resources/details" in paths
    assert "resource_id" in paths["/api/dashboard/resources/details"]["get"]["parameters"][0]["name"]
    assert "/api/dashboard/resources/{resource_id:path}/details" not in paths
    client = TestClient(app)
    response = client.get("/api/dashboard/resources/details", params={"resource_id": resource_id})
    assert response.status_code == 401

def test_chat_cost_is_deterministic_and_canonical():
    result = _deterministic_chat_answer("What is my monthly cost?", _canonical_summary(summary()))
    assert result["answer"] == "The current monthly cost is $1,492.08 USD."
    assert result["evidence"][0]["value"] == CANONICAL_MONTHLY_COST

def test_question_intents_cover_representative_domains():
    questions = {
        "cost": "What is my monthly cost?", "savings": "How can I save money?", "resources": "Which resources cost most?",
        "performance": "Are there performance issues?", "metrics": "Display the metrics and usage of finops-test-vm", "security": "Any security findings?", "governance": "What is our compliance status?",
        "recommendations": "What recommendations do you have?", "actions": "What actions did the agent execute?",
        "finops_summary": "Summarize my FinOps health", "out_of_scope": "What is the weather?",
    }
    assert {classify_question_intent(question) for intent, question in questions.items()} == set(questions)


def test_explicit_resource_recommendation_remains_in_recommendation_flow():
    data = _canonical_summary(summary())
    assert resolve_question("what do you recommend for finops-test-vm?", data)["intent"] == "recommendations"


def test_sku_follow_up_retains_resolved_resource_and_does_not_use_global_cost():
    resource_id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/jenkins-vm"
    data = {"subscription_id": "sub", "cost": {"currency": "USD"}, "resource_inventory": [{"resource_id": resource_id, "resource_name": "jenkins-vm", "resource_type": "Microsoft.Compute/virtualMachines", "configuration": {"sku": "Standard_D4s_v5"}}], "cost_resources": [{"resource_id": resource_id, "resource_name": "jenkins-vm", "monthly_cost": 12.5}], "recommendations_all": [], "performance": {"resources": []}}
    first = resolve_question("what do you recommend for jenkins-vm?", data)
    follow_up = resolve_question("compare smaller SKUs", data, [{"role": "user", "content": "what do you recommend for jenkins-vm?"}])
    assert first["target_resources"][0]["resource_id"] == resource_id
    assert follow_up["target_resources"] == first["target_resources"]
    context = _resource_context(follow_up, data, follow_up["intent"])
    response = _sku_comparison_response(context, follow_up, "request")
    assert response["resource_id"] == resource_id
    assert "$1492.08" not in response["answer"]
    assert "Savings not quantifiable" in response["answer"]


def test_resource_metrics_query_uses_collected_azure_monitor_values_without_recommendation():
    resource_id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/finops-test-vm"
    data = {"cost": {"currency": "USD"}, "resource_inventory": [{"resource_id": resource_id, "resource_name": "finops-test-vm", "resource_type": "Microsoft.Compute/virtualMachines", "configuration": {}}], "cost_resources": [], "recommendations_all": [{"resource_id": resource_id, "action": "resize_vm", "potential_savings": 42}], "performance": {"resources": [{"resource_id": resource_id, "metric_names": ["Percentage CPU", "Network In Total", "Network Out Total", "Disk Read Operations/Sec", "Disk Write Operations/Sec"], "values": {"Percentage CPU": 7.8, "Network In Total": 1024, "Network Out Total": 2048, "Disk Read Operations/Sec": 1.5, "Disk Write Operations/Sec": 2.5}, "collected_days": 30, "collected_at": "2026-01-01T00:00:00+00:00"}]}}
    resolution = resolve_question("display the metrics and usage of finops-test-vm", data)
    assert resolution["intent"] == "metrics"
    context = _resource_context(resolution, data, resolution["intent"])
    response = _metrics_response(context, resolution, "request")
    assert response["recommendations"] == []
    assert "resize_vm" not in response["answer"]
    assert response["evidence"][0] == {"label": "Percentage CPU", "metric_name": "Percentage CPU", "value": 7.8, "unit": "%", "period": "last 30 days", "resource_name": "finops-test-vm", "source": "Azure Monitor", "status": "available", "collected_at": "2026-01-01T00:00:00+00:00"}
    assert {item["metric_name"] for item in response["evidence"]} == set(data["performance"]["resources"][0]["metric_names"])
    assert {chart["type"] for chart in response["visualizations"]} == {"bar"}
    assert {chart["unit"] for chart in response["visualizations"]} == {"%", "bytes", "operations/sec"}


def test_historical_metrics_use_line_visualization_without_fabricating_points():
    metric = {"metric_name": "Percentage CPU", "unit": "%", "timeseries": [{"timestamp": "2026-01-01T00:00:00Z", "value": 5.2}, {"timestamp": "2026-01-01T01:00:00Z", "value": 8.1}]}
    charts = _metrics_visualizations(metric, [])
    assert charts[0]["type"] == "line"
    assert charts[0]["series"][0]["data"] == metric["timeseries"]


def test_missing_metric_data_does_not_create_fabricated_chart_data():
    assert _metrics_visualizations({"metric_name": "Percentage CPU", "unit": "%", "timeseries": []}, [{"metric_name": "Percentage CPU", "value": None, "unit": "%"}]) == []


def test_named_resource_resolution_is_evidence_backed_and_scoped():
    data = _canonical_summary(summary())
    resolution = resolve_question("Analyze TerraformHCPMigration CPU configuration and give me a FinOps recommendation", data)
    assert resolution["target_resources"] == [{"resource_id": "/subscriptions/sub/resourceGroups/other/providers/Microsoft.Compute/virtualMachines/TerraformHCPMigration", "resource_name": "TerraformHCPMigration"}]
    assert {"utilization", "configuration", "savings"}.issubset(resolution["dimensions"])
    context = _resource_context(resolution, data, resolution["intent"])
    assert [item["resource_name"] for item in context["cost_resources"]] == ["TerraformHCPMigration"]
    assert [item["resource_name"] for item in context["recommendations_all"]] == ["TerraformHCPMigration"]
    assert context["performance"]["scope"].startswith("subscription aggregate")


def test_managed_disk_chat_uses_one_cost_evidence_record_and_disk_fallback():
    resource_id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/disks/disk_os_ulysse_vm"
    data = {
        "cost": {"currency": "USD"},
        "resource_inventory": [{"resource_id": resource_id, "resource_name": "disk_os_ulysse_vm", "resource_type": "Microsoft.Compute/disks", "configuration": {"disk_size_gb": 32, "managed_by": "/subscriptions/sub/providers/Microsoft.Compute/virtualMachines/ulysse"}, "configuration_status": "available"}],
        "cost_resources": [{"resource_id": resource_id, "resource_name": "disk_os_ulysse_vm", "resource_type": "Microsoft.Compute/disks", "monthly_cost": 1.18, "cost_source": "Azure Retail Prices", "cost_type": "estimated", "is_estimated": True, "cost_data_available": True, "cost_status": "estimated"}],
        "performance": {"resources": [{"resource_id": resource_id, "resource_type": "Microsoft.Compute/disks", "metric_available": False, "metric_names": ["Composite Disk Read Operations/Sec"], "utilization_status": "unavailable", "metric_unavailable_reason": "azure_monitor_returned_no_datapoints"}]},
        "recommendations_all": [],
    }
    resolution = resolve_question("Analyze disk_os_ulysse_vm", data)
    context = _resource_context(resolution, data, resolution["intent"])
    answer = _format_resource_answer("", context, resolution)
    response = _chat_response("", [], context, resolution, "request")
    assert context["resource_evidence"][0]["cost"] == 1.18
    assert context["resource_evidence"][0]["cost_data_available"] is True
    assert "**Cost:** $1.18/month / estimated / Azure Retail Prices" in answer
    assert "Not quantifiable from available evidence" in answer
    assert "CPU/utilization" not in response["next_step"]
    assert "disk IOPS/throughput and attachment-state" in response["next_step"]


def test_live_disk_evidence_overrides_stale_monitor_failure_and_has_no_deletion_recommendation():
    resource_id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/disks/disk_os_ulysse_vm"
    data = {
        "cost": {"currency": "USD"},
        "resource_inventory": [{"resource_id": resource_id, "resource_name": "disk_os_ulysse_vm", "resource_type": "Microsoft.Compute/disks", "configuration": {"managed_by": "/subscriptions/sub/providers/Microsoft.Compute/virtualMachines/vm-ulysse", "disk_state": "Attached", "sku": "StandardSSD_LRS", "disk_size_gb": 64}, "configuration_status": "available"}],
        "cost_resources": [{"resource_id": resource_id, "resource_name": "disk_os_ulysse_vm", "resource_type": "Microsoft.Compute/disks", "monthly_cost": 1.18, "cost_source": "Azure Retail Prices", "cost_type": "estimated", "is_estimated": True, "cost_data_available": True}],
        "performance": {"resources": [{"resource_id": resource_id, "resource_type": "Microsoft.Compute/disks", "metric_available": True, "values": {"Composite Disk Read Operations/sec": 2.0977, "Composite Disk Write Operations/sec": 3.8907, "Composite Disk Read Bytes/sec": 39755.4327, "Composite Disk Write Bytes/sec": 57322.9165}, "metric_errors": {"DiskPaidBurstIOPS": {"reason": "azure_monitor_returned_no_datapoints"}}, "utilization_status": "available"}]},
        "recommendations_all": [{"resource_id": resource_id, "action": "Collect disk IOPS/throughput/latency and attachment-state evidence before quantifying savings.", "reason": "azure_monitor_query_failed", "potential_savings": 1.18}],
    }
    resolution = resolve_question("Analyze disk_os_ulysse_vm", data)
    context = _resource_context(resolution, data, resolution["intent"])
    answer = _format_resource_answer("", context, resolution)
    response = _chat_response("", [], context, resolution, "request")
    evidence = context["resource_evidence"][0]
    assert evidence["metric_available"] is True
    assert evidence["metrics"]["Composite Disk Read Operations/sec"] == 2.0977
    assert evidence["metric_errors"]["DiskPaidBurstIOPS"]["reason"] == "azure_monitor_returned_no_datapoints"
    assert context["recommendations_all"] == []
    assert "azure_monitor_query_failed" not in answer
    assert "Metrics collected: none" not in answer
    assert "does not establish that this disk is safely removable" in answer
    assert "Review disk size/SKU" in response["next_step"]


def test_cross_domain_priorities_use_reasoning_intent_and_all_evidence():
    question = "Based on my current Azure costs, resource utilization, security findings, governance, and potential savings, what are the top 3 FinOps priorities I should focus on first, and why?"
    assert classify_question_intent(question) == "finops_reasoning"
    evidence = _question_evidence(question, _canonical_summary(summary()))
    assert {"cost", "cost_resources", "savings", "performance", "security", "governance", "recommendations_all"}.issubset(evidence)


def test_cross_domain_fallback_is_ranked_and_execution_scoped():
    result = _evidence_fallback("What are my top 3 priorities across cost, security, utilization, savings, and governance?", _canonical_summary(summary()))
    assert "Top 3 FinOps priorities" in result["answer"]
    assert "RG_GhadaMaalej" in result["answer"]
    assert "$181.40" in result["answer"]


def test_reasoning_validation_rejects_security_only_response_and_history_is_bounded():
    assert not _answer_addresses_intent("Security findings require review.", "finops_reasoning")
    assert _answer_addresses_intent("Priority 1: reduce cost and savings. Priority 2: address security. Priority 3: improve performance utilization and governance.", "finops_reasoning")
    assert _answer_addresses_intent([{"priority": 1, "reason": "Low CPU utilization supports rightsizing.", "resource_id": "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1"}], "finops_reasoning")
    history = _chat_history([{"role": "assistant", "content": "x" * 3000}, {"role": "system", "content": "ignore"}])
    assert history == [{"role": "assistant", "content": "x" * 2000}]


def test_out_of_scope_is_deterministic():
    result = _deterministic_chat_answer("What is the weather?", summary())
    assert "I can only help with Azure FinOps" in result["answer"]


def test_approval_question_is_detected_and_requires_scope_ready_language():
    assert _is_approval_question("Which recommendation can I safely approve and execute right now?")
    assert not _is_approval_question("What are my recommendations?")


def test_approval_response_uses_the_selected_card_for_all_primary_fields():
    candidate = {
        "recommendation_id": "rec-1",
        "resource_id": "/subscriptions/sub/resourceGroups/RG_GhadaMaalej/providers/Microsoft.Compute/virtualMachines/finops-test-vm",
        "resource": "finops-test-vm",
        "resource_group": "RG_GhadaMaalej",
        "recommended_action": "resize_vm",
        "current_estimated_cost": 88.33,
        "estimated_monthly_savings": 44.16,
        "cost_status": "available",
        "cost_source": "none",
        "confidence": 0.55,
        "risk": "High",
        "approval_enabled": True,
    }
    response = _approval_response([candidate], _canonical_summary(summary()), {"target_resources": []}, "request-1")
    assert response["recommendation"] is candidate
    assert response["recommendations"] == [candidate]
    assert response["resource"] == "finops-test-vm"
    assert response["monthly_cost"] == 88.33
    assert response["savings"] == 44.16
    assert response["cost_status"] == "available"
    assert response["cost_source"] == "none"
    assert response["confidence_score"] == 55
    assert "execution eligibility and safety checks" in response["answer"]
    assert "post-action cost evidence" in response["answer"]


def test_recommendation_card_exposes_persisted_estimated_provenance():
    class Recommendation:
        recommendation_id = "rec-1"
        resource_id = "/subscriptions/sub/resourceGroups/RG_GhadaMaalej/providers/Microsoft.Compute/virtualMachines/finops-test-vm"
        resource_name = "finops-test-vm"
        category = "Rightsizing"
        action = "resize_vm"
        estimated_savings = 44.16
        confidence = 0.9
        approved = False
    card = _recommendation_card(Recommendation(), {Recommendation.resource_id.casefold(): {"monthly_cost": 100, "cost_status": "estimated", "cost_source": "Azure Retail Prices", "is_estimated": True}})
    assert card["approval_enabled"] is True
    assert card["resource_group"] == "RG_GhadaMaalej"
    assert card["estimated_monthly_savings"] == 44.16
    assert card["cost_status"] == "estimated"
    assert card["cost_source"] == "Azure Retail Prices"


def test_chat_savings_is_deterministic():
    result = _deterministic_chat_answer("How much potential savings do I have?", summary())
    assert result["answer"] == "The persisted recommendations indicate $181.40 in potential monthly savings."
    assert result["evidence"][0]["value"] == 181.4

def test_health_evidence_is_focused_and_has_local_fallback():
    data = _canonical_summary(summary())
    evidence = _question_evidence("Summarize my FinOps health", data)
    assert "cost_resources" not in evidence
    assert {"cost", "savings", "security", "governance", "performance"}.issubset(evidence)
    fallback = _evidence_fallback("Summarize my FinOps health", data)
    assert "$1,492.08" in fallback["answer"]
    assert fallback["evidence"]


def test_acr_zero_activity_uses_collected_metrics_for_removal_recommendation():
    context = {
        "resource_evidence": [{
            "resource_type": "Microsoft.ContainerRegistry/registries",
            "resource_name": "insomearegistry",
            "resource_group": "rg-acr",
            "metrics": {"StorageUsed": 708 * 1024 * 1024, "TotalPullCount": 0.0014, "TotalPushCount": 0.0014},
            "configuration": {"sku": "Basic", "sku_tier": "Basic", "retention_policy": "disabled", "soft_delete_policy": "disabled"},
            "cost": 18.4,
            "cost_source": "Azure Retail Prices",
            "cost_type": "estimated",
        }],
    }
    resolution = {"target_resources": [{
        "resource_name": "insomearegistry",
        "resource_type": "Microsoft.ContainerRegistry/registries",
    }]}

    answer = _format_resource_answer("", context, resolution)

    assert answer.startswith("### FinOps Analysis - insomearegistry")
    assert "Cost: $18.40/month / estimated / Azure Retail Prices" in answer
    assert "Storage: approximately 708 MB" in answer
    assert "Pull activity: 0.0014" in answer
    assert "Push activity: 0.0014" in answer
    assert "apply_image_retention_policy" in answer
    assert "delete registry" not in answer.casefold()
    assert "downgrade is not available" in answer
    assert "Not quantifiable from available evidence" in answer


def test_exact_jenkins_follow_up_queries_validated_candidate_price_without_global_cost(monkeypatch):
    resource_id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/jenkins-vm"
    data = {"subscription_id": "sub", "cost": {"currency": "USD"}, "resource_inventory": [{"resource_id": resource_id, "resource_name": "jenkins-vm", "resource_type": "Microsoft.Compute/virtualMachines", "location": "westeurope", "configuration": {"sku": "Standard_D4s_v5", "region": "westeurope", "os_type": "Linux"}}], "cost_resources": [{"resource_id": resource_id, "resource_name": "jenkins-vm", "monthly_cost": 185.42}], "recommendations_all": [], "performance": {"resources": []}}
    class FakePricing:
        def get_vm_price(self, region, sku, os_type):
            assert (region, sku, os_type) == ("westeurope", "Standard_D2s_v5", "Linux")
            return {"retail_price": 0.1, "pricing_validated": True}
    monkeypatch.setattr("api.agent.AzureRetailPriceService", FakePricing)
    history = [{"role": "user", "content": "what do you recommend for jenkins-vm?"}]
    resolution = resolve_question("Compare compatible smaller VM SKUs and collect their prices before resizing.", data, history)
    assert resolution["intent"] == "sku_comparison"
    assert resolution["target_resources"] == [{"resource_id": resource_id, "resource_name": "jenkins-vm", "resource_type": "Microsoft.Compute/virtualMachines"}]
    response = _sku_comparison_response(_resource_context(resolution, data, resolution["intent"]), resolution, "request")
    assert response["resource_id"] == resource_id
    assert response["comparisons"][0]["price"] == 73.0
    assert response["comparisons"][0]["savings"] == 112.42
    assert "$1492.08" not in response["answer"]


def test_exact_metric_history_wording_routes_to_metrics_but_recommendation_wording_does_not():
    assert classify_question_intent("show me the CPU usage of jenkins-vm over time") == "metrics_history"
    assert classify_question_intent("what do you recommend for jenkins-vm based on its CPU usage?") == "recommendations"


def test_missing_cpu_history_returns_aggregate_notice_without_visualization():
    resource_id = "/subscriptions/sub/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/jenkins-vm"
    data = {"cost": {"currency": "USD"}, "resource_inventory": [{"resource_id": resource_id, "resource_name": "jenkins-vm", "resource_type": "Microsoft.Compute/virtualMachines", "configuration": {"sku": "Standard_D4s_v5"}}], "cost_resources": [], "recommendations_all": [{"resource_id": resource_id, "action": "resize_vm"}], "performance": {"resources": [{"resource_id": resource_id, "values": {"Percentage CPU": 0.3222}, "metric_names": ["Percentage CPU"], "timeseries": []}]}}
    resolution = resolve_question("show me the CPU usage of jenkins-vm over time", data)
    response = _metrics_response(_resource_context(resolution, data, resolution["intent"]), resolution, "request")
    assert response["intent"] == "metrics_history"
    assert response["visualizations"] == []
    assert response["recommendations"] == []
    assert "Historical CPU datapoints are unavailable for jenkins-vm" in response["answer"]
    assert "0.3222%" in response["answer"]


def test_follow_up_savings_uses_explicit_sku_context(monkeypatch):
    resource_id = "/subscriptions/sub/resourceGroups/RG-ZINEDINEDRIDI/providers/Microsoft.Compute/virtualMachines/JENKINS-VM"
    data = {"cost": {"currency": "USD"}, "resource_inventory": [{"resource_id": resource_id, "resource_name": "jenkins-vm", "resource_type": "Microsoft.Compute/virtualMachines", "resource_group": "RG-ZINEDINEDRIDI", "location": "westeurope", "configuration": {"sku": "Standard_D4s_v5", "os_type": "Linux"}}], "cost_resources": [{"resource_id": resource_id, "resource_name": "jenkins-vm", "monthly_cost": 185.42}], "recommendations_all": [], "performance": {"resources": []}}
    class FakePricing:
        def get_vm_price(self, region, sku, os_type):
            return {"retail_price": (185.42 - 92.71) / 730, "pricing_validated": True}
    monkeypatch.setattr("api.agent.AzureRetailPriceService", FakePricing)
    context = {"resource": {"name": "jenkins-vm", "resource_id": resource_id, "type": "Microsoft.Compute/virtualMachines"}, "configuration": {"sku": "Standard_D4s_v5"}, "last_intent": "sku_comparison"}
    resolution = resolve_question("how much could I save?", data, conversation_context=context)
    assert resolution["intent"] == "savings_analysis"
    assert resolution["target_resources"][0]["resource_id"] == resource_id
    result = _sku_comparison_response(_resource_context(resolution, data, resolution["intent"]), resolution, "r")
    assert result["savings"] == {"monthly": 92.71, "validated": True}
    assert result["best_candidate"]["estimated_savings"] == 92.71 if "estimated_savings" in result["best_candidate"] else result["best_candidate"]["savings"] == 92.71

def test_resource_listing_is_inventory_scoped_and_has_no_recommendation_data():
    data = {"resource_inventory": [{"resource_id": "/subscriptions/sub/resourceGroups/RG_GhadaMaalej/providers/Microsoft.Compute/virtualMachines/vm1", "resource_name": "vm1", "resource_type": "Microsoft.Compute/virtualMachines", "resource_group": "RG_GhadaMaalej", "location": "westeurope"}, {"resource_id": "/subscriptions/sub/resourceGroups/other/providers/Microsoft.Compute/virtualMachines/vm2", "resource_name": "vm2", "resource_type": "Microsoft.Compute/virtualMachines", "resource_group": "other"}], "recommendations_all": [{"action": "resize_vm", "potential_savings": 58.4}]}
    assert classify_question_intent("list the ressources existing in RG_GhadaMaalej") == "resource_listing"
    response = _resource_listing_response(data, "list the ressources existing in RG_GhadaMaalej", "r")
    assert response["resource_group"] == "RG_GhadaMaalej"
    assert [item["name"] for item in response["resources"]] == ["vm1"]
    assert response["recommendations"] == []
    assert response["monthly_cost"] is None
