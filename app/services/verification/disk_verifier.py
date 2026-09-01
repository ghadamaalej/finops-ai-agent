from app.models.verification import *


class DiskVerifier:


    def __init__(
        self,
        compute_client
    ):

        self.client = compute_client



    async def verify(
        self,
        execution_result
    ):


        parts = execution_result.resource_id.split("/")


        rg = parts[
            parts.index(
                "resourceGroups"
            )+1
        ]


        disk = parts[
            parts.index(
                "disks"
            )+1
        ]



        try:


            self.client.disks.get(
                rg,
                disk
            )


            exists=True


        except:

            exists=False



        return VerificationResult(

            resource_id=
            execution_result.resource_id,

            action="delete_disk",

            status=
            VerificationStatus.FAILED
            if exists
            else
            VerificationStatus.SUCCESS,


            message=
            "Disk deleted"
            if not exists
            else
            "Disk still exists"

        )