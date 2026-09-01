from app.learning.recommendation_intelligence import (
    RecommendationIntelligence
)


intelligence = RecommendationIntelligence()


def recommendation_intelligence_node(state):

    cost_history = state.get(
        "cost_history",
        []
    )

    execution_history = state.get(
        "execution_history",
        []
    )

    issues = state.get(
        "issues",
        []
    )

    analyzer_confidence = 0.5

    if issues:

        confidences = []

        for issue in issues:

            confidence = getattr(
                issue,
                "confidence",
                None
            )

            if confidence is not None:

                confidences.append(
                    float(confidence)
                )

        if confidences:

            analyzer_confidence = (
                sum(confidences)
                / len(confidences)
            )

    intelligence_result = (
        intelligence.analyze(
            cost_history,
            execution_history,
            analyzer_confidence
        )
    )

    return {
        **state,

        "recommendation_intelligence":
            intelligence_result
    }