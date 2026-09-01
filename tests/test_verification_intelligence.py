import pytest

from app.agent.nodes.verification import verify
from app.models.execution import ActionType, ExecutionResult, ExecutionStatus
from app.models.verification import VerificationResult, VerificationStatus


class PassingRouter:
    async def verify(self, execution):
        return VerificationResult(
            execution_id=execution.execution_id,
            resource_id=execution.resource_id,
            action="resize_vm",
            status=VerificationStatus.PASSED,
            expected_state={"sku": "Standard_B2s_v2"},
            actual_state={"sku": "Standard_B2s_v2"},
            checks={
                "sku_changed": True,
                "resource_available": True,
                "performance_healthy": True,
                "cost_improvement": True,
            },
            evidence={"after_monthly_cost": 31.54},
            message="VM SKU matches the expected target",
        )


@pytest.mark.asyncio
async def test_dry_run_verification_is_skipped_without_router_call():
    execution = ExecutionResult(
        action=ActionType.RESIZE_VM,
        resource_id="/subscriptions/test/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm",
        status=ExecutionStatus.SUCCESS,
        message="Dry run completed.",
        dry_run=True,
        baseline_monthly_cost=88.33,
        expected_savings=61.83,
        new_state={"sku": "Standard_B2s_v2"},
    )
    result = await verify({
        "execution_results": [execution],
        "verification_router": None,
    })

    report = result["verification_report"]
    assert report["overall_status"] == "SKIPPED"
    check = report["results"][0]
    assert check["verification_status"] == "SKIPPED"
    assert check["realized_savings"] is None
    assert check["checks"]["execution_mutated"] is False


@pytest.mark.asyncio
async def test_verification_compares_state_and_measures_realized_savings():
    execution = ExecutionResult(
        action=ActionType.RESIZE_VM,
        resource_id="/subscriptions/test/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm",
        status=ExecutionStatus.SUCCESS,
        message="VM operation completed",
        dry_run=False,
        baseline_monthly_cost=88.33,
        expected_savings=61.83,
        new_state={"sku": "Standard_B2s_v2"},
    )
    result = await verify({
        "execution_results": [execution],
        "verification_router": PassingRouter(),
    })

    report = result["verification_report"]
    assert report["overall_status"] == "VERIFIED"
    assert report["realized_savings"] == 56.79
    check = report["results"][0]
    assert check["expected_state"] == check["actual_state"]
    assert check["checks"]["sku_changed"] is True
    assert check["verification_status"] == "MEASURED"


@pytest.mark.asyncio
async def test_failed_execution_is_not_sent_to_verifier():
    execution = ExecutionResult(
        action=ActionType.RESIZE_VM,
        resource_id="vm",
        status=ExecutionStatus.FAILED,
        message="VM operation failed",
        dry_run=False,
        expected_savings=10,
    )
    result = await verify({
        "execution_results": [execution],
        "verification_router": PassingRouter(),
    })

    check = result["verification_report"]["results"][0]
    assert check["verification_status"] == "SKIPPED_EXECUTION_FAILED"
    assert check["checks"]["execution_succeeded"] is False
