import os

import pytest

from app.services.azure_context_builder import AzureContextBuilder


SUBSCRIPTION_ID = "6850d94e-3234-463d-aa51-615d3c486939"

pytestmark = pytest.mark.skipif(
    os.getenv("RUN_LIVE_AZURE_TESTS") != "1",
    reason="Requires a real Azure session and writes refreshed cost snapshots.",
)


def test_live_cost_service():
    context = AzureContextBuilder().build(SUBSCRIPTION_ID)
    result = context.resource_costs

    print("\n" + "=" * 80)
    print("COST SERVICE RESULT")
    print("=" * 80)

    print("Type:", type(result))
    print("Result:", result)

    assert result
