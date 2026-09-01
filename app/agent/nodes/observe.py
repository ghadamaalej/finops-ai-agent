from app.services.azure_context_builder import AzureContextBuilder
from app.agent.state import AgentState

builder = AzureContextBuilder()

def observe(state: AgentState):

    subscription_id = state.get(
        "subscription_id"
    )

    if not subscription_id:

        raise ValueError(
            "subscription_id is required"
        )

    context = builder.build(
        subscription_id
    )

    print(
        "===== AZURE CONTEXT ====="
    )

    print(
        "Subscription:",
        context.subscription_id
    )

    print(
        "Resources:",
        len(context.resources)
    )

    return {
        **state,
        "azure_context": context
    }