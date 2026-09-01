from app.agent.nodes.approval import approval


def test_approval():

    state={

        "validated_recommendations":[

            type(
                "Recommendation",
                (),
                {
                    "title":"Stop VM",
                    "requires_approval":True
                }
            )()

        ]

    }


    result=approval(state)


    assert len(
        result["pending_approval"]
    ) == 1


    assert len(
        result["approved_recommendations"]
    ) == 0
    