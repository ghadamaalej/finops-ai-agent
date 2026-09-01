from types import SimpleNamespace

import pytest

from app.agent.nodes.validator import validate
from app.services.execution.execution_router import ExecutionRouter
from app.services.execution.base_executor import BaseExecutor
from app.services.execution.recommendation_to_request import (
    recommendation_to_execution_request,
)
from app.models.execution import (
    ActionType,
    ExecutionStatus,
)
from app.models.recommendation import Recommendation


# ============================================================
# Fake VM executor
# ============================================================

class FakeVMExecutor(BaseExecutor):

    async def execute(self, request):

        await self.validate(request)

        if request.dry_run:
            return self.dry_run_result(request)

        raise AssertionError(
            "Real Azure execution must NOT happen in dry-run test"
        )


# ============================================================
# Fake verification result
# ============================================================

class FakeVerificationResult:

    def __init__(
        self,
        resource_id,
        action,
        status,
        message,
    ):
        self.resource_id = resource_id
        self.action = action
        self.status = status
        self.message = message


class FakeVerifier:

    async def verify(self, execution_result):

        assert execution_result.dry_run is True

        return FakeVerificationResult(
            resource_id=execution_result.resource_id,
            action=execution_result.action,
            status="skipped",
            message=(
                "Verification skipped because "
                "execution was dry-run."
            ),
        )


# ============================================================
# TEST
# ============================================================

