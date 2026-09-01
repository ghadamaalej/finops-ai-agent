from app.services.execution.base_executor import BaseExecutor



class GovernanceExecutor(BaseExecutor):


    def __init__(
        self,
        policy_client,
        dry_run=True
    ):

        super().__init__(dry_run)

        self.client = policy_client



    async def execute(
        self,
        request
    ):


        if request.dry_run:

            return self.dry_run_result(request)


        return {

            "message":
            "Policy remediation executed"

        }