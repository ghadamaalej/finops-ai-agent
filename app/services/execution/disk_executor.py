from app.services.execution.base_executor import BaseExecutor

from app.models.execution import (
    ExecutionResult,
    ExecutionStatus
)



class DiskExecutor(BaseExecutor):


    def __init__(
        self,
        compute_client,
        dry_run=True
    ):

        super().__init__(dry_run)

        self.client = compute_client



    async def execute(
        self,
        request
    ):


        if self.dry_run or request.dry_run:

            return self.dry_run_result(request)



        try:


            parts = request.resource_id.split("/")


            resource_group = (
                parts[
                    parts.index(
                        "resourceGroups"
                    )+1
                ]
            )


            disk_name = (
                parts[
                    parts.index(
                        "disks"
                    )+1
                ]
            )



            poller = (
                self.client
                .disks
                .begin_delete(
                    resource_group,
                    disk_name
                )
            )


            poller.result()



            return ExecutionResult(

                action=request.action,

                resource_id=request.resource_id,

                status=ExecutionStatus.SUCCESS,

                message="Disk deleted",

                dry_run=False

            )


        except Exception as e:


            return ExecutionResult(

                action=request.action,

                resource_id=request.resource_id,

                status=ExecutionStatus.FAILED,

                message="Disk deletion failed",

                error=str(e)

            )