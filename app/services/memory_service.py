from app.database.models import RecommendationMemory

from app.database.connection import SessionLocal



class MemoryService:


    def find_by_resource(
        self,
        resource_id:str
    ):


        db=SessionLocal()



        records=(

            db.query(
                RecommendationMemory
            )

            .filter(
                RecommendationMemory.resource_id
                ==
                resource_id
            )

            .all()

        )



        result=[]



        for r in records:


            result.append({

                "resource_id":
                    r.resource_id,


                "action":
                    r.action,


                "approved":
                    r.approved,


                "feedback":
                    r.user_feedback,


                "savings":
                    r.estimated_savings

            })



        db.close()


        return result