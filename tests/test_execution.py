import pytest

from app.models.execution import ActionType, ExecutionRequest
from app.services.execution.base_executor import BaseExecutor
from app.services.execution.execution_router import ExecutionRouter


class DryRunVMExecutor(BaseExecutor):
    async def execute(self, request):
        await self.validate(request)
        return self.dry_run_result(request)


@pytest.mark.asyncio
async def test_vm_execution_dry_run():
    executor = DryRunVMExecutor()
    router = ExecutionRouter(
        vm_executor=executor,
        disk_executor=executor,
        network_executor=executor,
        storage_executor=executor,
        governance_executor=executor,
    )
    request = ExecutionRequest(
        action=ActionType.STOP_VM,
        resource_id="/subscriptions/test/resourceGroups/demo/providers/Microsoft.Compute/virtualMachines/test",
        dry_run=True,
        baseline_monthly_cost=88.33,
        estimated_savings=61.83,
    )

    result = await router.execute(request)

    assert result.status == "dry_run"
    assert result.dry_run is True
    assert result.baseline_monthly_cost == 88.33
    assert result.expected_savings == 61.83
