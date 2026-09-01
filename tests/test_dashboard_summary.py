from datetime import datetime

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from api import dashboard
from app.database.models import ApplicationUser, AzureConnection, Base, CostCache, LearningMetricMemory, OptimizationOutcomeMemory, RecommendationMemory
from app.models.recommendation import Recommendation
from app.services.dashboard_summary import DashboardSummaryService
from app.services.learning_service import LearningService
from app.services.azure_context_builder import _governance_resource_ids


SUBSCRIPTION_ID = "subscription-a"
RESOURCE_ID = f"/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-a"


def build_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


@pytest.mark.parametrize("affected_resources", [[], [RESOURCE_ID], None, 0])
def test_resource_id_collection_is_safe_for_legacy_governance_snapshots(affected_resources):
    assert dashboard._resource_id_collection(affected_resources) == ([] if not isinstance(affected_resources, list) else affected_resources)


def test_governance_producer_contract_keeps_ids_and_separates_legacy_counts():
    assert _governance_resource_ids([]) == ([], 0)
    assert _governance_resource_ids([RESOURCE_ID]) == ([RESOURCE_ID], 1)
    assert _governance_resource_ids(None) == ([], 0)
    assert _governance_resource_ids(0) == ([], 0)
    assert _governance_resource_ids(5) == ([], 5)


@pytest.mark.parametrize("environment", [
    {"governance": {"affected_resources": value}, "performance": {"resources": []}}
    for value in ([], [RESOURCE_ID], None, 0, 5)
] + [
    {"performance": {"resources": 0}, "security_findings": 0, "governance": {}},
    {"performance": {"resources": [{"resource_id": RESOURCE_ID, "metric_names": 0, "values": 0, "metric_errors": 0, "collected_at": "2026-01-01T00:00:00+00:00"}]}},
    None,
])
def test_resource_details_handles_malformed_persisted_evidence(monkeypatch, environment):
    session = build_session()
    user = ApplicationUser(entra_subject_id="subject-a", tenant_id="tenant-a", is_active=True)
    session.add(user)
    session.flush()
    session.add(AzureConnection(user_id=user.id, tenant_id="tenant-a", subscription_id=SUBSCRIPTION_ID, connection_status="CONNECTED"))
    metrics = {"subscription_id": SUBSCRIPTION_ID}
    if environment is not None:
        metrics["environment"] = environment
    session.add(LearningMetricMemory(metrics=metrics))
    session.commit()
    monkeypatch.setattr(dashboard, "SessionLocal", lambda: session)
    monkeypatch.setattr(dashboard, "validate_id_token", lambda _token: {"sub": "subject-a", "tid": "tenant-a"})
    monkeypatch.setattr(dashboard.ResourceCollector, "collect", lambda _self, _subscription: [{"id": RESOURCE_ID, "name": "JENKINS-VM", "type": "Microsoft.Compute/virtualMachines", "location": "westeurope", "configuration": {}}])
    from main import app
    response = TestClient(app).get("/api/dashboard/resources/details", params={"resource_id": RESOURCE_ID}, headers={"Authorization": "Bearer id-token"})
    assert response.status_code == 200
    assert set(response.json()) == {"resource", "metrics", "cost", "finops", "security", "governance", "evidence"}
    session.close()


def test_safe_isoformat_handles_datetime_and_string_timestamps():
    timestamp = datetime(2026, 1, 1)
    assert dashboard._safe_isoformat(timestamp) == timestamp.isoformat()
    assert dashboard._safe_isoformat("2026-01-01T00:00:00+00:00") == "2026-01-01T00:00:00+00:00"


