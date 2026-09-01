from datetime import datetime, timedelta
import logging
from sqlalchemy import inspect, text
from app.database.models import CostCache
logger = logging.getLogger(__name__)


def _ensure_cost_cache_schema(db):
    """Apply additive columns required by the ORM to legacy deployments."""
    required = {
        "daily_cost": "FLOAT",
        "cost_source": "VARCHAR",
        "cost_type": "VARCHAR",
        "is_estimated": "BOOLEAN",
        "cost_status": "VARCHAR",
    }
    bind = db.get_bind()
    existing = {column["name"] for column in inspect(bind).get_columns("cost_cache")}
    missing = [name for name in required if name not in existing]
    if missing:
        logger.warning("cost_cache schema repair: missing_columns=%s", missing)
        for name in missing:
            db.execute(text(f"ALTER TABLE cost_cache ADD COLUMN {name} {required[name]}"))
        db.commit()


class CostCacheRepository:

    def get_valid_cache(
        self,
        db,
        subscription_id: str,
        hours: int = 12,
    ):
        _ensure_cost_cache_schema(db)
        limit = (
            datetime.utcnow()
            - timedelta(hours=hours)
        )

        records = (
            db.query(CostCache)
            .filter(
                CostCache.subscription_id == subscription_id
            )
            .filter(
                CostCache.collected_at >= limit
            )
            .order_by(
                CostCache.collected_at.desc()
            )
            .all()
        )

        # A cache entry without provenance predates the canonical retail
        # mapping (or came from a non-conforming collector).  It is not a
        # valid cache hit: refresh it rather than returning misleading data.
        if any(
            item.cost_source is None
            or item.cost_type is None
            or item.is_estimated is None
            for item in records
        ):
            return []
        return records

    def save_cache(
        self,
        db,
        subscription_id: str,
        costs: list[dict],
        *,
        commit: bool = True,
    ):
        expiration = (
            datetime.utcnow()
            - timedelta(hours=24)
        )

        # Remove expired cache
        (
            db.query(CostCache)
            .filter(
                CostCache.collected_at < expiration
            )
            .delete(
                synchronize_session=False
            )
        )

        # Replace current subscription cache
        (
            db.query(CostCache)
            .filter(
                CostCache.subscription_id == subscription_id
            )
            .delete(
                synchronize_session=False
            )
        )

        records = []

        for cost in costs:
            monthly_cost = cost.get("monthly_cost")
            is_estimated = cost.get("is_estimated")
            records.append(
                CostCache(
                    subscription_id=subscription_id,
                    resource_id=cost["resource_id"],
                    resource_name=cost.get("resource_name"),
                    service_name=cost.get("service_name"),
                    daily_cost=cost.get("daily_cost"),
                    monthly_cost=monthly_cost,
                    currency=cost.get("currency"),
                    cost_source=cost.get("cost_source"),
                    cost_type=cost.get("cost_type"),
                    is_estimated=is_estimated,
                    cost_status=cost.get("cost_status") or (
                        "estimated" if is_estimated else
                        "available" if monthly_cost is not None else
                        "unavailable"
                    ),
                )
            )

        if records:
            db.add_all(records)

        if commit:
            db.commit()

        return records
