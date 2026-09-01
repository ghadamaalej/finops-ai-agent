import uuid
from app.models.issue import Issue

class SecurityAnalyzer:

    def analyze(self, context):


        issues=[]

        for finding in context.security_findings:

            if finding.severity.lower() in [

                "high",

                "critical"

            ]:

                risk = (

                    100

                    if finding.severity.lower()=="critical"

                    else 80

                )

                issues.append(

                    Issue(

                    id=str(uuid.uuid4()),


                    category="Security",


                    issue_type=
                    "SecurityVulnerability",


                    severity=
                    finding.severity,

                    confidence=0.95,

                    resource_id=
                    finding.resource_id,

                    resource_name=
                    finding.resource_id,

                    resource_type=
                    "AzureResource",

                    description=
                    finding.description,

                    evidence={

                        "recommendation":
                        finding.recommendation,

                        "category":
                        finding.category

                    },

                    business_impact=
                    "Security exposure detected",

                    risk_score=risk,

                    detected_by=
                    "security_analyzer"

                    )

                )


        return issues