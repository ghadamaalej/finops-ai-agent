class VerificationRouter:

    def __init__(
        self,
        vm,
        disk,
        network,
        governance,
    ):
        self.map = {

            "stop_vm":
                vm,

            "resize_vm":
                vm,

            "enable_autoshutdown":
                vm,

            "delete_disk":
                disk,

            "remove_public_ip":
                network,

            "apply_policy":
                governance,
        }

    async def verify(
        self,
        execution_result,
    ):

        action = execution_result.action

        verifier = self.map.get(action)

        if verifier is None:
            return {
                "status": "UNSUPPORTED",
                "action": action,
                "message": (
                    f"No verifier registered "
                    f"for action '{action}'."
                ),
            }

        return await verifier.verify(
            execution_result
        )