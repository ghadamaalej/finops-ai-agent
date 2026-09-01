from azure.identity import DefaultAzureCredential
from azure.mgmt.resource.resources import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.policyinsights import PolicyInsightsClient
from azure.mgmt.monitor import MonitorManagementClient
from azure.mgmt.costmanagement import CostManagementClient
from azure.mgmt.storage import StorageManagementClient


class AzureExecutor:


    def __init__(
        self,
        subscription_id: str
    ):

        self.subscription_id = subscription_id


        credential = DefaultAzureCredential()


        self.compute_client = (
            ComputeManagementClient(
                credential,
                subscription_id
            )
        )


        self.network_client = (
            NetworkManagementClient(
                credential,
                subscription_id
            )
        )


        self.policy_client = PolicyInsightsClient(
            credential,
            subscription_id
        )

        self.resource_client = ResourceManagementClient(
            credential,
            subscription_id
        )

        self.monitor_client = MonitorManagementClient(
            credential,
            subscription_id
        )

        self.storage_client = StorageManagementClient(
            credential,
            subscription_id
        )

        self.cost_client = CostManagementClient(
            credential,
            subscription_id
        )