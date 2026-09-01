from abc import ABC, abstractmethod

from app.models.execution import (
    ExecutionRequest,
    ExecutionResult,
    ExecutionStatus
)

class BaseExecutor(ABC):

    """
    Abstract execution engine.

    Every Azure executor must implement this.
    """



    def __init__(self, dry_run: bool = True):

        self.dry_run = dry_run



    @abstractmethod
    async def execute(
        self,
        request: ExecutionRequest
    ) -> ExecutionResult:

        pass



    async def validate(
        self,
        request: ExecutionRequest
    ):

        """
        Common validation before execution.
        """

        if not request.resource_id:

            raise ValueError(
                "Resource ID is required"
            )



    def dry_run_result(
        self,
        request: ExecutionRequest
    ):

        return ExecutionResult(

            action=request.action,

            resource_id=request.resource_id,

            status=ExecutionStatus.DRY_RUN,

            message=
            (
                "Dry run completed. "
                "No Azure resource modified."
            ),

            dry_run=True,

            baseline_monthly_cost=request.baseline_monthly_cost,

            expected_savings=request.estimated_savings,

            new_state=request.expected_state,

            previous_state=request.before_state or None,
        )
