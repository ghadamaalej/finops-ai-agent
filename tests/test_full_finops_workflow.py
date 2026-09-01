import pytest

from app.agent.graph import finops_agent


SUBSCRIPTION_ID = (
    "6850d94e-3234-463d-aa51-615d3c486939"
)


@pytest.mark.asyncio
async def test_full_finops_workflow():

    state = {
        "subscription_id": SUBSCRIPTION_ID,

        "user_request":
            "Analyze Azure environment for "
            "FinOps optimization opportunities.",
    }

    # =========================================================
    # RUN FULL GRAPH
    # =========================================================

    result = await finops_agent.ainvoke(
        state
    )

    # =========================================================
    # GRAPH COMPLETED
    # =========================================================

    assert result is not None

    # =========================================================
    # OBSERVATION
    # =========================================================

    assert "azure_context" in result

    # =========================================================
    # ANALYZERS
    # =========================================================

    assert "cost_issues" in result

    assert "performance_issues" in result

    assert "security_issues" in result

    assert "governance_issues" in result

    # =========================================================
    # MERGE
    # =========================================================

    assert "issues" in result

    assert isinstance(
        result["issues"],
        list
    )

    # =========================================================
    # RECOMMENDATION PIPELINE
    # =========================================================

    assert "recommendations" in result

    assert isinstance(
        result["recommendations"],
        list
    )

    assert (
        "validated_recommendations"
        in result
    )

    assert isinstance(
        result[
            "validated_recommendations"
        ],
        list
    )

    # =========================================================
    # APPROVAL
    # =========================================================

    assert (
        "approved_recommendations"
        in result
        or
        "pending_approval"
        in result
    )

    # =========================================================
    # EXECUTION IS OPTIONAL
    #
    # If there are approved recommendations:
    #
    #     approval → execution → verification → learning
    #
    # Otherwise:
    #
    #     approval → learning
    # =========================================================

    approved = result.get(
        "approved_recommendations",
        []
    )

    if approved:

        assert (
            "execution_results"
            in result
        )

        assert (
            "verification_report"
            in result
        )

    # =========================================================
    # LEARNING
    #
    # Both graph paths must eventually reach learning.
    # =========================================================

    assert "learning" in result

    assert isinstance(
        result["learning"],
        dict
    )