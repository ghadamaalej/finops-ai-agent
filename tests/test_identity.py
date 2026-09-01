from app.services.azure_credential import get_azure_credential
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest


credential = get_azure_credential()

client = ResourceGraphClient(
    credential
)


request = QueryRequest(
    subscriptions=[
        "6850d94e-3234-463d-aa51-615d3c486939"
    ],
    query="""
    Resources
    | project name, type, resourceGroup
    | limit 5
    """
)


response = client.resources(request)


print("Resources found:", len(response.data))

for resource in response.data:
    print(resource)