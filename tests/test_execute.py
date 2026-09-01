import pytest

from app.agent.nodes.execution import execute
from app.models.execution import (
    ExecutionResult,
    ExecutionStatus
)


class FakeRouter:

    async def execute(self, request):

        return ExecutionResult(
            action=request.action,
            resource_id=request.resource_id,
            status=ExecutionStatus.SUCCESS,
            message="Executed successfully",
            dry_run=True
        )


@pytest.mark.asyncio
async def test_execute():

    router = FakeRouter()

    recommendation = type(
        "Recommendation",
        (),
        {
            "action": "stop_vm",
            "resource_id": "/subscriptions/test/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm1",
            "dry_run": True
        }
    )()

    state = {
        "execution_router": router,
        "approved_recommendations": [
            recommendation
        ]
    }

    result = await execute(state)

    assert len(result["execution_results"]) == 1

    assert (
        result["execution_results"][0].status
        == ExecutionStatus.SUCCESS
    )