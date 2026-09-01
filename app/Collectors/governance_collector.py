from azure.mgmt.policyinsights import PolicyInsightsClient

from app.services.azure_credential import get_azure_credential


class GovernanceCollector:


    def __init__(self, credential=None):

        self.credential = credential or get_azure_credential()
        self.client = PolicyInsightsClient(
            credential=self.credential,
            subscription_id=""
        )


    def collect(self, subscription_id:str):

        client = PolicyInsightsClient(
            credential=self.credential,
            subscription_id=subscription_id
        )


        violations=[]
        affected_resources=[]

        results = (
            client.policy_states
            .list_query_results_for_subscription(
                "latest",
                subscription_id
            )
        )


        total=0
        compliant=0


        for item in results:

            total += 1

            if item.compliance_state == "Compliant":

                compliant += 1

            else:

                violations.append(
                    item.policy_definition_name
                )
                resource_id = getattr(item, "resource_id", None)
                if resource_id:
                    affected_resources.append(resource_id)


        score = 0

        if total:

            score = (
                compliant / total
            ) * 100


        return {

            "compliance_score": score,
            "policy_violations": violations,
            "affected_resources": affected_resources,

        }