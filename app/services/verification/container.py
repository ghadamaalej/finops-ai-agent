from app.services.verification.azure_verifier import AzureVerifier
from app.services.verification.vm_verifier import VMVerifier
from app.services.verification.disk_verifier import DiskVerifier
from app.services.verification.network_verifier import NetworkVerifier
from app.services.verification.governance_verifier import GovernanceVerifier
from app.services.verification.verification_router import VerificationRouter

def create_verification_router(subscription_id: str):
    azure = AzureVerifier(subscription_id)

    vm_verifier = VMVerifier(
        azure.compute_client
    )

    disk_verifier = DiskVerifier(
        azure.compute_client
    )

    network_verifier = NetworkVerifier(
        azure.network_client
    )

    governance_verifier = GovernanceVerifier(
        azure.policy_client
    )

    return VerificationRouter(
        vm_verifier,
        disk_verifier,
        network_verifier,
        governance_verifier
    )