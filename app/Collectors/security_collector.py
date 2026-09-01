# app/Collectors/security_collector.py
from azure.mgmt.security import SecurityCenter
from azure.identity import AzureCliCredential


class SecurityCollector:
    def __init__(self, subscription_id, credential=None):
        credential = credential or AzureCliCredential()
        self.client = SecurityCenter(
            credential,
            subscription_id
        )
        self.subscription_id = subscription_id

    def collect(self):
        findings = []
        scope = f"/subscriptions/{self.subscription_id}"

        try:
            assessments = self.client.assessments.list(scope)

            for assessment in assessments:
                resource_id = "unknown"

                if assessment.resource_details:
                    if hasattr(assessment.resource_details, "id"):
                        resource_id = assessment.resource_details.id
                    elif hasattr(assessment.resource_details, "resource_id"):
                        resource_id = assessment.resource_details.resource_id

                severity = "Unknown"
                if assessment.status:
                    severity = getattr(assessment.status, "severity", "Unknown")

                description = ""
                if assessment.metadata:
                    description = getattr(assessment.metadata, "description", "")

                findings.append({
                    "resource_id": resource_id,
                    "severity": severity,
                    "recommendation": assessment.display_name,
                    "description": description,
                    "category": "Security"
                })

        except Exception as e:
            print(f"Security recommendations error: {e}")

        print(f"Security findings collected: {len(findings)}")
        return findings