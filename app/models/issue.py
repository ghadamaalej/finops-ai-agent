from pydantic import BaseModel
from typing import Dict, Any
from typing import Optional

class Issue(BaseModel):

    id: str

    category: str

    issue_type: str

    severity: str

    confidence: float

    resource_id: str

    resource_name: str

    resource_type: str

    description: str

    evidence: dict

    current_monthly_cost: float = 0.0

    estimated_monthly_savings: float = 0.0

    business_impact: str = ""

    risk_score: float = 0.0

    detected_by: str = "analyzer"

    # Cost provenance
    cost_source: Optional[str] = None

    cost_type: Optional[str] = None

    is_estimated: bool = False

    currency: Optional[str] = None

    cost_data_available: bool = False

    hourly_price: Optional[float] = None

    estimated_hours: Optional[float] = None