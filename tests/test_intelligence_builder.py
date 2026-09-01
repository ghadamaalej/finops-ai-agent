from app.services.azure_context_builder import AzureContextBuilder
from app.agent.nodes.intelligence_builder import build_intelligence_context


def test_intelligence_builder():

    subscription_id = (
        "6850d94e-3234-463d-aa51-615d3c486939"
    )

    builder = AzureContextBuilder()

    azure_context = builder.build(
        subscription_id
    )


    state = {
        "azure_context": azure_context
    }


    result = build_intelligence_context(
        state
    )


    intelligence = result["finops_context"]


    print("\n===== INTELLIGENCE =====")


    print(
        "Total cost:",
        intelligence.cost.total_cost
    )


    print(
        "Health score:",
        intelligence.environment_health_score
    )


    print(
        "Observations:",
        intelligence.key_observations
    )


    assert intelligence is not None