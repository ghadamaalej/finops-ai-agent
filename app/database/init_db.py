from sqlalchemy import inspect, text

from app.database.connection import engine
from app.database.models import Base


def upgrade_cost_schema():
    """Apply the additive cost-schema changes for databases created pre-migration.

    This project does not yet use Alembic, so `create_all` alone cannot add
    columns to an existing PostgreSQL database.
    """
    required_columns = {
        "cost_cache": {
            "daily_cost": "FLOAT",
            "cost_source": "VARCHAR",
            "cost_type": "VARCHAR",
            "is_estimated": "BOOLEAN",
            "cost_status": "VARCHAR",
        },
        "cost_history": {
            "subscription_id": "VARCHAR",
            "cost_source": "VARCHAR",
            "cost_type": "VARCHAR",
            "is_estimated": "BOOLEAN",
            "cost_status": "VARCHAR",
            # Older deployments used `collection_date`; the ORM and dashboard
            # use this explicit snapshot timestamp.
            "collected_at": "TIMESTAMP",
        },
        "cost_records": {
            "subscription_id": "VARCHAR",
            "resource_id": "VARCHAR",
            "resource_name": "VARCHAR",
            "service_name": "VARCHAR",
            "daily_cost": "FLOAT",
            "monthly_cost": "FLOAT",
            "currency": "VARCHAR",
            "cost_source": "VARCHAR",
            "cost_type": "VARCHAR",
            "is_estimated": "BOOLEAN",
            "cost_status": "VARCHAR",
            "collected_at": "TIMESTAMP",
        },
    }
    inspector = inspect(engine)
    with engine.begin() as connection:
        for table_name, columns in required_columns.items():
            existing = {column["name"] for column in inspector.get_columns(table_name)}
            for column_name, column_type in columns.items():
                if column_name not in existing:
                    connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"))

        # Provenance/status was added after the original tables were deployed.
        # Backfill only metadata from existing cost fields; never alter costs.
        for table_name in ("cost_cache", "cost_history", "cost_records"):
            connection.execute(text(
                f"UPDATE {table_name} SET cost_status = CASE "
                "WHEN monthly_cost IS NOT NULL AND is_estimated IS TRUE THEN 'estimated' "
                "WHEN monthly_cost IS NOT NULL THEN 'available' ELSE 'unavailable' END "
                "WHERE cost_status IS NULL"
            ))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_cost_history_subscription_id ON cost_history (subscription_id)"))
        connection.execute(text("CREATE INDEX IF NOT EXISTS ix_cost_records_subscription_id ON cost_records (subscription_id)"))


def init_database():

    Base.metadata.create_all(
        bind=engine
    )
    upgrade_cost_schema()


if __name__ == "__main__":

    init_database()

    print(
        "Database initialized"
    )
