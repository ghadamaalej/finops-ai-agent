from app.database.models import ExecutionMemory

from app.database.connection import SessionLocal



def save_execution(
    result
):

    db=SessionLocal()

    record=ExecutionMemory(

        recommendation_id=
            result["id"],


        resource_id=
            result["resource"],


        action=
            result["action"],


        status=
            result["status"],


        result=
            str(result),


        realized_savings=
            result.get(
                "savings",
                0
            )

    )


    db.add(record)

    db.commit()

    db.close()