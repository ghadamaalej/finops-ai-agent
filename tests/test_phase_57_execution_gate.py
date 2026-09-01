"""Phase 5.7: LangGraph integration tests with no Azure mutation."""

import pytest

from app.agent.execution_gate_graph import create_execution_gate_graph
from app.models.execution import ActionType, ExecutionResult, ExecutionStatus
from app.models.recommendation import Recommendation
from app.models.verification import VerificationResult, VerificationStatus


RESOURCE_ID = "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/finops-test-vm"


def issue():
    return {
        "id": "rightsizing-1",
        "resource_id": RESOURCE_ID,
        "resource_name": "finops-test-vm",
        "current_monthly_cost": 88.33,
        "estimated_monthly_savings": 61.83,
        "currency": "USD",
        "cost_source": "Azure Retail Prices",
        "cost_type": "estimated",
        "is_estimated": True,
        "evidence": {"cpu_average": 0.151, "cpu_max": 24.24},
    }


def recommendation():
    return Recommendation(
        title="Rightsize VM",
        source_issue_id="rightsizing-1",
        resource_id=RESOURCE_ID,
        resource_name="finops-test-vm",
        action="resize_vm",
        action_type="resize_vm",
        current_state={"sku": "Standard_D2s_v6", "region": "westeurope", "power_state": "running"},
        recommended_state={"sku": "Standard_B2s_v2"},
        current_cost=88.33,
        potential_savings=61.83,
        estimated_savings=61.83,
        projected_cost=26.5,
        observed_cpu_average_percent=0.151,
        observed_cpu_max_percent=24.24,
        confidence=0.6,
        requires_approval=True,
    )


class MockAzureExecutionRouter:
    def __init__(self, rollback_fails=False):
        self.rollback_fails = rollback_fails
        self.mutations = 0
        self.snapshots = []

    async def execute(self, request):
        if request.dry_run:
            return ExecutionResult(
                action=request.action, resource_id=request.resource_id,
                status=ExecutionStatus.DRY_RUN, message="Dry run; no Azure mutation.",
                dry_run=True, new_state=request.expected_state,
                previous_state=request.before_state,
                baseline_monthly_cost=request.baseline_monthly_cost,
                expected_savings=request.estimated_savings,
            )
        self.mutations += 1
        snapshot = {**request.before_state, "sku": "Standard_D2s_v6"}
        self.snapshots.append(snapshot)
        return ExecutionResult(
            action=request.action, resource_id=request.resource_id,
            status=ExecutionStatus.SUCCESS, message="Mock resize completed", dry_run=False,
            previous_state=snapshot, new_state=request.expected_state,
            rollback_available=True,
            rollback={"available": True, "strategy": "restore_previous_vm_sku", "previous_sku": "Standard_D2s_v6", "rollback_required": False, "rollback_status": "not_required", "manual_intervention_required": False},
            baseline_monthly_cost=request.baseline_monthly_cost,
            expected_savings=request.estimated_savings,
        )

    async def rollback(self, execution):
        if self.rollback_fails:
            return ExecutionResult(action=execution.action, resource_id=execution.resource_id, status=ExecutionStatus.FAILED, message="Mock rollback failed", dry_run=False)
        self.mutations += 1
        return ExecutionResult(action=execution.action, resource_id=execution.resource_id, status=ExecutionStatus.SUCCESS, message="Mock rollback completed", dry_run=False, new_state={"sku": "Standard_D2s_v6"})


class MockVerificationRouter:
    def __init__(self, fail_initial=False):
        self.fail_initial = fail_initial

    async def verify(self, execution):
        sku = execution.new_state.get("sku")
        passed = sku == "Standard_D2s_v6" or not self.fail_initial
        return VerificationResult(
            execution_id=execution.execution_id, resource_id=execution.resource_id,
            action="resize_vm", status=VerificationStatus.PASSED if passed else VerificationStatus.FAILED,
            expected_state={"sku": sku}, actual_state={"sku": sku if passed else "Standard_D2s_v6"},
            checks={"sku_changed": passed}, rollback_required=not passed,
            evidence={}, message="Mock verification",
        )


def graph():
    def observe(state): return {**state, "observed": {"source": "mocked_azure"}}
    def analyze(state): return {**state, "issues": [issue()]}
    def recommend(state): return {**state, "recommendations": [recommendation()]}
    return create_execution_gate_graph(observe, analyze, recommend)


async def run_gate(*, dry_run, verifier, executor):
    return await graph().ainvoke({
        "dry_run": dry_run,
        "approved_recommendation_ids": ["rightsizing-1"],
        "recommendation_intelligence": {"recommendation_confidence": 0.6},
        "execution_router": executor,
        "verification_router": verifier,
    })


@pytest.mark.asyncio
async def test_graph_full_dry_run_has_no_mutation_or_realized_savings():
    executor = MockAzureExecutionRouter()
    result = await run_gate(dry_run=True, verifier=MockVerificationRouter(), executor=executor)
    execution = result["execution_results"][0]
    check = result["verification_report"]["results"][0]
    assert execution.status == ExecutionStatus.DRY_RUN
    assert executor.mutations == 0
    assert check["verification_status"] == "SKIPPED"
    assert check["realized_savings"] is None


@pytest.mark.asyncio
async def test_graph_successful_resize_snapshots_and_verifies():
    executor = MockAzureExecutionRouter()
    result = await run_gate(dry_run=False, verifier=MockVerificationRouter(), executor=executor)
    check = result["verification_report"]["results"][0]
    assert executor.snapshots[0]["sku"] == "Standard_D2s_v6"
    assert executor.mutations == 1
    assert check["status"] == "verified"
    assert check["expected_state"] == check["actual_state"]
    assert check["rollback_status"] == "not_required"


@pytest.mark.asyncio
async def test_graph_failed_verification_rolls_back_and_verifies_recovery():
    executor = MockAzureExecutionRouter()
    result = await run_gate(dry_run=False, verifier=MockVerificationRouter(fail_initial=True), executor=executor)
    check = result["verification_report"]["results"][0]
    assert executor.mutations == 2
    assert check["rollback_status"] == "success"
    assert check["final_state"] == "BEFORE_STATE"
    assert check["execution_status"] == ExecutionStatus.FAILED_VERIFICATION


@pytest.mark.asyncio
async def test_graph_failed_rollback_requires_manual_intervention():
    executor = MockAzureExecutionRouter(rollback_fails=True)
    result = await run_gate(dry_run=False, verifier=MockVerificationRouter(fail_initial=True), executor=executor)
    check = result["verification_report"]["results"][0]
    assert check["rollback_status"] == "failed"
    assert check["manual_intervention_required"] is True
    assert check["execution_status"] == ExecutionStatus.ROLLBACK_FAILED
