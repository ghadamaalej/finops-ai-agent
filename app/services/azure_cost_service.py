from azure.mgmt.costmanagement import CostManagementClient
from azure.identity import DefaultAzureCredential

from app.models.azure import ResourceCost


class AzureCostService:

    def __init__(self):

        credential = DefaultAzureCredential()

        self.client = CostManagementClient(
            credential
        )


    def get_resource_costs(
        self,
        subscription_id: str
    ) -> list[ResourceCost]:

        scope = (
            f"/subscriptions/{subscription_id}"
        )


        query = {
            "type": "Usage",
            "timeframe": "MonthToDate",
            "dataset": {

                "granularity": "Monthly",

                "aggregation": {

                    "totalCost": {
                        "name": "Cost",
                        "function": "Sum"
                    }
                },

                "grouping": [

                    {
                        "type": "Dimension",
                        "name": "ResourceId"
                    }

                ]

            }
        }


        result = self.client.query.usage(
            scope,
            query
        )


        costs=[]


        for row in result.rows:

            resource_id = row[1]
            cost = row[0]


            costs.append(
                ResourceCost(

                    resource_id=resource_id,

                    resource_name=
                    resource_id.split("/")[-1],

                    service_name="Azure",

                    monthly_cost=float(cost),

                    currency="USD",

                    cost_last_30_days=float(cost)

                )
            )


        return costs