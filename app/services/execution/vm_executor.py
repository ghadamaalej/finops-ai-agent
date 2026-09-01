from app.services.execution.base_executor import BaseExecutor

from app.models.execution import (
    ActionType,
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus
)



class VMExecutor(BaseExecutor):


    def __init__(
        self,
        azure_client,
        dry_run=True
    ):

        super().__init__(dry_run)

        self.client = azure_client



    async def execute(
        self,
        request: ExecutionRequest
    ):


        await self.validate(request)



        if self.dry_run or request.dry_run:

            return self.dry_run_result(request)



        try:


            vm_id = request.resource_id.split("/")


            resource_group = (
                vm_id[
                    vm_id.index("resourceGroups")+1
                ]
            )


            vm_name = (
                vm_id[
                    vm_id.index("virtualMachines")+1
                ]
            )


            if request.action == ActionType.STOP_VM:


                poller = (
                    self.client
                    .virtual_machines
                    .begin_deallocate(
                        resource_group,
                        vm_name
                    )
                )


                poller.result()



            elif request.action == ActionType.RESIZE_VM:

                new_size = request.parameters.get("target_sku")

                if not new_size:
                    raise ValueError(
                        "A target_sku is required for a real VM resize"
                    )


                vm = (
                    self.client
                    .virtual_machines
                    .get(
                        resource_group,
                        vm_name
                    )
                )

                previous_sku = vm.hardware_profile.vm_size

                # The Azure GET above is the authoritative snapshot used for
                # rollback; recommendation evidence is retained alongside it.
                before_state = {
                    **request.before_state,
                    "resource_id": request.resource_id,
                    "current_sku": previous_sku,
                }


                vm.hardware_profile.vm_size = (
                    new_size
                )


                poller = (
                    self.client
                    .virtual_machines
                    .begin_create_or_update(
                        resource_group,
                        vm_name,
                        vm
                    )
                )


                poller.result()



            return ExecutionResult(

                action=request.action,

                resource_id=request.resource_id,

                status=ExecutionStatus.SUCCESS,

                message=
                "VM operation completed",

                dry_run=False,

                previous_state={
                    "sku": previous_sku,
                    **before_state,
                } if request.action == ActionType.RESIZE_VM else {},

                new_state=request.expected_state or (
                    {"sku": new_size}
                    if request.action == ActionType.RESIZE_VM
                    else {}
                ),

                baseline_monthly_cost=request.baseline_monthly_cost,

                expected_savings=request.estimated_savings,

                rollback_available=request.action == ActionType.RESIZE_VM,
                rollback={
                    "available": request.action == ActionType.RESIZE_VM,
                    "strategy": "restore_previous_vm_sku" if request.action == ActionType.RESIZE_VM else None,
                    "previous_sku": previous_sku if request.action == ActionType.RESIZE_VM else None,
                    "rollback_required": False,
                    "rollback_status": "not_required",
                    "manual_intervention_required": False,
                },

            )


        except Exception as e:


            return ExecutionResult(

                action=request.action,

                resource_id=request.resource_id,

                status=ExecutionStatus.FAILED,

                message="VM operation failed",

                error=str(e),

                dry_run=False,

                baseline_monthly_cost=request.baseline_monthly_cost,

                expected_savings=request.estimated_savings,

            )

    async def rollback(self, execution_result: ExecutionResult) -> ExecutionResult:
        """Restore a successfully resized VM to its Azure-observed SKU."""
        if execution_result.action != ActionType.RESIZE_VM:
            raise ValueError("Rollback is only supported for VM resize operations")
        previous_sku = (execution_result.previous_state or {}).get("sku")
        if not previous_sku:
            raise ValueError("Rollback requires a captured previous VM SKU")
        try:
            resource_group, vm_name = self._parse_resource_id(execution_result.resource_id)
            vm = self.client.virtual_machines.get(resource_group, vm_name)
            vm.hardware_profile.vm_size = previous_sku
            self.client.virtual_machines.begin_create_or_update(resource_group, vm_name, vm).result()
            return ExecutionResult(
                action=ActionType.RESIZE_VM,
                resource_id=execution_result.resource_id,
                status=ExecutionStatus.SUCCESS,
                message="VM rollback completed",
                dry_run=False,
                previous_state=execution_result.new_state,
                new_state={"sku": previous_sku},
                rollback_available=True,
            )
        except Exception as exc:
            return ExecutionResult(
                action=ActionType.RESIZE_VM,
                resource_id=execution_result.resource_id,
                status=ExecutionStatus.FAILED,
                message="VM rollback failed",
                dry_run=False,
                error=str(exc),
                previous_state=execution_result.previous_state,
                new_state=execution_result.new_state,
                rollback_available=True,
            )

    @staticmethod
    def _parse_resource_id(resource_id):
        parts = resource_id.split("/")
        return parts[parts.index("resourceGroups") + 1], parts[parts.index("virtualMachines") + 1]
