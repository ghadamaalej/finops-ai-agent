from app.database.connection import SessionLocal
from app.database.models import RecommendationMemory

def _recommendation_id(recommendation):
    # Identify the same action independently for every Azure resource.
    action = str(recommendation.action or recommendation.title or "recommendation").strip().lower()
    resource = str(recommendation.resource_name or recommendation.resource_id or "resource").strip().lower()
    action = "".join(character if character.isalnum() or character in "-_" else "_" for character in action)
    resource = "".join(character if character.isalnum() or character in "-_" else "_" for character in resource)
    return f"{action}:{resource}"



class LearningService:


    def save_recommendations(
        self,
        recommendations,
        db=None,
    ):


        owns_session = db is None
        db = db or SessionLocal()

        saved = 0
        seen = set()

        for rec in recommendations:
            key = (str(rec.resource_id).lower(), str(rec.action).lower())
            if key in seen:
                continue
            seen.add(key)

            recommendation_id = _recommendation_id(rec)
            memory=RecommendationMemory(

                recommendation_id=recommendation_id,


                resource_id=
                    rec.resource_id,


                resource_name=
                    rec.resource_name,


                action=
                    rec.action,


                category=
                    "FinOps",


                estimated_savings=
                    rec.estimated_savings,


                confidence=
                    rec.confidence,


                approved=False

            )


            existing = db.query(RecommendationMemory).filter_by(
                resource_id=rec.resource_id,
                action=rec.action,
                approved=False,
            ).first()
            if existing:
                existing.estimated_savings = rec.estimated_savings
                existing.confidence = rec.confidence
                existing.resource_name = rec.resource_name
                existing.recommendation_id = recommendation_id
                saved += 1
            else:
                db.add(memory)
                saved += 1



        db.commit()

        if owns_session:
            db.close()

        return saved
