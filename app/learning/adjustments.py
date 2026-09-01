"""Evidence-based proposals only; no function here changes production policy."""


FORBIDDEN_AUTOMATION = {"cpu_threshold", "savings_percentage", "risk_threshold", "approval_requirement"}


def propose_confidence_adjustments(metrics):
    proposals = []
    for bucket, value in metrics.get("confidence_calibration", {}).items():
        if value.get("calibration_status") != "READY":
            continue
        lower = float(bucket.split("-")[0])
        observed = value.get("verification_success_rate")
        if observed is None or abs(observed - lower) < 0.15:
            continue
        proposals.append({
            "kind": "confidence_calibration", "bucket": bucket,
            "observed_verification_rate": observed, "sample_size": value["sample_size"],
            "status": "PROPOSED", "requires_human_approval": True,
        })
    return proposals


def validate_adjustments(proposals):
    validated = []
    for proposal in proposals:
        forbidden = set(proposal).intersection(FORBIDDEN_AUTOMATION)
        result = dict(proposal)
        result["validation_status"] = "REJECTED" if forbidden else "VALIDATED"
        result["apply_to_production"] = False
        if forbidden:
            result["reason"] = "Autonomous production policy changes are prohibited"
        validated.append(result)
    return validated
