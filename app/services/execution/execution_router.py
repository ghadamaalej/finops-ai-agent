from httpx import request

from app.models.execution import ActionType, ExecutionResult, ExecutionStatus



class ExecutionRouter:


    def __init__(
        self,
        vm_executor,
        disk_executor,
        network_executor,
        storage_executor,
        governance_executor
    ):


        self.executors = {


            ActionType.STOP_VM:
                vm_executor,


            ActionType.RESIZE_VM:
                vm_executor,


            ActionType.DELETE_DISK:
                disk_executor,


            ActionType.REMOVE_PUBLIC_IP:
                network_executor,


            ActionType.ENABLE_AUTOSHUTDOWN:
                vm_executor,


            ActionType.APPLY_POLICY:
                governance_executor

        }

    async def execute(self, request):

        executor = self.executors.get(request.action)

        if executor is None:
            return ExecutionResult(
                action=request.action,
                resource_id=request.resource_id,
                status=ExecutionStatus.FAILED,
                message=f"No executor registered for {request.action}",
                dry_run=request.dry_run,
            )

        return await executor.execute(request)

    async def rollback(self, execution_result):
        executor = self.executors.get(execution_result.action)
        if executor is None or not hasattr(executor, "rollback"):
            raise ValueError(f"No rollback executor registered for {execution_result.action}")
        return await executor.rollback(execution_result)
