def approval(state):

    auto_execute = []
    pending_approval = []
    approved_ids = set(state.get("approved_recommendation_ids", []))

    for rec in state.get("validated_recommendations", []):

        # Human/API approval is explicit.  Recommendations that do not need
        # approval may continue automatically; those that do only continue
        # after their source issue or resource was approved.
        identifier = getattr(rec, "source_issue_id", None) or getattr(rec, "resource_id", None)
        if not rec.requires_approval or identifier in approved_ids:
            auto_execute.append(rec)
        else:
            pending_approval.append(rec)


    return {
        **state,
        "approved_recommendations": auto_execute,
        "pending_approval": pending_approval
    }
