class HistoricalSuccess:

    def calculate(self, executions):

        if not executions:
            return 0.5


        successful = 0


        for execution in executions:

            if isinstance(execution, dict):

                status = execution.get(
                    "status"
                )

            else:

                status = getattr(
                    execution,
                    "status",
                    None
                )


            if status == "SUCCESS":

                successful += 1


        return round(
            successful / len(executions),
            2
        )