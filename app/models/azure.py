# app/models/azure.py

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AzureResource(BaseModel):
    id: str
    name: str
    type: str
    location: str
    resource_group: str
    subscription_id: str

    sku: Optional[str] = None
    power_state: Optional[str] = None
    configuration: Dict[str, Any] = Field(default_factory=dict)

    tags: Dict[str, Any] = Field(
        default_factory=dict
    )


class ResourceCost(BaseModel):

    resource_id: str
    product_name: str | None = None
    resource_name: str | None = None
    resource_type: str | None = None

    service_name: str | None = None
    service_family: str | None = None

    monthly_cost: float = 0.0
    cost_last_30_days: float = 0.0

    currency: str = "USD"

    arm_sku_name: Optional[str] = None

    cost_source: str | None = None
    cost_type: str | None = None
    is_estimated: bool = False
    cost_data_available: bool = False
    cost_status: str = "unavailable"

    pricing_method: str | None = None
    pricing_unit: str | None = None

    meter_name: str | None = None

    hourly_price: float | None = None
    price_per_gb_month: float | None = None

    estimated_hours: float | None = None
    estimated_quantity: float | None = None

    sku: str | None = None
    region: str | None = None

    pricing_validated: bool = False
    pricing_selection: str | None = None
    pricing_warning: str | None = None
    requested_arm_sku: str | None = None
    os_type: str | None = None
    rejected_candidate_count: int = 0

    disk_size_gb: int | None = None
    disk_tier: str | None = None
    pricing_sku: str | None = None
    storage_sku: str | None = None


class PerformanceMetric(BaseModel):
    resource_id: str
    resource_type: Optional[str] = None
    metric_available: bool = False
    metric_names: List[str] = Field(default_factory=list)
    values: Dict[str, Optional[float]] = Field(default_factory=dict)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    metric_errors: Dict[str, Any] = Field(default_factory=dict)
    configuration: Dict[str, Any] = Field(default_factory=dict)
    collected_at: Optional[datetime] = None
    cpu_average: Optional[float] = None
    cpu_max: Optional[float] = None

    memory_average: Optional[float] = None
    memory_max: Optional[float] = None

    network_in: Optional[float] = None
    network_out: Optional[float] = None

    disk_read_iops: Optional[float] = None
    disk_write_iops: Optional[float] = None

    availability: Optional[float] = None

    collected_days: int = 0
    utilization_status: str = "unavailable"
    utilization_reason: str | None = None
    metric_unavailable_reason: str | None = None


class SecurityFinding(BaseModel):
    resource_id: str
    severity: str
    recommendation: str
    description: str
    category: str

    source: Optional[str] = None


class GovernanceState(BaseModel):
    compliance_score: float = 100.0

    policy_violations: List[str] = Field(
        default_factory=list
    )


class AzureContext(BaseModel):
    subscription_id: str

    collected_at: datetime

    resources: List[AzureResource] = Field(
        default_factory=list
    )

    resource_costs: List[ResourceCost] = Field(
        default_factory=list
    )

    metrics: List[PerformanceMetric] = Field(
        default_factory=list
    )

    security_findings: List[SecurityFinding] = Field(
        default_factory=list
    )

    governance: Optional[GovernanceState] = None

    advisor_recommendations: List[Any] = Field(
        default_factory=list
    )

    budgets: List[Any] = Field(
        default_factory=list
    )

    reservations: List[Any] = Field(
        default_factory=list
    )

    activity_logs: List[Any] = Field(
        default_factory=list
    )