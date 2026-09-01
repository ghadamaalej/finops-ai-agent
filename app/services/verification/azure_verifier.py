from azure.identity import DefaultAzureCredential
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.policyinsights import PolicyInsightsClient
from azure.mgmt.storage import StorageManagementClient

class AzureVerifier:
    def __init__(
        self,
        subscription_id: str
    ):
        credential = DefaultAzureCredential()
        
        self.compute_client = ComputeManagementClient(
            credential,
            subscription_id
        )
        
        self.network_client = NetworkManagementClient(
            credential,
            subscription_id
        )
        
        self.policy_client = PolicyInsightsClient(
            credential,
            subscription_id
        )
        
        self.storage_client = StorageManagementClient(
            credential,
            subscription_id
        )