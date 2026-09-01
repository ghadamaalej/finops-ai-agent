from datetime import datetime

from app.database.models import CostRecord


class CostRecordRepository:
    """Persists the most recent analyzer-ready costs per subscription."""

    def replace_records(self, db, subscription_id: str, costs: list[dict], *, collected_at: datetime, commit: bool = True):
        db.query(CostRecord).filter(CostRecord.subscription_id == subscription_id).delete(synchronize_session=False)
        records = [
            CostRecord(
                subscription_id=subscription_id,
                resource_id=cost["resource_id"],
                resource_name=cost.get("resource_name"),
                service_name=cost.get("service_name"),
                daily_cost=cost.get("daily_cost"),
                monthly_cost=cost.get("monthly_cost"),
                currency=cost.get("currency"),
                cost_source=cost.get("cost_source"),
                cost_type=cost.get("cost_type"),
                is_estimated=cost.get("is_estimated"),
                cost_status=cost.get("cost_status"),
                collected_at=collected_at,
            )
            for cost in costs
        ]
        if records:
            db.add_all(records)
        if commit:
            db.commit()
        return records
