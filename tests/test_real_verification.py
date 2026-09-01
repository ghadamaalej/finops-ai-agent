import pytest

from app.models.execution import (
    ActionType,
    ExecutionResult,
    ExecutionStatus,
)
from app.services.verification.verification_router import VerificationRouter
from app.services.verification.azure_verifier import AzureVerifier
from app.services.verification.vm_verifier import VMVerifier
from app.services.verification.disk_verifier import DiskVerifier
from app.services.verification.network_verifier import NetworkVerifier
from app.services.verification.governance_verifier import GovernanceVerifier


SUBSCRIPTION_ID = "6850d94e-3234-463d-aa51-615d3c486939"

RESOURCE_ID = (
    f"/subscriptions/{SUBSCRIPTION_ID}"
    "/resourceGroups/RG_GhadaMaalej"
    "/providers/Microsoft.Compute/virtualMachines/finops-test-vm"
)


def create_real_verification_router():
    """Create the real read-only VerificationRouter."""

    azure = AzureVerifier(SUBSCRIPTION_ID)

    vm_verifier = VMVerifier(azure.compute_client)
    disk_verifier = DiskVerifier(azure.compute_client)
    network_verifier = NetworkVerifier(azure.network_client)
    governance_verifier = GovernanceVerifier(azure.policy_client)

    return VerificationRouter(
        vm_verifier,
        disk_verifier,
        network_verifier,
        governance_verifier,
    )


@pytest.mark.asyncio
async def test_real_verification_router_vm():
    """
    Read-only integration test.

    Existing Azure VM
        -> AzureVerifier
        -> VMVerifier
        -> VerificationRouter
        -> VerificationResult

    No VMExecutor is called.
    No Azure resource is modified.
    """

    print("\n" + "=" * 60)
    print("REAL VERIFICATION TEST")
    print("=" * 60)

    print("\nResource : finops-test-vm")
    print("Action   : stop_vm")

    # ---------------------------------------------------------------
    # 1. Create real verification router
    # ---------------------------------------------------------------

    router = create_real_verification_router()

    print("\n[1] Azure resource lookup")

    # Synthetic result only.
    # This does NOT execute stop_vm.
    execution_result = ExecutionResult(
        action=ActionType.STOP_VM,
        resource_id=RESOURCE_ID,
        status=ExecutionStatus.SUCCESS,
        message="Synthetic result for read-only verification test",
        dry_run=False,
    )

    print("PASS: VerificationRouter created")

    # ---------------------------------------------------------------
    # 2. Run real verifier
    # ---------------------------------------------------------------

    print("\n[2] VM state inspection")

    verification_result = await router.verify(
        execution_result
    )

    assert verification_result is not None, (
        "VerificationRouter returned None for stop_vm"
    )

    print("PASS: VM verifier returned a result")

    # ---------------------------------------------------------------
    # 3. Validate verification result
    # ---------------------------------------------------------------

    print("\n[3] Verification result")

    print(
        f"Status   : {verification_result.status}"
    )
    print(
        f"Message  : {verification_result.message}"
    )
    print(
        f"Resource : {verification_result.resource_id}"
    )

    assert verification_result.resource_id == RESOURCE_ID
    assert verification_result.action == "stop_vm"
    assert verification_result.status is not None

    print("\n" + "=" * 60)
    print("REAL VERIFICATION TEST PASSED")
    print("=" * 60)
