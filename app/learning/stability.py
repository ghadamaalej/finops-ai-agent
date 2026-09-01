from statistics import stdev


class ResourceStability:

    def calculate(self, history):

        if len(history) < 2:
            return 0.5


        costs = [
            float(x.monthly_cost)
            for x in history
        ]


        average = sum(costs) / len(costs)


        if average <= 0:
            return 0.5


        deviation = stdev(costs)


        coefficient_variation = (
            deviation / average
        )


        stability = (
            1 - coefficient_variation
        )


        return round(

            max(
                0.0,
                min(
                    stability,
                    1.0
                )
            ),

            2

        )