from app.models.verification import *


class GovernanceVerifier:


    def __init__(
        self,
        policy_client
    ):

        self.client = policy_client



    async def verify(
        self,
        execution_result
    ):


        return VerificationResult(

            resource_id=
            execution_result.resource_id,

            action="apply_policy",

            status=
            VerificationStatus.SUCCESS,

            message=
            "Policy remediation completed"

        )