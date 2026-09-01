from app.models.verification import *


class NetworkVerifier:


    def __init__(
        self,
        network_client
    ):

        self.client = network_client



    async def verify(
        self,
        execution_result
    ):


        parts = (
            execution_result.resource_id
            .split("/")
        )


        rg = parts[
            parts.index(
                "resourceGroups"
            )+1
        ]


        ip = parts[
            parts.index(
                "publicIPAddresses"
            )+1
        ]


        try:

            self.client.public_ip_addresses.get(
                rg,
                ip
            )


            exists=True


        except:

            exists=False



        return VerificationResult(

            resource_id=
            execution_result.resource_id,

            action="remove_public_ip",

            status=
            VerificationStatus.SUCCESS
            if not exists
            else
            VerificationStatus.FAILED,

            message=
            "Public IP removed"

        )