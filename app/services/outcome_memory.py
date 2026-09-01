"""PostgreSQL persistence for Phase 6 outcomes; no learning decisions occur here."""

from app.database.connection import SessionLocal
from app.database.models import (
    LearningMetricMemory,
    OptimizationOutcomeMemory,
    RecommendationFeedbackMemory,
)


class OutcomeMemoryRepository:
    def __init__(self, session_factory=SessionLocal):
        self.session_factory = session_factory

    def save(self, outcomes, feedback, metrics):
        session = self.session_factory()
        try:
            for outcome in outcomes:
                # Reprocessing an execution must not create a second outcome.
                if outcome.execution_id and session.query(OptimizationOutcomeMemory).filter_by(execution_id=outcome.execution_id).first():
                    continue
                payload = outcome.model_dump(mode="json")
                session.add(OptimizationOutcomeMemory(
                    outcome_id=outcome.outcome_id,
                    execution_id=outcome.execution_id,
                    recommendation_id=outcome.recommendation_id,
                    resource_id=outcome.resource_id,
                    outcome=payload,
                ))
            for item in feedback:
                session.add(RecommendationFeedbackMemory(
                    recommendation_id=item.get("recommendation_id"),
                    resource_id=item.get("resource_id"),
                    feedback=item,
                    decision=item.get("decision", "DEFERRED"),
                    reason=item.get("reason"),
                ))
            session.add(LearningMetricMemory(metrics=metrics))
            session.commit()
            return {"status": "PERSISTED", "outcome_count": len(outcomes)}
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