def test_summary_aggregates_only_persisted_subscription_evidence():
    session = build_session()
    session.add_all(
        [
            CostCache(subscription_id=SUBSCRIPTION_ID, resource_id=RESOURCE_ID, resource_name="vm-a", service_name="Virtual Machines", monthly_cost=100, currency="USD"),
            CostCache(subscription_id="other", resource_id="/subscriptions/other/vm", resource_name="other", service_name="Storage", monthly_cost=500, currency="USD"),
            RecommendationMemory(recommendation_id="recommendation-a", resource_id=RESOURCE_ID, resource_name="vm-a", action="RESIZE", category="Underutilized VM", estimated_savings=40, confidence=0.9, approved=False),
            RecommendationMemory(recommendation_id="recommendation-other", resource_id="/subscriptions/other/vm", estimated_savings=500, approved=False),
            OptimizationOutcomeMemory(
                outcome_id="outcome-a",
                execution_id="execution-a",
                recommendation_id="recommendation-a",
                resource_id=RESOURCE_ID,
                recorded_at=datetime(2026, 1, 1),
                outcome={
                    "execution": {"action": "RESIZE", "status": "SUCCESS"},
                    "verification": {"status": "MEASURED"},
                    "savings": {"realized": 12.5},
                },
            ),
        ]
    )
    session.commit()

    summary = DashboardSummaryService().build(session, SUBSCRIPTION_ID)

    assert summary["cost"]["monthly"] == 100
    assert summary["savings"]["potential_monthly"] == 40
    assert summary["savings"]["realized_monthly"] == 12.5
    assert summary["savings"]["verified_actions"] == 1
    assert summary["resources"]["total"] == 1
    assert summary["agent"]["pending_approval"] == 1
    assert summary["security"]["score"] is None
    assert summary["cost"]["cost_source"] is None
    assert summary["cost_resources"][0]["cost_data_available"] is True
    assert summary["recent_actions"][0]["verification_status"] == "MEASURED"


def test_verified_action_without_cost_evidence_does_not_invent_realized_savings():
    session = build_session()
    session.add(
        OptimizationOutcomeMemory(
            outcome_id="outcome-no-cost-evidence",
            execution_id="execution-no-cost-evidence",
            resource_id=RESOURCE_ID,
            outcome={"verification": {"status": "PASSED"}, "savings": {"realized": None}},
        )
    )
    session.commit()

    summary = DashboardSummaryService().build(session, SUBSCRIPTION_ID)

    assert summary["savings"]["verified_actions"] == 1
    assert summary["savings"]["realized_monthly"] is None
    assert summary["resources"]["total"] is None


def test_cost_composition_omits_zero_cost_resources_and_preserves_total():
    session = build_session()
    session.add_all([
        CostCache(subscription_id=SUBSCRIPTION_ID, resource_id="/subscriptions/subscription-a/vm", service_name="Virtual Machines", monthly_cost=100, currency="USD"),
        CostCache(subscription_id=SUBSCRIPTION_ID, resource_id="/subscriptions/subscription-a/network", service_name="microsoft.network", monthly_cost=0, currency="USD"),
        CostCache(subscription_id=SUBSCRIPTION_ID, resource_id="/subscriptions/subscription-a/storage", service_name="microsoft.storage", monthly_cost=None, currency="USD"),
    ])
    session.commit()

    summary = DashboardSummaryService().build(session, SUBSCRIPTION_ID)

    assert summary["cost"]["monthly"] == 100
    assert summary["cost_composition"] == [{"name": "Virtual Machines", "monthly_cost": 100}]


def test_cost_drivers_are_top_five_sorted_and_include_backend_percentages():
    session = build_session()
    session.add_all([
        CostCache(subscription_id=SUBSCRIPTION_ID, resource_id=f"/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-{index}", resource_name=f"vm-{index}", service_name="Virtual Machines", monthly_cost=100 - index * 10, currency="USD")
        for index in range(7)
    ])
    session.commit()

    drivers = DashboardSummaryService().build(session, SUBSCRIPTION_ID)["cost_drivers"]

    assert len(drivers) == 5
    assert [item["monthly_cost"] for item in drivers] == [100, 90, 80, 70, 60]
    assert drivers[0]["resource_type"] == "microsoft.compute/virtualmachines"
    assert drivers[0]["service_name"] == "Virtual Machines"
    assert drivers[0]["percent_of_total"] == 20.41


def test_dashboard_endpoint_reads_only_the_authenticated_users_connection(monkeypatch):
    session = build_session()
    user = ApplicationUser(entra_subject_id="subject-a", tenant_id="tenant-a", is_active=True)
    session.add(user)
    session.flush()
    session.add(AzureConnection(user_id=user.id, tenant_id="tenant-a", subscription_id=SUBSCRIPTION_ID, connection_status="CONNECTED"))
    session.commit()
    monkeypatch.setattr(dashboard, "SessionLocal", lambda: session)
    monkeypatch.setattr(dashboard, "validate_id_token", lambda _token: {"sub": "subject-a", "tid": "tenant-a"})

    summary = dashboard.dashboard_summary(HTTPAuthorizationCredentials(scheme="Bearer", credentials="id-token"))

    assert summary["subscription_id"] == SUBSCRIPTION_ID


