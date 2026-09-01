from app.models.verification import VerificationResult, VerificationStatus


class VMVerifier:
    """Read-only VM post-execution verification."""

    def __init__(self, compute_client):
        self.client = compute_client

    async def verify(self, execution_result):
        action = getattr(execution_result.action, "value", execution_result.action)
        if action == "stop_vm":
            return await self.verify_stop(execution_result)
        if action == "resize_vm":
            return await self.verify_resize(execution_result)
        return VerificationResult(
            execution_id=getattr(execution_result, "execution_id", None),
            resource_id=execution_result.resource_id,
            action=str(action),
            status=VerificationStatus.UNSUPPORTED,
            message=f"VM verification is not implemented for '{action}'.",
        )

    async def verify_stop(self, execution_result):
        rg, vm = self._parse(execution_result.resource_id)
        instance = self.client.virtual_machines.instance_view(rg, vm)
        states = [status.display_status for status in instance.statuses]
        deallocated = any("deallocated" in state.lower() for state in states)
        return VerificationResult(
            execution_id=execution_result.execution_id,
            resource_id=execution_result.resource_id,
            action="stop_vm",
            status=VerificationStatus.PASSED if deallocated else VerificationStatus.FAILED,
            expected_state={"power_state": "deallocated"},
            actual_state={"statuses": states},
            checks={
                "resource_available": True,
                "expected_state_reached": deallocated,
                "performance_healthy": None,
                "cost_improvement": None,
            },
            message="VM deallocated" if deallocated else "VM is not deallocated",
            rollback_required=not deallocated,
        )

    async def verify_resize(self, execution_result):
        rg, vm = self._parse(execution_result.resource_id)
        current = self.client.virtual_machines.get(rg, vm)
        actual_sku = current.hardware_profile.vm_size
        expected = getattr(execution_result, "new_state", {}) or {}
        expected_sku = expected.get("sku")
        sku_changed = bool(expected_sku) and actual_sku == expected_sku
        return VerificationResult(
            execution_id=execution_result.execution_id,
            resource_id=execution_result.resource_id,
            action="resize_vm",
            status=VerificationStatus.PASSED if sku_changed else VerificationStatus.FAILED,
            expected_state={"sku": expected_sku},
            actual_state={"sku": actual_sku},
            checks={
                "resource_available": True,
                "sku_changed": sku_changed,
                # Metrics and price collection are separate read-only jobs.
                "performance_healthy": None,
                "cost_improvement": None,
            },
            evidence={
                "before_monthly_cost": getattr(execution_result, "baseline_monthly_cost", None),
                "potential_monthly_savings": getattr(execution_result, "expected_savings", 0),
            },
            message="VM SKU matches the expected target" if sku_changed else "VM SKU does not match the expected target",
            rollback_required=not sku_changed,
        )

    @staticmethod
    def _parse(resource_id):
        parts = resource_id.split("/")
        try:
            return (
                parts[parts.index("resourceGroups") + 1],
                parts[parts.index("virtualMachines") + 1],
            )
        except (ValueError, IndexError) as exc:
            raise ValueError(f"Invalid VM resource ID: {resource_id}") from exc
