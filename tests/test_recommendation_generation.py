import pytest

from app.agent.nodes.graph_recommendation_test import (
    recommendation_test_agent
)


@pytest.mark.asyncio
async def test_recommendation_generation():

    subscription_id = "6850d94e-3234-463d-aa51-615d3c486939"

    state = {

        "user_request":
            "Analyze my Azure environment and recommend cost optimizations.",

        "subscription_id":
            subscription_id,

        "azure_context": None,

        "finops_context": None,

        "observed": {},

        "cost_issues": [],
        "performance_issues": [],
        "security_issues": [],
        "governance_issues": [],

        "issues": [],

        "recommendations": [],

        "validated_recommendations": [],

        "validation_errors": [],

        "approved_recommendations": [],

        "pending_approval": [],

        "execution_results": [],

        "verification_results": [],

        "learning": {},

        "logs": [],

        "execution_router": None,

        "verification_router": None,

        "memory_context": [],

        "cost_history": []
    }


    result = await recommendation_test_agent.ainvoke(
        state
    )


    print("\n")
    print("=" * 70)
    print("PHASE 7 RECOMMENDATION TEST")
    print("=" * 70)


    print("\nGenerated recommendations:")

    for recommendation in result.get(
        "recommendations",
        []
    ):

        print(
            recommendation.model_dump(
                mode="json"
            )
        )


    print("\nValidated recommendations:")

    for recommendation in result.get(
        "validated_recommendations",
        []
    ):

        print(
            recommendation.model_dump(
                mode="json"
            )
        )


    print("\nValidation errors:")

    for error in result.get(
        "validation_errors",
        []
    ):

        print(error)


    print("\n" + "=" * 70)


    assert "recommendations" in result

    assert "validated_recommendations" in result

    assert "validation_errors" in result