@pytest.mark.asyncio
async def test_full_dry_run_execution_flow():

    print(
        "\n"
        "============================================================\n"
        "DRY-RUN FINOPS EXECUTION FLOW TEST\n"
        "============================================================"
    )

    resource_id = (
        "/subscriptions/test-subscription/"
        "resourceGroups/rg-finops-test/"
        "providers/Microsoft.Compute/"
        "virtualMachines/finops-test-vm"
    )

    resource_name = "finops-test-vm"

    # --------------------------------------------------------
    # 1. Analyzer issue
    # --------------------------------------------------------

    issue = SimpleNamespace(

        id="issue-001",

        resource_id=resource_id,

        resource_name=resource_name,

        current_monthly_cost=88.33,

        estimated_monthly_savings=44.17,

        currency="USD",

        cost_source="Azure Retail Prices",

        cost_type="estimated",

        is_estimated=True,

        cost_data_available=True,

        confidence=0.90,
    )

    print("\n[1] Analyzer issue")
    print(
        f"Resource : {issue.resource_name}"
    )
    print(
        f"Cost     : ${issue.current_monthly_cost}"
    )
    print(
        f"Savings  : ${issue.estimated_monthly_savings}"
    )

    # --------------------------------------------------------
    # 2. LLM recommendation
    # --------------------------------------------------------

    recommendation = Recommendation(

        title="Rightsize underutilized VM",

        source_issue_id=issue.id,

        resource_id=resource_id,

        resource_name=resource_name,

        action="stop_vm",

        current_cost=88.33,

        projected_cost=44.16,

        estimated_savings=44.17,

        currency="USD",

        cost_source="Azure Retail Prices",

        cost_type="estimated",

        is_estimated=True,

        confidence=0.90,

        priority="High",

        roi="50% estimated reduction",

        implementation_risk="Medium",

        requires_approval=True,

        execution_plan=[
            "Review VM utilization",
            "Approve VM stop operation",
            "Deallocate the VM",
        ],

        explanation=(
            "The VM has sustained low CPU utilization. "
            "Retail pricing indicates an estimated "
            "monthly cost of $88.33."
        ),
    )

    print("\n[2] Recommendation generated")
    print(
        f"Action   : {recommendation.action}"
    )
    print(
        f"Resource : {recommendation.resource_name}"
    )
    print(
        f"Savings  : ${recommendation.estimated_savings}"
    )

    # --------------------------------------------------------
    # 3. Validate
    # --------------------------------------------------------

    state = {

        "issues": [
            issue
        ],

        "recommendations": [
            recommendation
        ],

        "recommendation_intelligence": {
            "recommendation_confidence": 0.90
        },

        "validated_recommendations": [],

        "validation_errors": [],
    }

    validated_state = validate(state)

    validated = validated_state[
        "validated_recommendations"
    ]

    rejected = validated_state[
        "validation_errors"
    ]

    print("\n[3] Validation")

    print(
        f"Valid    : {len(validated)}"
    )

    print(
        f"Rejected : {len(rejected)}"
    )

    assert len(validated) == 1
    assert len(rejected) == 0

    validated_recommendation = validated[0]

    assert (
        validated_recommendation.resource_id
        == resource_id
    )

    assert (
        validated_recommendation.current_cost
        == 88.33
    )

    assert (
        validated_recommendation.estimated_savings
        == 44.17
    )

    assert (
        validated_recommendation.projected_cost
        == 44.16
    )

    assert (
        validated_recommendation.cost_source
        == "Azure Retail Prices"
    )

    assert (
        validated_recommendation.cost_type
        == "estimated"
    )

    assert (
        validated_recommendation.is_estimated
        is True
    )

    print(
        "PASS: Recommendation validated"
    )

    # --------------------------------------------------------
    # 4. Approval
    # --------------------------------------------------------

    # Simulate the Approval node.
    #
    # The real Approval node should populate this field
    # after user/system approval.

    approved_recommendations = [
        validated_recommendation
    ]

    assert len(
        approved_recommendations
    ) == 1

    print("\n[4] Approval")
    print(
        "Approved recommendations: 1"
    )

    # --------------------------------------------------------
    # 5. Recommendation -> ExecutionRequest
    # --------------------------------------------------------

    execution_request = (
        recommendation_to_execution_request(
            validated_recommendation
        )
    )

    print(
        "\n[5] ExecutionRequest"
    )

    print(
        f"Action       : "
        f"{execution_request.action}"
    )

    print(
        f"Resource     : "
        f"{execution_request.resource_id}"
    )

    print(
        f"Savings      : "
        f"${execution_request.estimated_savings}"
    )

    print(
        f"Confidence   : "
        f"{execution_request.confidence}"
    )

    print(
        f"Approval     : "
        f"{execution_request.requires_approval}"
    )

    print(
        f"Dry run      : "
        f"{execution_request.dry_run}"
    )

    assert (
        execution_request.action
        == ActionType.STOP_VM
    )

    assert (
        execution_request.resource_id
        == resource_id
    )

    assert (
        execution_request.estimated_savings
        == 44.17
    )

    assert (
        execution_request.confidence
        == 0.90
    )

    assert (
        execution_request.requires_approval
        is True
    )

    assert (
        execution_request.dry_run
        is True
    )

    print(
        "PASS: Recommendation -> ExecutionRequest"
    )

    vm_executor = FakeVMExecutor()

    router = ExecutionRouter(

        vm_executor=vm_executor,

        disk_executor=vm_executor,

        network_executor=vm_executor,

        storage_executor=vm_executor,

        governance_executor=vm_executor,
    )

    execution_result = await router.execute(
        execution_request
    )

    print(
        "\n[6] ExecutionResult"
    )

    print(
        f"Status       : "
        f"{execution_result.status}"
    )

    print(
        f"Action       : "
        f"{execution_result.action}"
    )

    print(
        f"Resource     : "
        f"{execution_result.resource_id}"
    )

    print(
        f"Dry run      : "
        f"{execution_result.dry_run}"
    )

    print(
        f"Message      : "
        f"{execution_result.message}"
    )

    assert (
        execution_result.status
        == ExecutionStatus.DRY_RUN
    )

    assert (
        execution_result.action
        == ActionType.STOP_VM
    )

    assert (
        execution_result.resource_id
        == resource_id
    )

    assert (
        execution_result.dry_run
        is True
    )

    print(
        "PASS: ExecutionResult SUCCESS"
    )

    # --------------------------------------------------------
    # 7. Verification
    # --------------------------------------------------------

    verifier = FakeVerifier()

    verification_result = await verifier.verify(
        execution_result
    )

    print(
        "\n[7] VerificationResult"
    )

    print(
        f"Status       : "
        f"{verification_result.status}"
    )

    print(
        f"Message      : "
        f"{verification_result.message}"
    )

    assert (
        verification_result.status
        == "skipped"
    )

    assert (
        verification_result.resource_id
        == resource_id
    )

    print(
        "PASS: Verification SKIPPED"
    )

    # --------------------------------------------------------
    # 8. Learning input
    # --------------------------------------------------------

    learning_state = {

        "execution_results": [
            execution_result
        ],

        "verification_results": [
            verification_result
        ],

        "recommendations": [
            validated_recommendation
        ],
    }

    assert len(
        learning_state["execution_results"]
    ) == 1

    assert len(
        learning_state["verification_results"]
    ) == 1

    print(
        "\n[8] Learning"
    )

    print(
        "Execution result available : YES"
    )

    print(
        "Verification result available: YES"
    )

    print(
        "Learning input ready        : YES"
    )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print(
        "\n"
        "============================================================"
    )

    print(
        "DRY-RUN FINOPS EXECUTION FLOW PASSED"
    )

    print(
        "============================================================"
    )
