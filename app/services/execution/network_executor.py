from app.services.execution.base_executor import BaseExecutor

from app.models.execution import (
    ExecutionResult,
    ExecutionStatus
)



class NetworkExecutor(BaseExecutor):


    def __init__(
        self,
        network_client,
        dry_run=True
    ):

        super().__init__(dry_run)

        self.client = network_client



    async def execute(
        self,
        request
    ):


        if self.dry_run or request.dry_run:

            return self.dry_run_result(request)



        try:


            parts=request.resource_id.split("/")


            rg=parts[
                parts.index("resourceGroups")+1
            ]


            ip_name=parts[
                parts.index("publicIPAddresses")+1
            ]



            self.client.public_ip_addresses.begin_delete(
                rg,
                ip_name
            ).result()



            return ExecutionResult(

                action=request.action,

                resource_id=request.resource_id,

                status=ExecutionStatus.SUCCESS,

                message="Public IP removed",

                dry_run=False

            )


        except Exception as e:


            return ExecutionResult(

                action=request.action,

                resource_id=request.resource_id,

                status=ExecutionStatus.FAILED,

                message="Network action failed",

                error=str(e)

            )