def test_dashboard_endpoint_returns_persisted_environment_metrics(monkeypatch):
    session = build_session()
    user = ApplicationUser(entra_subject_id="subject-a", tenant_id="tenant-a", is_active=True)
    session.add(user)
    session.flush()
    session.add(AzureConnection(user_id=user.id, tenant_id="tenant-a", subscription_id=SUBSCRIPTION_ID, connection_status="CONNECTED"))
    session.add(LearningMetricMemory(metrics={
        "subscription_id": SUBSCRIPTION_ID,
        "environment": {
            "security": {"score": 80, "critical": 1, "high": 1, "total": 2},
            "governance": {"compliance": 96.5, "violations": 2, "affected_resources": 2},
            "performance": {"average_cpu": 34.25, "underutilized": 1, "overutilized": 2},
        },
    }))
    session.commit()
    monkeypatch.setattr(dashboard, "SessionLocal", lambda: session)
    monkeypatch.setattr(dashboard, "validate_id_token", lambda _token: {"sub": "subject-a", "tid": "tenant-a"})

    from main import app

    client = TestClient(app)
    response = client.get("/api/dashboard/summary", headers={"Authorization": "Bearer id-token"})
    assert response.status_code == 200
    summary = response.json()

    assert summary["security"] == {"score": 80, "critical": 1, "high": 1, "total": 2}
    assert summary["governance"] == {"compliance": 96.5, "violations": 2, "affected_resources": 2}
    assert summary["performance"] == {"average_cpu": 34.25, "underutilized": 1, "overutilized": 2}


def test_dashboard_endpoint_rejects_user_without_connected_subscription(monkeypatch):
    session = build_session()
    session.add(ApplicationUser(entra_subject_id="subject-a", tenant_id="tenant-a", is_active=True))
    session.commit()
    monkeypatch.setattr(dashboard, "SessionLocal", lambda: session)
    monkeypatch.setattr(dashboard, "validate_id_token", lambda _token: {"sub": "subject-a", "tid": "tenant-a"})

    with pytest.raises(HTTPException) as error:
        dashboard.dashboard_summary(HTTPAuthorizationCredentials(scheme="Bearer", credentials="id-token"))

    assert error.value.status_code == 403


def test_learning_service_reports_the_number_of_persisted_recommendations():
    session = build_session()
    session.add(
        RecommendationMemory(
            recommendation_id="existing",
            resource_id=RESOURCE_ID,
            resource_name="vm-a",
            action="resize_vm",
            category="FinOps",
            estimated_savings=5.0,
            confidence=0.4,
            approved=False,
        )
    )
    session.commit()

    recommendations = [
        Recommendation(
            title="resize-vm-a",
            source_issue_id="issue-a",
            resource_id=RESOURCE_ID,
            resource_name="vm-a",
            action="resize_vm",
            issue_type="VM_RIGHTSIZING",
            current_cost=100.0,
            projected_cost=75.0,
            estimated_savings=25.0,
            currency="USD",
            cost_source="retail",
            cost_type="estimated",
            is_estimated=True,
            observed_cpu_average_percent=8.0,
            confidence=0.9,
            execution_plan=["Verify SKU constraints"],
            explanation="Low CPU indicates rightsizing.",
        ),
        Recommendation(
            title="resize-vm-b",
            source_issue_id="issue-b",
            resource_id="/subscriptions/subscription-a/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-b",
            resource_name="vm-b",
            action="resize_vm",
            issue_type="VM_RIGHTSIZING",
            current_cost=80.0,
            projected_cost=60.0,
            estimated_savings=20.0,
            currency="USD",
            cost_source="retail",
            cost_type="estimated",
            is_estimated=True,
            observed_cpu_average_percent=12.0,
            confidence=0.8,
            execution_plan=["Check compatibility"],
            explanation="Low CPU indicates rightsizing.",
        ),
    ]

    persisted = LearningService().save_recommendations(recommendations, db=session)

    assert persisted == 2
    assert session.query(RecommendationMemory).count() == 2
