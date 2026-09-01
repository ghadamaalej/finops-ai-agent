from datetime import datetime

from app.database.repositories.cost_repository import CostRepository
from app.database.repositories.cost_record_repository import CostRecordRepository


class CostService:

    def __init__(
        self,
        collector,
        cache_repository,
        history_repository=None,
        record_repository=None,
    ):
        self.collector = collector
        self.cache_repository = cache_repository
        self.history_repository = history_repository or CostRepository()
        self.record_repository = record_repository or CostRecordRepository()

    def get_costs(
        self,
        db,
        subscription_id: str,
        resources: list[dict],
        force_refresh: bool = False,
    ):
        cached = self.cache_repository.get_valid_cache(
            db,
            subscription_id=subscription_id,
            hours=12,
        )

        if cached and not force_refresh:
            print("Using cached Azure costs.")

            return [
                {
                    "resource_id": item.resource_id,
                    "resource_name": item.resource_name,
                    "service_name": item.service_name,
                    "daily_cost": item.daily_cost,
                    "monthly_cost": item.monthly_cost,
                    "currency": item.currency,
                    "cost_last_30_days": item.monthly_cost,
                    "cost_source": item.cost_source,
                    "cost_type": item.cost_type,
                    "is_estimated": item.is_estimated,
                    "cost_status": item.cost_status or ("estimated" if item.is_estimated else "available" if item.monthly_cost is not None else "unavailable"),
                    "cost_data_available": item.monthly_cost is not None,
                }
                for item in cached
            ]

        print(
            "Cache expired or unavailable. "
            "Calculating estimated Azure retail costs..."
        )

        costs = [
            {
                **cost,
                "cost_status": cost.get("cost_status") or ("estimated" if cost.get("is_estimated") else "available" if cost.get("monthly_cost") is not None else "unavailable"),
                "cost_source": cost.get("cost_source") or "none",
            }
            for cost in self.collector.collect(resources)
        ]
        missing_provenance = [
            cost.get("resource_id", "unknown")
            for cost in costs
            if not cost.get("cost_status")
        ]
        if missing_provenance:
            raise ValueError(
                "Collector returned cost records without provenance: "
                + ", ".join(missing_provenance)
            )
        # Retail collection is monthly priced.  Persist an explicit daily
        # equivalent so every persisted record has both requested periods.
        costs = [
            {
                **cost,
                "daily_cost": cost.get("daily_cost") if cost.get("monthly_cost") is None else cost.get("daily_cost", round(float(cost["monthly_cost"]) / 30, 4)),
            }
            for cost in costs
        ]

        if costs:
            collected_at = datetime.utcnow()
            try:
                self.cache_repository.save_cache(
                    db,
                    subscription_id=subscription_id,
                    costs=costs,
                    commit=False,
                )
                self.history_repository.save_costs(
                    db,
                    subscription_id=subscription_id,
                    costs=costs,
                    collected_at=collected_at,
                    commit=False,
                )
                self.record_repository.replace_records(
                    db,
                    subscription_id=subscription_id,
                    costs=costs,
                    collected_at=collected_at,
                    commit=False,
                )
                db.commit()
            except Exception:
                db.rollback()
                raise

        return costs
