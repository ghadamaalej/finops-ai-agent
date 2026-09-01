from app.services.execution.execution_router import ExecutionRouter
from app.services.execution.execution_logger import ExecutionLogger


execution_logger = ExecutionLogger()


from app.services.execution.execution_logger import ExecutionLogger
from app.services.execution.recommendation_to_request import (
    recommendation_to_execution_request
)


execution_logger = ExecutionLogger()


async def execute(state):

    results = []

    router = state["execution_router"]

    recommendations = state.get(
        "approved_recommendations",
        []
    )

    for recommendation in recommendations:

        try:

            request = (
                recommendation_to_execution_request(
                    recommendation,
                    dry_run=state.get("dry_run", True),
                )
            )

            result = await router.execute(
                request
            )

            results.append(
                result
            )

            execution_logger.log(
                result
            )

        except Exception as e:

            error_result = {
                "status": "failed",
                "resource_id":
                    getattr(
                        recommendation,
                        "resource_id",
                        None
                    ),
                "error": str(e)
            }

            results.append(
                error_result
            )

            execution_logger.log(
                error_result
            )

    return {
        **state,
        "execution_results": results
    }
