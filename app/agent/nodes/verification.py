from typing import Any

from app.models.execution import ExecutionStatus
from app.models.verification import VerificationStatus
from app.services.execution.execution_logger import ExecutionLogger


execution_logger = ExecutionLogger()


def _get_value(obj: Any, name: str, default=None):
    """
    Supports both Pydantic/model objects and dictionaries.
    """
    if isinstance(obj, dict):
        return obj.get(name, default)

    return getattr(obj, name, default)


def _calculate_realized_savings(
    baseline_monthly_cost,
    post_action_monthly_cost,
):
    if (
        baseline_monthly_cost is None
        or post_action_monthly_cost is None
    ):
        return None

    return round(
        max(
            0.0,
            baseline_monthly_cost
            - post_action_monthly_cost,
        ),
        2,
    )


def _calculate_accuracy(
    realized_savings,
    expected_savings,
):
    if (
        realized_savings is None
        or expected_savings is None
        or expected_savings <= 0
    ):
        return None

    accuracy = round(
        realized_savings / expected_savings,
        2,
    )

    return max(
        0.0,
        min(accuracy, 1.0),
    )


async def verify(state):
    """
    Phase 5.5 verification node.

    Responsibilities:
        1. Skip verification for dry-run executions.
        2. Verify real executions through VerificationRouter.
        3. Record Azure post-action state.
        4. Measure realized savings when cost data exists.
        5. Produce a verification report for the Learning node.
    """

    verification_router = state.get(
        "verification_router"
    )

    execution_results = state.get(
        "execution_results",
        []
    )

    results = []

    for execution in execution_results:

        resource_id = _get_value(
            execution,
            "resource_id",
        )

        action = _get_value(
            execution,
            "action",
        )

        action = getattr(action, "value", action)

        dry_run = _get_value(
            execution,
            "dry_run",
            False,
        )

        baseline_cost = _get_value(
            execution,
            "baseline_monthly_cost",
        )

        expected_savings = _get_value(
            execution,
            "expected_savings",
            0,
        ) or 0

        execution_status = _get_value(
            execution,
            "status",
        )

        execution_status = getattr(
            execution_status,
            "value",
            execution_status,
        )

        # ============================================================
        # DRY RUN
        # ============================================================

        if dry_run:

            results.append({

                "resource_id":
                    resource_id,

                "action":
                    action,

                "status":
                    "skipped",

                "verification_status":
                    "SKIPPED",

                "message":
                    (
                        "Verification skipped because "
                        "execution was dry-run."
                    ),

                "dry_run":
                    True,

                "baseline_monthly_cost":
                    baseline_cost,

                "post_action_monthly_cost":
                    None,

                "expected_savings":
                    expected_savings,

                "realized_savings":
                    None,

                "savings_measured":
                    False,

                "savings_status": "NOT_YET_VERIFIABLE",

                "savings_accuracy":
                    None,

                "expected_state": _get_value(
                    execution, "new_state", {}
                ) or {},

                "actual_state": {},

                "checks": {
                    "execution_mutated": False,
                    "verification_required": False,
                },
            })

            continue

        if str(execution_status).lower() != "success":

            results.append({

                "resource_id": resource_id,
                "action": action,
                "status": "skipped",
                "verification_status": "SKIPPED_EXECUTION_FAILED",
                "message": "Verification skipped because execution did not succeed.",
                "dry_run": False,
                "baseline_monthly_cost": baseline_cost,
                "post_action_monthly_cost": None,
                "expected_savings": expected_savings,
                "realized_savings": None,
                "savings_measured": False,
                "savings_status": "NOT_YET_VERIFIABLE",
                "savings_accuracy": None,
                "expected_state": _get_value(execution, "new_state", {}) or {},
                "actual_state": {},
                "checks": {"execution_succeeded": False},
            })

            continue

        # ============================================================
        # REAL EXECUTION
        # ============================================================

        try:

            if verification_router is None:
                raise ValueError(
                    "verification_router is required for real executions"
                )

            verification_result = (
                await verification_router.verify(
                    execution
                )
            )

        except Exception as exc:

            results.append({

                "resource_id":
                    resource_id,

                "action":
                    action,

                "status":
                    "verification_error",

                "verification_status":
                    "ERROR",

                "message":
                    str(exc),

                "dry_run":
                    False,

                "baseline_monthly_cost":
                    baseline_cost,

                "post_action_monthly_cost":
                    None,

                "expected_savings":
                    expected_savings,

                "realized_savings":
                    None,

                "savings_measured":
                    False,

                "savings_status": "NOT_YET_VERIFIABLE",

                "savings_accuracy":
                    None,
            })

            continue

        # Router may return None when no verifier exists.
        if verification_result is None:

            results.append({

                "resource_id":
                    resource_id,

                "action":
                    action,

                "status":
                    "unsupported",

                "verification_status":
                    "UNSUPPORTED",

                "message":
                    (
                        f"No verifier available "
                        f"for action '{action}'."
                    ),

                "dry_run":
                    False,

                "baseline_monthly_cost":
                    baseline_cost,

                "post_action_monthly_cost":
                    None,

                "expected_savings":
                    expected_savings,

                "realized_savings":
                    None,

                "savings_measured":
                    False,

                "savings_status": "NOT_YET_VERIFIABLE",

                "savings_accuracy":
                    None,
            })

            continue

        # ============================================================
        # NORMALIZE VERIFICATION RESULT
        # ============================================================

        azure_status = _get_value(
            verification_result,
            "status",
        )

        azure_status = getattr(
            azure_status,
            "value",
            azure_status,
        )

        message = _get_value(
            verification_result,
            "message",
        )

        post_action_cost = _get_value(
            verification_result,
            "post_action_monthly_cost",
        )

        verification_evidence = _get_value(
            verification_result,
            "evidence",
            {},
        ) or {}

        expected_state = _get_value(
            verification_result,
            "expected_state",
            _get_value(execution, "new_state", {}),
        ) or {}

        actual_state = _get_value(
            verification_result,
            "actual_state",
            {},
        ) or {}

        checks = _get_value(
            verification_result,
            "checks",
            {},
        ) or {}

        # Some verifiers may already provide cost information.
        if post_action_cost is None:

            post_action_cost = verification_evidence.get(
                "after_monthly_cost"
            )

        if post_action_cost is None:

            post_action_cost = _get_value(
                execution,
                "post_action_monthly_cost",
            )

        realized_savings = (
            _calculate_realized_savings(
                baseline_cost,
                post_action_cost,
            )
        )

        savings_accuracy = _calculate_accuracy(
            realized_savings,
            expected_savings,
        )

        savings_measured = (
            realized_savings is not None
        )

        # A failed post-mutation check is a safety event.  Rollback is
        # deterministic and only attempted when the executor captured a
        # usable before-state; no language-model decision is involved.
        rollback = _get_value(execution, "rollback", {}) or {}
        rollback_result = None
        rollback_verification = None
        rollback_status = rollback.get("rollback_status", "not_required")
        final_state = "AFTER_STATE"
        manual_intervention_required = False
        verification_failed = str(azure_status).lower() in {"failed", "error"}

        if verification_failed and _get_value(verification_result, "rollback_required", False):
            rollback["rollback_required"] = True
            router = state.get("execution_router")
            if not rollback.get("available") or router is None:
                rollback_status = "failed"
                manual_intervention_required = True
                final_state = "UNKNOWN"
            else:
                rollback["rollback_status"] = "pending"
                try:
                    rollback_result = await router.rollback(execution)
                    execution_logger.log({
                        "event": "rollback_execution",
                        "execution_id": _get_value(execution, "execution_id"),
                        "result": _get_value(rollback_result, "model_dump", lambda **_: rollback_result)(mode="json") if hasattr(rollback_result, "model_dump") else rollback_result,
                    })
                    if _get_value(rollback_result, "status") == ExecutionStatus.SUCCESS:
                        rollback_verification = await verification_router.verify(rollback_result)
                        verified = str(_get_value(rollback_verification, "status")).lower() in {"verificationstatus.passed", "passed", "success", "verified"}
                        rollback_status = "success" if verified else "failed"
                        final_state = "BEFORE_STATE" if verified else "UNKNOWN"
                        manual_intervention_required = not verified
                    else:
                        rollback_status = "failed"
                        final_state = "UNKNOWN"
                        manual_intervention_required = True
                except Exception as rollback_exc:
                    rollback_status = "failed"
                    final_state = "UNKNOWN"
                    manual_intervention_required = True
                    rollback["error"] = str(rollback_exc)

            rollback["rollback_status"] = rollback_status
            rollback["manual_intervention_required"] = manual_intervention_required
            if rollback_status == "success":
                execution.status = ExecutionStatus.FAILED_VERIFICATION
            else:
                execution.status = ExecutionStatus.ROLLBACK_FAILED

        # ============================================================
        # VERIFICATION STATUS
        # ============================================================

        if savings_measured:

            verification_status = "MEASURED"

        elif azure_status in (
            "SUCCESS", "VERIFIED", "PASSED",
            "success", "verified", "passed",
        ):

            verification_status = (
                "PENDING_MEASUREMENT"
            )

        else:

            verification_status = (
                azure_status or "UNKNOWN"
            )

        results.append({

            "resource_id":
                resource_id,

            "action":
                action,

            "status":
                (
                    "verified"
                    if azure_status in (
                    "SUCCESS",
                        "VERIFIED", "PASSED",
                        "success", "verified", "passed",
                    )
                    else "failed"
                ),

            "verification_status":
                verification_status,

            "message":
                message,

            "dry_run":
                False,

            "azure_verification":
                verification_result,

            "expected_state": expected_state,

            "actual_state": actual_state,

            "checks": checks,

            "evidence": verification_evidence,

            "rollback": rollback,

            "rollback_result": rollback_result,

            "rollback_verification": rollback_verification,

            "rollback_status": rollback_status,

            "final_state": final_state,

            "manual_intervention_required": manual_intervention_required,

            "execution_status": _get_value(execution, "status"),

            "baseline_monthly_cost":
                baseline_cost,

            "post_action_monthly_cost":
                post_action_cost,

            "expected_savings":
                expected_savings,

            "realized_savings":
                realized_savings,

            "savings_measured":
                savings_measured,

            "savings_status": "MEASURED" if savings_measured else "NOT_YET_VERIFIABLE",

            "savings_accuracy":
                savings_accuracy,
        })

    # ================================================================
    # AGGREGATION
    # ================================================================

    measured_results = [
        result
        for result in results
        if result["savings_measured"]
    ]

    expected_total = round(
        sum(
            result["expected_savings"] or 0
            for result in results
        ),
        2,
    )

    realized_values = [
        result["realized_savings"]
        for result in measured_results
        if result["realized_savings"] is not None
    ]

    if realized_values:

        realized_total = round(
            sum(realized_values),
            2,
        )

    else:

        realized_total = None

    if (
        expected_total > 0
        and realized_total is not None
    ):

        savings_accuracy = round(
            realized_total / expected_total,
            2,
        )

        savings_accuracy = max(
            0.0,
            min(
                savings_accuracy,
                1.0,
            ),
        )

    else:

        savings_accuracy = None

    real_results = [
        result
        for result in results
        if not result["dry_run"]
    ]

    verified_results = [
        result
        for result in real_results
        if result["status"] == "verified"
    ]

    if not real_results:

        overall_status = "SKIPPED"

    elif verified_results:

        overall_status = "VERIFIED"

    elif any(
        result["verification_status"] == "ERROR"
        for result in real_results
    ):

        overall_status = "VERIFICATION_ERROR"

    else:

        overall_status = "FAILED"

    verification_rate = (
        len(verified_results)
        / len(real_results)
        if real_results
        else 0.0
    )

    report = {

        "overall_status":
            overall_status,

        "expected_savings":
            expected_total,

        "realized_savings":
            realized_total,

        "savings_accuracy":
            savings_accuracy,

        "savings_measured":
            bool(measured_results),

        "verification_rate":
            round(
                verification_rate,
                2,
            ),

        "results":
            results,

        "recommendations":
            [],
    }

    return {
        **state,

        "verification_report":
            report,
    }
