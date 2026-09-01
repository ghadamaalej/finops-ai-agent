import pytest

from app.learning.outcome_metrics import calculate_outcome_metrics
from app.learning.outcomes import build_outcome, feedback_for
from app.agent.nodes.learning import learn
from app.learning.adjustments import propose_confidence_adjustments, validate_adjustments
from app.models.execution import ActionType, ExecutionResult, ExecutionStatus
from app.models.recommendation import Recommendation


def recommendation(confidence=0.6):
    return Recommendation(
        title="Rightsize", source_issue_id="rec-1", resource_id="vm-1", resource_name="vm-1",
        action="resize_vm", action_type="resize_vm", current_cost=88.33,
        potential_savings=61.83, estimated_savings=61.83, projected_cost=26.5,
        confidence=confidence, cost_source="Azure Retail Prices", cost_type="estimated",
    )


def execution(status=ExecutionStatus.SUCCESS, dry_run=False):
    return ExecutionResult(
        action=ActionType.RESIZE_VM, resource_id="vm-1", status=status,
        message="result", dry_run=dry_run, previous_state={"sku": "D2s_v6"}, new_state={"sku": "B2s_v2"},
    )


def verification(status="PENDING_MEASUREMENT", realized=None, rollback_status="not_required", final_state="AFTER_STATE"):
    return {
        "resource_id": "vm-1", "verification_status": status, "actual_state": {"sku": "B2s_v2"},
        "checks": {"sku_changed": status != "FAILED"}, "evidence": {}, "realized_savings": realized,
        "savings_status": "MEASURED" if realized is not None else "NOT_YET_VERIFIABLE",
        "rollback": {"rollback_required": rollback_status != "not_required"},
        "rollback_status": rollback_status, "final_state": final_state,
        "manual_intervention_required": rollback_status == "failed",
    }


def test_successful_execution_outcome_keeps_estimated_and_realized_separate():
    outcome = build_outcome(recommendation(), execution(), verification())
    assert outcome.execution["status"] == "success"
    assert outcome.verification["status"] == "PENDING_MEASUREMENT"
    assert outcome.savings["estimated"] == 61.83
    assert outcome.savings["realized"] is None
    assert outcome.savings["status"] == "NOT_YET_VERIFIABLE"
    with pytest.raises(Exception):
        outcome.resource_id = "changed"


def test_dry_run_outcome_is_not_an_execution_success():
    outcome = build_outcome(recommendation(), execution(ExecutionStatus.DRY_RUN, True), verification("SKIPPED"))
    metrics = calculate_outcome_metrics([outcome])
    assert outcome.execution["dry_run"] is True
    assert metrics["execution_success_rate"] is None
    assert outcome.savings["realized"] is None


def test_failed_verification_and_successful_rollback_are_recorded():
    outcome = build_outcome(recommendation(), execution(ExecutionStatus.FAILED_VERIFICATION), verification("FAILED", rollback_status="success", final_state="BEFORE_STATE"))
    assert outcome.rollback == {"required": True, "status": "success", "verified": True, "manual_intervention_required": False}
    assert calculate_outcome_metrics([outcome])["rollback_success_rate"] == 1.0


def test_failed_rollback_requires_manual_action_and_affects_metrics():
    outcome = build_outcome(recommendation(), execution(ExecutionStatus.ROLLBACK_FAILED), verification("FAILED", rollback_status="failed", final_state="UNKNOWN"))
    assert outcome.rollback["manual_intervention_required"] is True
    metrics = calculate_outcome_metrics([outcome])
    assert metrics["rollback_failure_rate"] == 1.0


def test_realized_savings_requires_post_action_cost_evidence():
    unmeasured = build_outcome(recommendation(), execution(), verification())
    measured = build_outcome(recommendation(), execution(), verification("MEASURED", realized=57.42))
    assert unmeasured.savings["realized"] is None
    assert measured.savings["realized"] == 57.42
    assert calculate_outcome_metrics([measured])["savings_prediction_error"] == 0.07


def test_feedback_tracks_approval_execution_and_verification_without_changing_outcome():
    outcome = build_outcome(recommendation(), execution(), verification())
    feedback = feedback_for(recommendation(), outcome, approved=True)
    assert feedback == {"recommendation_id": "rec-1", "resource_id": "vm-1", "approved": True, "decision": "APPROVED", "executed": True, "verified": True, "failed": False}


