from app.services.azure_context_builder import AzureContextBuilder


def test_context_builder():

    subscription_id = (
        "6850d94e-3234-463d-aa51-615d3c486939"
    )


    builder = AzureContextBuilder()


    context = builder.build(
        subscription_id
    )


    print("\n===== CONTEXT TEST =====")


    print(
        "Subscription:",
        context.subscription_id
    )


    print(
        "Resources:",
        len(context.resources)
    )


    print(
        "Metrics:",
        len(context.metrics)
    )


    print(
        "Security findings:",
        len(context.security_findings)
    )


    print(
    "Cost records:",
    len(context.resource_costs)
    )


    assert context.subscription_id == subscription_id

    assert len(context.resources) > 0