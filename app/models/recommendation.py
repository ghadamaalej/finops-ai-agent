from typing import List, Optional

from pydantic import BaseModel, Field


class Recommendation(BaseModel):

    title: str

    source_issue_id: str

    resource_id: str
    
    resource_name: str

    action: str

    # Execution contract.  A target SKU remains optional until the deterministic
    # rightsizing engine has selected a compatible, priced candidate.
    issue_type: Optional[str] = None
    action_type: Optional[str] = None
    current_state: dict = Field(default_factory=dict)
    recommended_state: dict = Field(default_factory=dict)
    potential_savings: Optional[float] = None

    current_cost: float = 0.0

    projected_cost: float = 0.0

    estimated_savings: float = 0.0

    currency: Optional[str] = None

    # Cost provenance
    cost_source: Optional[str] = None

    cost_type: Optional[str] = None

    is_estimated: bool = False

    # These are copied from analyzer evidence, never inferred by the LLM.
    observed_cpu_average_percent: Optional[float] = None
    observed_cpu_max_percent: Optional[float] = None
    savings_method: Optional[str] = None

    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0
    )

    priority: str = "Low"

    roi: str = ""

    implementation_risk: str = "Low"

    requires_approval: bool = True

    execution_plan: List[str] = Field(
        default_factory=list
    )

    explanation: str = ""
