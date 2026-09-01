from datetime import datetime


from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON
)


from app.database.connection import engine

from sqlalchemy.orm import declarative_base



Base = declarative_base()


class ApplicationUser(Base):
    """Application identity metadata; never stores Entra passwords or tokens."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    entra_subject_id = Column(String, unique=True, nullable=False, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    email = Column(String, nullable=True, index=True)
    display_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, default=datetime.utcnow, nullable=False)


class AzureConnection(Base):
    """Selected Azure subscription metadata, without delegated credentials."""
    __tablename__ = "azure_connections"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False, index=True)
    tenant_id = Column(String, nullable=False, index=True)
    subscription_id = Column(String, nullable=False, index=True)
    subscription_name = Column(String, nullable=True)
    connection_status = Column(String, default="CONNECTED", nullable=False)
    permissions_status = Column(String, default="UNVERIFIED", nullable=False)
    connected_at = Column(DateTime, default=datetime.utcnow, nullable=False)



class RecommendationMemory(Base):

    __tablename__="recommendations"



    id=Column(
        Integer,
        primary_key=True
    )


    recommendation_id=Column(
        String
    )


    resource_id=Column(
        String,
        index=True
    )


    resource_name=Column(
        String
    )


    action=Column(
        String
    )


    category=Column(
        String
    )


    estimated_savings=Column(
        Float
    )


    confidence=Column(
        Float
    )


    approved=Column(
        Boolean,
        default=False
    )


    user_feedback=Column(
        Text,
        nullable=True
    )


    created_at=Column(
        DateTime,
        default=datetime.utcnow
    )



class ExecutionMemory(Base):


    __tablename__="executions"



    id=Column(
        Integer,
        primary_key=True
    )


    recommendation_id=Column(
        String
    )


    resource_id=Column(
        String
    )


    action=Column(
        String
    )


    status=Column(
        String
    )


    result=Column(
        Text
    )


    realized_savings=Column(
        Float
    )


    executed_at=Column(
        DateTime,
        default=datetime.utcnow
    )



class LearningMemory(Base):


    __tablename__="learning"



    id=Column(
        Integer,
        primary_key=True
    )


    resource_id=Column(
        String
    )


    lesson=Column(
        Text
    )


    created_at=Column(
        DateTime,
        default=datetime.utcnow
    )


class OptimizationOutcomeMemory(Base):
    __tablename__ = "optimization_outcomes"

    id = Column(Integer, primary_key=True)
    outcome_id = Column(String, unique=True, nullable=False, index=True)
    execution_id = Column(String, unique=True, index=True)
    recommendation_id = Column(String, index=True)
    resource_id = Column(String, index=True, nullable=False)
    outcome = Column(JSON, nullable=False)
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)


class RecommendationFeedbackMemory(Base):
    __tablename__ = "recommendation_feedback"

    id = Column(Integer, primary_key=True)
    recommendation_id = Column(String, index=True)
    resource_id = Column(String, index=True)
    feedback = Column(JSON, nullable=False)
    decision = Column(String, nullable=False, default="DEFERRED")
    reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)


class LearningMetricMemory(Base):
    __tablename__ = "learning_metrics"

    id = Column(Integer, primary_key=True)
    metrics = Column(JSON, nullable=False)
    calculated_at = Column(DateTime, default=datetime.utcnow, index=True)

from datetime import datetime



class CostHistory(Base):
    __tablename__ = "cost_history"

    id = Column(Integer, primary_key=True)

    # Nullable during the transition so existing database rows remain valid.
    subscription_id = Column(String, index=True)
    resource_id = Column(String, index=True)
    resource_name = Column(String)
    service_name = Column(String)

    daily_cost = Column(Float)
    monthly_cost = Column(Float)

    currency = Column(String)
    cost_source = Column(String)
    cost_type = Column(String)
    is_estimated = Column(Boolean)
    cost_status = Column(String)

    collected_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )
from datetime import datetime


class CostRecord(Base):
    """Analyzer-ready record of the latest successful resource cost refresh."""
    __tablename__ = "cost_records"

    id = Column(Integer, primary_key=True)
    subscription_id = Column(String, index=True, nullable=False)
    resource_id = Column(String, index=True, nullable=False)
    resource_name = Column(String)
    service_name = Column(String)
    daily_cost = Column(Float)
    monthly_cost = Column(Float)
    currency = Column(String)
    cost_source = Column(String)
    cost_type = Column(String)
    is_estimated = Column(Boolean)
    cost_status = Column(String)
    collected_at = Column(DateTime, default=datetime.utcnow, index=True)


class CostCache(Base):

    __tablename__ = "cost_cache"

    id = Column(
        Integer,
        primary_key=True
    )

    subscription_id = Column(
        String,
        index=True,
        nullable=False
    )

    resource_id = Column(
        String,
        index=True,
        nullable=False
    )

    resource_name = Column(
        String
    )

    service_name = Column(
        String
    )

    daily_cost = Column(Float)

    monthly_cost = Column(
        Float
    )

    currency = Column(
        String
    )

    collected_at = Column(
        DateTime,
        default=datetime.utcnow,
        index=True
    )
    cost_source = Column(String)
    cost_type = Column(String)
    is_estimated = Column(Boolean)
    cost_status = Column(String)
