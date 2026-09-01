from statistics import mean


class TrendAnalyzer:

    def analyze(self, history):

        if not history:
            return None

        costs = [h.monthly_cost for h in history]

        current = costs[-1]

        previous = costs[-2] if len(costs) > 1 else current

        growth = 0

        if previous > 0:
            growth = round(
                ((current - previous) / previous) * 100,
                2
            )

        average = round(mean(costs), 2)

        trend = "stable"

        if growth > 10:
            trend = "increasing"

        elif growth < -10:
            trend = "decreasing"

        return {

            "current_cost": current,

            "previous_cost": previous,

            "average_cost": average,

            "growth_percent": growth,

            "trend": trend

        }