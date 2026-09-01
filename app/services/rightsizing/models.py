from dataclasses import dataclass


@dataclass
class SkuCandidate:

    sku: str

    hourly_price: float

    monthly_cost: float

    cpu_compatible: bool

    memory_compatible: bool

    savings: float

    savings_percent: float