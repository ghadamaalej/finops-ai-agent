import json
import logging

from app.models.execution import ExecutionResult


class ExecutionLogger:

    def __init__(self):

        self.logger = logging.getLogger(
            "finops_execution"
        )

        if not self.logger.handlers:

            handler = logging.FileHandler(
                "execution.log"
            )

            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)s | %(message)s"
            )

            handler.setFormatter(
                formatter
            )

            self.logger.addHandler(
                handler
            )

        self.logger.setLevel(
            logging.INFO
        )

    def log(self, result):

        if isinstance(
            result,
            ExecutionResult
        ):

            payload = result.model_dump(
                mode="json"
            )

        elif isinstance(
            result,
            dict
        ):

            payload = result

        else:

            payload = {
                "result": str(result)
            }

        self.logger.info(
            json.dumps(
                payload,
                default=str
            )
        )