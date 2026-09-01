from dataclasses import dataclass


@dataclass(frozen=True)
class SavingsEstimate:
    """A potential saving, not a guaranteed achievable resize saving."""

    percentage: float
    monthly_savings: float
    confidence: float
    method: str


class SavingsCalculator:
    def estimate_potential(
        self,
        monthly_cost: float,
        cpu_average_percent: float | None,
    ) -> SavingsEstimate:
        monthly_cost = float(monthly_cost or 0)
        if monthly_cost <= 0:
            return SavingsEstimate(0.0, 0.0, 0.0, "no_cost")
        if cpu_average_percent is None:
            return SavingsEstimate(0.0, 0.0, 0.0, "missing_cpu_evidence")

        utilization = float(cpu_average_percent)
        if utilization < 5:
            percentage, confidence = 0.70, 0.60
        elif utilization < 15:
            percentage, confidence = 0.50, 0.55
        elif utilization < 30:
            percentage, confidence = 0.30, 0.45
        else:
            percentage, confidence = 0.0, 0.20

        return SavingsEstimate(
            percentage=percentage,
            monthly_savings=round(monthly_cost * percentage, 2),
            confidence=confidence,
            method="heuristic_rightsizing",
        )

    def estimate_rightsize_savings(
        self,
        monthly_cost: float,
        utilization: float,
    ) -> dict:
        """Compatibility API for existing analyzers."""
        estimate = self.estimate_potential(monthly_cost, utilization)
        return {
            "current_cost": round(float(monthly_cost or 0), 2),
            "utilization": utilization,
            "estimated_savings": estimate.monthly_savings,
            "savings_percentage": estimate.percentage,
            "confidence": estimate.confidence,
            "savings_method": estimate.method,
        }
