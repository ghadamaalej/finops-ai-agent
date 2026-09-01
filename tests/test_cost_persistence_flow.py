from datetime import datetime

from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api import dashboard
from app.database.models import ApplicationUser, AzureConnection, Base, CostCache, CostHistory, CostRecord
from app.database.repositories.cost_cache_repository import CostCacheRepository
from app.database.repositories.cost_repository import CostRepository
from app.Collectors.retail_cost_collector import RetailCostCollector
from app.models.azure import ResourceCost
from app.services.cost_service import CostService
from app.services.azure_context_builder import AzureContextBuilder


class FakeRetailCollector:
    def __init__(self):
        self.resources_received = []

    def collect(self, resources):
        self.resources_received.append(resources)
        return [
            {
                "resource_id": "/subscriptions/sub-a/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-a",
                "resource_name": "vm-a",
                "service_name": "Virtual Machines",
                "monthly_cost": 88.33,
                "currency": "USD",
                "cost_source": "Azure Retail Prices",
                "cost_type": "estimated",
                "is_estimated": True,
            }
        ]


class FakeProductionResourceCollector:
    def __init__(self):
        self.subscription_ids = []

    def collect(self, subscription_id):
        self.subscription_ids.append(subscription_id)
        return [
            {
                "id": f"/subscriptions/{subscription_id}/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/production-vm",
                "name": "production-vm",
                "type": "Microsoft.Compute/virtualMachines",
                "location": "westeurope",
                "resource_group": "rg",
                "subscription_id": subscription_id,
            }
        ]


def test_retail_collector_canonical_mapping_sets_estimated_provenance():
    record = RetailCostCollector._with_retail_provenance({"resource_id": "resource-a", "monthly_cost": 1})

    assert record["cost_source"] == "Azure Retail Prices"
    assert record["cost_type"] == "estimated"
    assert record["is_estimated"] is True


def test_cost_refresh_persists_cache_history_and_provenance_then_reuses_cache():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    collector = FakeRetailCollector()
    service = CostService(collector, CostCacheRepository(), CostRepository())
    resources = [{"id": "resource-a", "type": "Microsoft.Compute/virtualMachines"}]

    collected = service.get_costs(session, subscription_id="sub-a", resources=resources)
    cached = service.get_costs(session, subscription_id="sub-a", resources=resources)

    assert collector.resources_received == [resources]
    assert ResourceCost(**collected[0]).monthly_cost == 88.33
    assert cached[0]["cost_source"] == "Azure Retail Prices"
    assert cached[0]["cost_type"] == "estimated"
    assert cached[0]["is_estimated"] is True

    cache_row = session.query(CostCache).one()
    history_row = session.query(CostHistory).one()
    record_row = session.query(CostRecord).one()
    assert cache_row.subscription_id == "sub-a"
    assert cache_row.daily_cost == round(88.33 / 30, 4)
    assert history_row.subscription_id == "sub-a"
    assert history_row.cost_source == "Azure Retail Prices"
    assert history_row.cost_type == "estimated"
    assert history_row.is_estimated is True
    assert record_row.monthly_cost == 88.33
    assert record_row.cost_source == "Azure Retail Prices"
    assert record_row.cost_type == "estimated"
    assert record_row.is_estimated is True
    assert cache_row.cost_source == "Azure Retail Prices"
    assert cache_row.cost_type == "estimated"
    assert cache_row.is_estimated is True


def test_provenance_incomplete_cache_is_refreshed_not_returned():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add(CostCache(subscription_id="sub-a", resource_id="resource-a", monthly_cost=1, currency="USD"))
    session.commit()
    collector = FakeRetailCollector()

    costs = CostService(collector, CostCacheRepository(), CostRepository()).get_costs(
        session, subscription_id="sub-a", resources=[{"id": "resource-a"}]
    )

    cache_row = session.query(CostCache).one()
    assert collector.resources_received == [[{"id": "resource-a"}]]
    assert costs[0]["cost_source"] == "Azure Retail Prices"
    assert cache_row.cost_source == "Azure Retail Prices"
    assert cache_row.cost_type == "estimated"
    assert cache_row.is_estimated is True


