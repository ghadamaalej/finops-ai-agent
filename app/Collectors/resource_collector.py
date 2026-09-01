from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest

from app.services.azure_credential import get_azure_credential


class ResourceCollector:


    RESOURCE_CATEGORIES = {

        "microsoft.compute":
            "Virtual Machine",

        "microsoft.web":
            "Application Service",

        "microsoft.sql":
            "Database",

        "microsoft.storage":
            "Storage",

        "microsoft.cognitiveservices":
            "AI Service",

        "microsoft.machinelearning":
            "AI/ML",

        "microsoft.containerservice":
           "Kubernetes",

        "microsoft.kubernetes":
            "Kubernetes",

        "microsoft.network":
            "Networking",

        "microsoft.keyvault":
            "Security",

        "microsoft.operationalinsights":
            "Monitoring",

        "microsoft.insights":
            "Monitoring",

        "microsoft.documentdb":
            "NoSQL Database",

        "microsoft.cache":
            "Cache",

        "microsoft.search":
            "Search Service",

        "microsoft.app":
           "Container Apps",

"microsoft.automation":
    "Automation",

"microsoft.eventhub":
    "Messaging",

"microsoft.servicebus":
    "Messaging",

"microsoft.databricks":
    "Analytics",

"microsoft.synapse":
    "Analytics",

"microsoft.recoveryservices":
    "Backup",

"microsoft.security":
    "Security"

    }


    def __init__(self, credential=None):

        self.client = ResourceGraphClient(
            credential=credential or get_azure_credential()
        )



    def collect(
        self,
        subscription_id:str
    ):


        query = """
Resources
| project
    id,
    name,
    type,
    location,
    resourceGroup,
    subscriptionId,

    vm_size =
        tostring(
            properties.hardwareProfile.vmSize
        ),

    os_type = tostring(
    properties.storageProfile.osDisk.osType
        ),
    sku_name =
        tostring(
            sku.name
        ),

    sku_tier =
        tostring(
            sku.tier
        ),

    disk_size_gb =
        toint(
            properties.diskSizeGB
        ),

    disk_state =
        tostring(
            properties.diskState
        ),

    managed_by =
        tostring(
            managedBy
        ),

    kind,
    properties,
    tags,
    provisioning_state = tostring(properties.provisioningState),
    power_state = tostring(properties.extended.instanceView.powerState.code)
"""



        request = QueryRequest(

            subscriptions=[
                subscription_id
            ],

            query=query

        )



        response = self.client.resources(
            request
        )



        resources=[]



        for item in response.data:


            resource_type = (
                item["type"]
                .lower()
            )


            resources.append(
              {
        "id": item["id"],
        "name": item["name"],
        "type": item["type"],
        "category": self.classify_resource(
            resource_type
        ),

        "location": (
            item.get("location")
            or ""
        ).lower().strip(),

        "resource_group": (
            item.get("resourceGroup")
            or ""
        ),

        "subscription_id": (
            item.get("subscriptionId")
            or subscription_id
        ),

        "sku": (
            item.get("vm_size")
            or item.get("sku_name")
            or ""
        ),

        "vm_size": (
            item.get("vm_size")
            or ""
        ),

        "os_type": (
            item.get("os_type")
            or ""
        ),

        "sku_name": (
            item.get("sku_name")
            or ""
        ),

        "sku_tier": (
            item.get("sku_tier")
            or ""
        ),

        "disk_size_gb": (
            item.get("disk_size_gb")
            or 0
        ),

        "disk_state": (
            item.get("disk_state")
            or ""
        ),

        "managed_by": (
            item.get("managed_by")
            or ""
        ),

        "kind": (
            item.get("kind")
            or ""
        ),

        "power_state": item.get("power_state") or None,
        "provisioning_state": item.get("provisioning_state") or None,

        # Resource Graph properties are configuration evidence, not inferred
        # utilization. Keep them resource-ID-linked for type-specific analysis.
        "configuration": {
            "sku": item.get("vm_size") or item.get("sku_name") or None,
            "sku_tier": item.get("sku_tier") or None,
            "disk_size_gb": item.get("disk_size_gb") or None,
            "disk_state": item.get("disk_state") or None,
            "managed_by": item.get("managed_by") or None,
            "kind": item.get("kind") or None,
            "os_type": item.get("os_type") or None,
            "properties": item.get("properties") or {},
        },

        "tags": (
            item.get("tags")
            or {}
        ),
    }
)



        print(
            f"Discovered {len(resources)} Azure resources"
        )


        return resources

    def classify_resource(
        self,
        resource_type:str
    ):


        for key,category in self.RESOURCE_CATEGORIES.items():


            if key in resource_type:


                return category



        return "Other"
