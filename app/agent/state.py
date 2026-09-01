# app/agent/state.py

from typing import TypedDict, Any


class AgentState(TypedDict, total=False):

    user_request: str
    subscription_id: str

    azure_context: Any
    finops_context: Any
    observed: dict

    # Analyzer outputs
    cost_issues: list
    performance_issues: list
    security_issues: list
    governance_issues: list

    # Merged issues
    issues: list

    # Recommendation system
    recommendations: list
    validated_recommendations: list
    validation_errors: list

    # Approval
    approved_recommendations: list
    pending_approval: list
    approved_recommendation_ids: list
    recommendation_decisions: dict

    # Execution
    execution_results: list
    execution_router: Any
    dry_run: bool

    # Verification
    verification_results: list
    verification_router: Any
    verification_report: dict

    # Learning
    learning: dict
    recommendation_intelligence: dict

    # Memory
    memory_context: list
    cost_history: list
    execution_history: list
    verification_history: list
    optimization_outcomes: list
    outcome_repository: Any

    # Diagnostics
    logs: list
    reasoning: str
    recommendation_error: str