def test_history_snapshots_provide_previous_change_trend_and_forecast():
    from app.services.dashboard_summary import DashboardSummaryService

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    resource_id = "/subscriptions/sub-a/resourceGroups/rg/providers/Microsoft.Compute/virtualMachines/vm-a"
    session.add(
        CostCache(
            subscription_id="sub-a",
            resource_id=resource_id,
            resource_name="vm-a",
            service_name="Virtual Machines",
            monthly_cost=120,
            currency="USD",
            cost_source="Azure Retail Prices",
            cost_type="estimated",
            is_estimated=True,
        )
    )
    session.add_all(
        [
            CostHistory(subscription_id="sub-a", resource_id=resource_id, monthly_cost=100, currency="USD", collected_at=datetime(2026, 1, 1)),
            CostHistory(subscription_id="sub-a", resource_id=resource_id, monthly_cost=120, currency="USD", collected_at=datetime(2026, 2, 1)),
        ]
    )
    session.commit()

    summary = DashboardSummaryService().build(session, "sub-a")

    assert summary["cost"]["previous"] == 100
    assert summary["cost"]["change_percent"] == 20
    assert summary["cost"]["forecast"] == 140
    assert summary["cost"]["cost_source"] == "Azure Retail Prices"
    assert summary["cost"]["is_estimated"] is True
    assert len(summary["cost_overview"]["trend"]) == 2


def test_empty_database_collection_populates_all_cost_tables_and_dashboard(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    collector = FakeRetailCollector()
    service = CostService(collector, CostCacheRepository(), CostRepository())
    user = ApplicationUser(entra_subject_id="subject-a", tenant_id="tenant-a", is_active=True)
    session.add(user)
    session.flush()
    session.add(AzureConnection(user_id=user.id, tenant_id="tenant-a", subscription_id="sub-a", connection_status="CONNECTED"))
    session.commit()

    service.get_costs(session, "sub-a", [{"id": "resource-a"}])
    monkeypatch.setattr(dashboard, "SessionLocal", lambda: session)
    monkeypatch.setattr(dashboard, "validate_id_token", lambda _: {"sub": "subject-a", "tid": "tenant-a", "oid": "object-a"})
    monkeypatch.setattr(dashboard, "validate_azure_management_token", lambda _: {"oid": "object-a"})
    result = dashboard.dashboard_summary(HTTPAuthorizationCredentials(scheme="Bearer", credentials="test-id-token"))

    assert session.query(CostRecord).count() > 0
    assert session.query(CostCache).count() > 0
    assert session.query(CostHistory).count() > 0
    assert result["cost"]["monthly"] == 88.33
    assert result["cost"]["cost_source"] == "Azure Retail Prices"
    assert result["cost"]["cost_type"] == "estimated"
    assert result["cost"]["is_estimated"] is True
    assert result["cost_drivers"][0]["resource_name"] == "vm-a"


def test_dashboard_refresh_uses_authenticated_connected_production_subscription(monkeypatch):
    production_subscription_id = "6850d94e-3234-463d-aa51-615d3c486939"
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    user = ApplicationUser(entra_subject_id="subject-a", tenant_id="tenant-a", is_active=True)
    session.add(user)
    session.flush()
    session.add(AzureConnection(user_id=user.id, tenant_id="tenant-a", subscription_id=production_subscription_id, connection_status="CONNECTED"))
    session.commit()
    resources = FakeProductionResourceCollector()
    builder = AzureContextBuilder(
        resource_collector=resources,
        session_factory=lambda: session,
        cost_service=CostService(FakeRetailCollector(), CostCacheRepository(), CostRepository()),
    )
    monkeypatch.setattr(dashboard, "SessionLocal", lambda: session)
    monkeypatch.setattr(dashboard, "validate_id_token", lambda _: {"sub": "subject-a", "tid": "tenant-a", "oid": "object-a"})
    monkeypatch.setattr(dashboard, "validate_azure_management_token", lambda _: {"oid": "object-a"})
    monkeypatch.setattr(dashboard, "create_cost_refresh_builder", lambda: builder)

    result = dashboard.refresh_dashboard_costs(dashboard.DashboardRefreshRequest(azure_access_token="a" * 20), HTTPAuthorizationCredentials(scheme="Bearer", credentials="test-id-token"))
    summary = dashboard.dashboard_summary(HTTPAuthorizationCredentials(scheme="Bearer", credentials="test-id-token"))

    assert resources.subscription_ids == [production_subscription_id]
    assert result["subscription_id"] == production_subscription_id
    assert result["resources_collected"] == 1
    assert result["cost_records_collected"] == 1
    assert result["cost_records_persisted"] == 1
    assert result["cache_rows_persisted"] == 1
    assert result["history_rows_persisted"] == 1
    assert result["cost_source"] == "Azure Retail Prices"
    assert result["cost_type"] == "estimated"
    assert result["is_estimated"] is True
    assert {row.subscription_id for row in session.query(CostRecord).all()} == {production_subscription_id}
    assert {row.subscription_id for row in session.query(CostCache).all()} == {production_subscription_id}
    assert {row.subscription_id for row in session.query(CostHistory).all()} == {production_subscription_id}
    assert summary["cost"]["monthly"] == 88.33
