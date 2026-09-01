"""Deterministic Phase 6.2 analytics over immutable outcomes and feedback."""

from collections import defaultdict


SUCCESSFUL_VERIFICATIONS = {"MEASURED", "PENDING_MEASUREMENT", "PASSED"}
MUTATED_STATUSES = {"success", "failed_verification", "rollback_failed"}


def _rate(numerator, denominator):
    return round(numerator / denominator, 2) if denominator else None


def _bucket(confidence):
    lower = min(0.9, int(float(confidence or 0) * 10) / 10)
    upper = 1.0 if lower == 0.9 else lower + 0.09
    return f"{lower:.2f}-{upper:.2f}"


def calculate_outcome_metrics(outcomes, feedback=None, minimum_samples=10):
    """Return measurements only; this function does not calibrate or mutate data."""
    outcomes, feedback = list(outcomes), list(feedback or [])
    real = [item for item in outcomes if not item.execution.get("dry_run", False)]
    dry_runs = [item for item in outcomes if item.execution.get("dry_run", False)]
    completed = [item for item in real if item.execution.get("status") not in {"pending", "approved", "dry_run"}]
    mutated = [item for item in real if item.execution.get("status") in MUTATED_STATUSES]
    verification_complete = [item for item in real if item.verification.get("status") not in {"NOT_EXECUTED", "SKIPPED", "SKIPPED_EXECUTION_FAILED"}]
    rollback_attempted = [item for item in outcomes if item.rollback.get("status") not in {"not_required", "pending"}]
    buckets, prediction_errors, realized_values = defaultdict(lambda: {"sample_size": 0, "verified": 0}), [], []
    for item in outcomes:
        bucket = buckets[_bucket(item.recommendation.get("confidence"))]
        bucket["sample_size"] += 1
        if item.verification.get("status") in SUCCESSFUL_VERIFICATIONS:
            bucket["verified"] += 1
        estimated, realized = item.savings.get("estimated"), item.savings.get("realized")
        if realized is not None:
            realized_values.append(float(realized))
        if estimated and realized is not None:
            prediction_errors.append(abs(float(estimated) - float(realized)) / float(estimated))
    calibration = {
        label: {**values, "verification_success_rate": _rate(values["verified"], values["sample_size"]),
                "calibration_status": "READY" if values["sample_size"] >= minimum_samples else "INSUFFICIENT_DATA",
                "minimum_samples": minimum_samples}
        for label, values in sorted(buckets.items())
    }
    total_recommendations = len(feedback) or len({item.recommendation_id for item in outcomes if item.recommendation_id})
    approved = sum(item.get("decision") == "APPROVED" or item.get("approved") is True for item in feedback)
    rejected = sum(item.get("decision") == "REJECTED" for item in feedback)
    return {
        "total_recommendations": total_recommendations, "total_executions": len(real), "total_dry_runs": len(dry_runs),
        "total_verified": sum(item.verification.get("status") in SUCCESSFUL_VERIFICATIONS for item in outcomes),
        "total_failed": sum(item.execution.get("status") in {"failed", "failed_verification", "rollback_failed"} for item in real),
        "execution_success_rate": _rate(sum(item.execution.get("status") == "success" for item in completed), len(completed)),
        "verification_success_rate": _rate(sum(item.verification.get("status") in SUCCESSFUL_VERIFICATIONS for item in verification_complete), len(verification_complete)),
        "rollback_rate": _rate(sum(item.rollback.get("required", False) for item in mutated), len(mutated)),
        "rollback_success_rate": _rate(sum(item.rollback.get("status") == "success" for item in rollback_attempted), len(rollback_attempted)),
        "rollback_failure_rate": _rate(sum(item.rollback.get("status") == "failed" for item in rollback_attempted), len(rollback_attempted)),
        "approval_rate": _rate(approved, len(feedback)), "rejection_rate": _rate(rejected, len(feedback)),
        "predicted_savings": round(sum(float(item.savings.get("estimated") or 0) for item in outcomes), 2),
        "realized_savings": round(sum(realized_values), 2) if realized_values else None,
        "savings_prediction_error": round(sum(prediction_errors) / len(prediction_errors), 2) if prediction_errors else None,
        "confidence_calibration": calibration,
    }
