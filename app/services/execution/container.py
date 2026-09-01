import os

from app.services.execution.azure_executor import AzureExecutor

from app.services.execution.vm_executor import VMExecutor
from app.services.execution.disk_executor import DiskExecutor
from app.services.execution.network_executor import NetworkExecutor
from app.services.execution.storage_executor import StorageExecutor
from app.services.execution.governance_executor import GovernanceExecutor
import os
from app.services.execution.execution_router import ExecutionRouter

def create_execution_router():

    azure = AzureExecutor(
    subscription_id=os.getenv("AZURE_SUBSCRIPTION_ID")
    )

    vm_executor = VMExecutor(
    azure.compute_client,
     dry_run=True
    )


    disk_executor = DiskExecutor(
        azure.compute_client,
        dry_run=True
    )


    network_executor = NetworkExecutor(
        azure.network_client,
        dry_run=True
    )


    storage_executor = StorageExecutor(
        azure.storage_client,
        True
    )


    governance_executor = GovernanceExecutor(
        azure.policy_client,
        dry_run=True
    )


    return ExecutionRouter(

        vm_executor,

        disk_executor,

        network_executor,

        storage_executor,

        governance_executor

    )