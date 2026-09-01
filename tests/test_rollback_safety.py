import pytest

from app.agent.nodes.verification import verify
from app.models.execution import ActionType, ExecutionResult, ExecutionStatus
from app.models.verification import VerificationResult, VerificationStatus
from app.services.execution.recommendation_to_request import recommendation_to_execution_request


RESOURCE_ID = "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm"


class FailedThenRestoredVerifier:
    async def verify(self, execution):
        target = execution.new_state["sku"]
        restored = target == "Standard_D2s_v6"
        return VerificationResult(
            execution_id=execution.execution_id,
            resource_id=execution.resource_id,
            action="resize_vm",
            status=VerificationStatus.PASSED if restored else VerificationStatus.FAILED,
            expected_state={"sku": target},
            actual_state={"sku": target if restored else "Standard_D2s_v6"},
            checks={"sku_changed": restored},
            rollback_required=not restored,
        )


class SuccessfulRollbackRouter:
    async def rollback(self, execution):
        return ExecutionResult(
            action=ActionType.RESIZE_VM,
            resource_id=execution.resource_id,
            status=ExecutionStatus.SUCCESS,
            message="rollback completed",
            dry_run=False,
            new_state={"sku": "Standard_D2s_v6"},
        )


class FailedRollbackRouter:
    async def rollback(self, execution):
        return ExecutionResult(
            action=ActionType.RESIZE_VM,
            resource_id=execution.resource_id,
            status=ExecutionStatus.FAILED,
            message="rollback failed",
            dry_run=False,
        )


def resized_execution():
    return ExecutionResult(
        action=ActionType.RESIZE_VM,
        resource_id=RESOURCE_ID,
        status=ExecutionStatus.SUCCESS,
        message="resize completed",
        dry_run=False,
        previous_state={"sku": "Standard_D2s_v6"},
        new_state={"sku": "Standard_B2s_v2"},
        rollback_available=True,
        rollback={
            "available": True,
            "strategy": "restore_previous_vm_sku",
            "previous_sku": "Standard_D2s_v6",
            "rollback_required": False,
            "rollback_status": "not_required",
            "manual_intervention_required": False,
        },
    )


def test_recommendation_captures_collector_before_state():
    request = recommendation_to_execution_request({
        "action_type": "resize_vm",
        "resource_id": RESOURCE_ID,
        "resource_name": "vm",
        "current_state": {"sku": "Standard_D2s_v6", "region": "westeurope", "power_state": "running"},
        "recommended_state": {"sku": "Standard_B2s_v2"},
        "current_cost": 88.33,
        "potential_savings": 61.83,
        "observed_cpu_average_percent": 0.151,
        "observed_cpu_max_percent": 24.24,
    })
    assert request.before_state["current_sku"] == "Standard_D2s_v6"
    assert request.before_state["monthly_cost"] == 88.33
    assert request.before_state["potential_savings"] == 61.83


@pytest.mark.asyncio
async def test_failed_verification_rolls_back_and_verifies_before_state():
    execution = resized_execution()
    result = await verify({
        "execution_results": [execution],
        "verification_router": FailedThenRestoredVerifier(),
        "execution_router": SuccessfulRollbackRouter(),
    })
    check = result["verification_report"]["results"][0]
    assert check["rollback_status"] == "success"
    assert check["final_state"] == "BEFORE_STATE"
    assert check["manual_intervention_required"] is False
    assert execution.status == ExecutionStatus.FAILED_VERIFICATION


@pytest.mark.asyncio
async def test_failed_rollback_requires_manual_intervention():
    execution = resized_execution()
    result = await verify({
        "execution_results": [execution],
        "verification_router": FailedThenRestoredVerifier(),
        "execution_router": FailedRollbackRouter(),
    })
    check = result["verification_report"]["results"][0]
    assert check["rollback_status"] == "failed"
    assert check["manual_intervention_required"] is True
    assert execution.status == ExecutionStatus.ROLLBACK_FAILED
