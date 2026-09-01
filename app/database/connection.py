from sqlalchemy import create_engine

from sqlalchemy.orm import sessionmaker

from config.settings import settings



engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    # Recover stale PostgreSQL connections instead of surfacing intermittent
    # pool/connection OperationalError responses to read-only endpoints.
    pool_pre_ping=True,
    pool_recycle=1800,
)



SessionLocal=sessionmaker(

    bind=engine,

    autoflush=False,

    autocommit=False

)