def test_learning_node_records_outcome_and_persists_only_with_injected_repository():
    class Repository:
        saved = None
        def save(self, outcomes, feedback, metrics):
            self.saved = outcomes, feedback, metrics

    repository = Repository()
    result = learn({
        "recommendations": [recommendation()], "execution_results": [execution()],
        "verification_report": {"results": [verification()]},
        "approved_recommendation_ids": ["rec-1"], "outcome_repository": repository,
        "cost_history": [], "execution_history": [], "verification_history": [],
    })
    assert len(result["optimization_outcomes"]) == 1
    assert result["learning"]["recommendation_feedback"][0]["approved"] is True
    assert repository.saved[0][0].resource_id == "vm-1"


def test_learning_analytics_aggregates_dimensions_and_excludes_dry_runs():
    outcomes = [
        build_outcome(recommendation(), execution(), verification("MEASURED", realized=57.42)),
        build_outcome(recommendation(), execution(ExecutionStatus.DRY_RUN, True), verification("SKIPPED")),
        build_outcome(recommendation(), execution(ExecutionStatus.FAILED_VERIFICATION), verification("FAILED", rollback_status="success", final_state="BEFORE_STATE")),
        build_outcome(recommendation(), execution(ExecutionStatus.ROLLBACK_FAILED), verification("FAILED", rollback_status="failed", final_state="UNKNOWN")),
    ]
    feedback = [
        {"decision": "APPROVED"}, {"decision": "REJECTED"},
        {"decision": "DEFERRED"}, {"decision": "DEFERRED"},
    ]
    metrics = calculate_outcome_metrics(outcomes, feedback, minimum_samples=5)
    assert metrics["total_recommendations"] == 4
    assert metrics["total_executions"] == 3
    assert metrics["total_dry_runs"] == 1
    assert metrics["total_verified"] == 1
    assert metrics["total_failed"] == 2
    assert metrics["execution_success_rate"] == 0.33
    assert metrics["verification_success_rate"] == 0.33
    assert metrics["rollback_rate"] == 0.67
    assert metrics["rollback_success_rate"] == 0.5
    assert metrics["approval_rate"] == 0.25
    assert metrics["rejection_rate"] == 0.25
    assert metrics["predicted_savings"] == 247.32
    assert metrics["realized_savings"] == 57.42
    bucket = metrics["confidence_calibration"]["0.60-0.69"]
    assert bucket["sample_size"] == 4
    assert bucket["calibration_status"] == "INSUFFICIENT_DATA"


def test_confidence_calibration_only_becomes_ready_after_minimum_sample_size():
    outcomes = [build_outcome(recommendation(0.72), execution(), verification()) for _ in range(3)]
    calibration = calculate_outcome_metrics(outcomes, minimum_samples=3)["confidence_calibration"]["0.70-0.79"]
    assert calibration["sample_size"] == 3
    assert calibration["verification_success_rate"] == 1.0
    assert calibration["calibration_status"] == "READY"


def test_adjustments_are_proposed_and_validated_but_never_applied():
    metrics = {"confidence_calibration": {"0.60-0.69": {
        "sample_size": 20, "verification_success_rate": 0.9, "calibration_status": "READY",
    }}}
    proposals = propose_confidence_adjustments(metrics)
    assert proposals[0]["status"] == "PROPOSED"
    validated = validate_adjustments(proposals)
    assert validated[0]["validation_status"] == "VALIDATED"
    assert validated[0]["apply_to_production"] is False


def test_learning_continues_when_persistence_is_unavailable():
    class UnavailableRepository:
        def save(self, *_):
            raise ConnectionError("database unavailable")

    result = learn({
        "recommendations": [recommendation()], "execution_results": [execution()],
        "verification_report": {"results": [verification()]}, "outcome_repository": UnavailableRepository(),
        "cost_history": [], "execution_history": [], "verification_history": [],
    })
    assert result["optimization_outcomes"][0].resource_id == "vm-1"
    assert result["learning"]["persistence"]["status"] == "UNAVAILABLE"
