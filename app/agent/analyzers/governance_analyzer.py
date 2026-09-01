import uuid

from app.models.issue import Issue



class GovernanceAnalyzer:


    def analyze(self,context):

        issues=[]


        governance=context.governance



        if not governance:

            return issues



        if governance.compliance_score <90:


            issues.append(

            Issue(

            id=str(uuid.uuid4()),

            category="Governance",

            issue_type="ComplianceIssue",

            severity="Medium",

            confidence=0.95,

            resource_id="subscription",

            resource_name="Azure Subscription",

            resource_type="Subscription",

            description=
            "Compliance score below threshold",

            evidence={
            "score":
            governance.compliance_score
            },

            business_impact=
            "Governance risk",

            risk_score=50,

            detected_by=
            "governance_analyzer"

            )

            )


        return issues