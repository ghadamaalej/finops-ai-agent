from app.learning.forecast import CostForecaster
from app.learning.trend_analyzer import TrendAnalyzer
from app.learning.history import HistoricalSuccess
from app.learning.stability import ResourceStability
from app.learning.confidence import ConfidenceCalculator
from app.learning.outcomes import build_outcome, feedback_for
from app.learning.outcome_metrics import calculate_outcome_metrics
from app.learning.adjustments import propose_confidence_adjustments, validate_adjustments


forecaster = CostForecaster()
trend_analyzer = TrendAnalyzer()
historical_success = HistoricalSuccess()
stability_analyzer = ResourceStability()
confidence_calculator = ConfidenceCalculator()


def learn(state):

    # Phase 6 learns from immutable, observed outcomes.  It deliberately does
    # not alter recommendation confidence or production thresholds.
    verification_by_resource = {
        item.get("resource_id"): item
        for item in state.get("verification_report", {}).get("results", [])
    }
    recommendations_by_resource = {
        getattr(item, "resource_id", item.get("resource_id") if isinstance(item, dict) else None): item
        for item in state.get("recommendations", [])
    }
    outcomes = []
    for execution in state.get("execution_results", []):
        resource_id = getattr(execution, "resource_id", execution.get("resource_id") if isinstance(execution, dict) else None)
        recommendation = recommendations_by_resource.get(resource_id)
        if recommendation is not None:
            outcomes.append(build_outcome(recommendation, execution, verification_by_resource.get(resource_id)))
    approved_ids = set(state.get("approved_recommendation_ids", []))
    feedback_decisions = state.get("recommendation_decisions", {})
    feedback = [
        feedback_for(
            recommendation,
            next((outcome for outcome in outcomes if outcome.recommendation_id == getattr(recommendation, "source_issue_id", None)), None),
            getattr(recommendation, "source_issue_id", None) in approved_ids,
            (feedback_decisions.get(getattr(recommendation, "source_issue_id", None)) or {}).get("decision") if isinstance(feedback_decisions.get(getattr(recommendation, "source_issue_id", None)), dict) else feedback_decisions.get(getattr(recommendation, "source_issue_id", None)),
            (feedback_decisions.get(getattr(recommendation, "source_issue_id", None)) or {}).get("reason") if isinstance(feedback_decisions.get(getattr(recommendation, "source_issue_id", None)), dict) else None,
        )
        for recommendation in state.get("recommendations", [])
    ]
    outcome_metrics = calculate_outcome_metrics(outcomes, feedback)
    outcome_repository = state.get("outcome_repository")
    persistence = {"status": "NOT_CONFIGURED"}
    if outcome_repository is not None and (outcomes or feedback):
        try:
            persistence = outcome_repository.save(outcomes, feedback, outcome_metrics)
        except Exception as exc:
            # Learning-memory availability never changes an Azure outcome.
            persistence = {"status": "UNAVAILABLE", "error": str(exc)}
    proposals = validate_adjustments(propose_confidence_adjustments(outcome_metrics))

    history = state.get(
        "cost_history",
        []
    )

    executions = state.get(
        "execution_history",
        []
    )

    analyzer_confidence = state.get(
        "analyzer_confidence",
        0.5
    )

    verification_report = state.get(
        "verification_report",
        {}
    )


    expected = verification_report.get(
        "expected_savings",
        0
    )


    realized = verification_report.get(
        "realized_savings",
        0
    )


    if (
    expected is not None
    and realized is not None
    and float(expected) > 0
):

     savings_accuracy = (
        float(realized)
        / float(expected)
    )

     savings_accuracy = max(
        0,
        min(
            savings_accuracy,
            1
        )
    )

     savings_accuracy = round(
        savings_accuracy,
        2
    )

    else:

      savings_accuracy = None

 
    historical_success_rate = (
        historical_success.calculate(
            executions
        )
    )

    trend_result = (
        trend_analyzer.analyze(
            history
        )
    )

    forecast_result = (
        forecaster.predict_next_month(
            history
        )
    )

    forecast_confidence = (
        forecast_result.get(
            "confidence",
            0.0
        )
    )

    resource_stability = (
        stability_analyzer.calculate(
            history
        )
    )

    recommendation_confidence = (
        confidence_calculator.calculate(

            historical_success=
                historical_success_rate,

            forecast_confidence=
                forecast_confidence,

            analyzer_confidence=
                analyzer_confidence,

            resource_stability=
                resource_stability
        )
    )

    return {

        **state,

        "learning": {

            "savings_accuracy":
                savings_accuracy,

            "historical_success":
                historical_success_rate,

            "forecast_confidence":
                forecast_confidence,

            "resource_stability":
                resource_stability,

            "analyzer_confidence":
                analyzer_confidence,

            "recommendation_confidence":
                recommendation_confidence,

            "trend":
                trend_result,

            "forecast":
                forecast_result,

            "outcome_metrics": outcome_metrics,

            "recommendation_feedback": feedback,
            "persistence": persistence,
            "adjustment_proposals": proposals,

        }

        ,
        "optimization_outcomes": outcomes,
        "execution_history": [*state.get("execution_history", []), *outcomes],
        "verification_history": [*state.get("verification_history", []), *outcomes],

    }
