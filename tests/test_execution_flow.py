import os
import sys
from pathlib import Path
import asyncio
import pytest
from dotenv import load_dotenv

load_dotenv()

sys.path.append(
    str(Path(__file__).resolve().parents[1])
)

from app.agent.graph import finops_agent


@pytest.mark.asyncio
async def test_real_azure_finops():

    subscription_id = os.getenv(
        "AZURE_SUBSCRIPTION_ID",
        "6850d94e-3234-463d-aa51-615d3c486939"
    )

    initial_state = {
        "user_request": (
            "Analyze the Azure resources in RG_GhadaMaalej "
            "and identify cost optimization opportunities."
        ),

        "subscription_id": subscription_id,

        # Tell your application which RG we're testing
        "resource_group": "RG_GhadaMaalej",

        "azure_context": None,
        "finops_context": None,
        "memory_context": [],

        "observed": {},

        "cost_issues": [],
        "performance_issues": [],
        "security_issues": [],
        "governance_issues": [],

        "recommendations": [],

        "validated_recommendations": [],
        "validation_errors": [],

        "pending_approval": [],
        "approved_recommendations": [],

        "execution_results": [],
        "verification_results": [],

        "learning": {},
        "logs": [],
    }

    result = await finops_agent.ainvoke(initial_state)

    print("\n")
    print("=" * 80)
    print("REAL AZURE FINOPS TEST")
    print("=" * 80)

    print("\n--- COST ISSUES ---")
    for issue in result.get("cost_issues", []):
        print(issue)

    print("\n--- PERFORMANCE ISSUES ---")
    for issue in result.get("performance_issues", []):
        print(issue)

    print("\n--- RECOMMENDATIONS ---")
    for recommendation in result.get("recommendations", []):
        print(recommendation)

    print("\n--- EXECUTION RESULTS ---")
    for execution in result.get("execution_results", []):
        print(execution)

    print("\n--- VERIFICATION RESULTS ---")
    for verification in result.get("verification_results", []):
        print(verification)

    print("\n" + "=" * 80)

    assert result is not None