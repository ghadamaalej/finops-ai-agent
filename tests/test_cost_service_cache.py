from app.services.cost_service import CostService
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.models import Base
from app.database.repositories.cost_cache_repository import CostCacheRepository


class FakeCollector:

    def __init__(self):

        self.calls = 0


    def collect(
        self,
        resources,
    ):

        self.calls += 1

        print(
            "!!! AZURE WAS CALLED !!!"
        )

        return [

            {
                "resource_id":
                    "/test/vm-1",

                "resource_name":
                    "vm-1",

                "service_name":
                    "Virtual Machines",

                "monthly_cost":
                    100.0,

                "currency":
                    "USD",

                "cost_source": "Azure Retail Prices",
                "cost_type": "estimated",
                "is_estimated": True,

                "cost_last_30_days":
                    100.0
            }

        ]


def test_cache_prevents_azure_call():

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()


    collector = FakeCollector()

    repository = CostCacheRepository()


    service = CostService(
        collector,
        repository
    )


    print("\n========== FIRST CALL ==========")


    costs1 = service.get_costs(
        db,
        "test-subscription",
        resources=[],
    )


    print(
        "Returned:",
        costs1
    )


    assert collector.calls == 1


    print("\n========== SECOND CALL ==========")


    costs2 = service.get_costs(
        db,
        "test-subscription",
        resources=[],
    )


    print(
        "Returned:",
        costs2
    )

    assert collector.calls == 1


    db.close()
