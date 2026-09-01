from datetime import datetime, timezone

import pytest

from app.agent.nodes.intelligence_builder import build_intelligence_context
from app.models.azure import AzureContext, AzureResource


@pytest.fixture
def context_fixture():
    return AzureContext(
        subscription_id="test-subscription",
        collected_at=datetime.now(timezone.utc),
        resources=[
            AzureResource(
                id="/subscriptions/test/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-test",
                name="vm-test",
                type="Microsoft.Compute/virtualMachines",
                location="westeurope",
                resource_group="rg",
                subscription_id="test-subscription",
                sku="Standard_D2s_v5",
            )
        ],
    )


def test_intelligence(context_fixture):
    result = build_intelligence_context({"azure_context": context_fixture})
    finops = result["finops_context"]

    assert finops.subscription_id == "test-subscription"
    assert len(finops.resources) == 1
