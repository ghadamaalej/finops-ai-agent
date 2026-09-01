def human_approval(state):

    approved=[]

    rejected=[]


    for rec in state["pending_approval"]:

        decision = state.get(
            "approval_decision",
            False
        )


        if decision:
            approved.append(rec)

        else:
            rejected.append(rec)



    return {

        **state,

        "approved_recommendations":
            approved,

        "rejected_recommendations":
            rejected
    }