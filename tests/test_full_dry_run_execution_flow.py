import pytest

from app.agent.graph import finops_agent


@pytest.mark.asyncio
async def test_full_dry_run_execution_flow():

    state = {
        "subscription_id":
            "6850d94e-3234-463d-aa51-615d3c486939",

        "target_resource_id":
            "...",

        "dry_run":
            True,
    }

    result = await finops_agent.ainvoke(
        state
    )

    assert "execution_results" in result

    assert len(
        result["execution_results"]
    ) > 0

    verification_report = result.get(
        "verification_report"
    )

    assert verification_report is not None

    assert (
        verification_report["overall_status"]
        == "SKIPPED"
    )

    for verification in (
        verification_report["results"]
    ):

        assert (
            verification["verification_status"]
            == "SKIPPED"
        )

        assert (
            verification["dry_run"]
            is True
        )

        assert (
            verification["realized_savings"]
            is None
        )