from app.agent.nodes.observe import observe


def test_observe():

    state = {
        "subscription_id":
            "6850d94e-3234-463d-aa51-615d3c486939"
    }

    result = observe(
        state
    )

    print("\n===== OBSERVE RESULT =====")

    print(
        result
    )

    assert result is not None

    assert isinstance(
        result,
        dict
    )

    assert (
        "azure_context"
        in result
    )

    assert (
        result["azure_context"]
        is not None
    )