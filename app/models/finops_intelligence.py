from typing import Any, Dict, List

from pydantic import BaseModel, Field

from app.models.azure import ResourceCost


class CostInsight(BaseModel):

    total_cost: float = 0.0

    monthly_forecast: float = 0.0

    estimated_cost: float = 0.0

    actual_cost: float = 0.0

    estimated_monthly_cost: float = 0.0

    actual_monthly_cost: float = 0.0

    estimated_cost_count: int = 0

    actual_cost_count: int = 0

    estimated_resource_count: int = 0

    actual_resource_count: int = 0

    top_cost_drivers: Dict[
        str,
        float
    ] = Field(
        default_factory=dict
    )

    cost_trend: str = "stable"


class PerformanceInsight(BaseModel):

    high_cpu_resources: List[str] = Field(
        default_factory=list
    )

    low_cpu_resources: List[str] = Field(
        default_factory=list
    )


class SecurityInsight(BaseModel):

    findings_by_severity: Dict[
        str,
        int
    ] = Field(
        default_factory=dict
    )

    high_risk_count: int = 0


class GovernanceInsight(BaseModel):

    compliance_score: float = 100.0

    policy_violations: List[str] = Field(
        default_factory=list
    )


class FinOpsIntelligenceContext(BaseModel):

    subscription_id: str

    resources: list = Field(
        default_factory=list
    )

    metrics: list = Field(
        default_factory=list
    )

    resource_costs: List[
        ResourceCost
    ] = Field(
        default_factory=list
    )

    security_findings: list = Field(
        default_factory=list
    )

    governance: Any = None


    cost: CostInsight = Field(
        default_factory=CostInsight
    )

    performance: PerformanceInsight = Field(
        default_factory=PerformanceInsight
    )

    security: SecurityInsight = Field(
        default_factory=SecurityInsight
    )

    governance_summary: GovernanceInsight = Field(
        default_factory=GovernanceInsight
    )

    environment_health_score: float = 100.0

    key_observations: List[str] = Field(
        default_factory=list
    )