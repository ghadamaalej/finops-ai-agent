from langgraph.graph import StateGraph, END

from app.agent.state import AgentState
from app.agent.nodes.observe import observe
from app.agent.nodes.cost_node import cost_node
from app.agent.nodes.performance_node import performance_node
from app.agent.nodes.security_node import security_node
from app.agent.nodes.governance_node import governance_node
from app.agent.nodes.merge import merge_issues
from app.agent.nodes.memory import retrieve_memory
from app.agent.nodes.reason import reason
from app.agent.nodes.validator import validate
from app.agent.nodes.approval import approval
from app.agent.nodes.execution import execute
from app.agent.nodes.verification import verify
from app.agent.nodes.intelligence import intelligence_node
from app.agent.nodes.recommendation_intelligence import (
    recommendation_intelligence_node
)
from app.agent.nodes.learning import learn




workflow=StateGraph(
    AgentState
)



workflow.add_node(
    "observe",
    observe
)


workflow.add_node(
    "cost",
    cost_node
)

workflow.add_node(
    "intelligence",
    intelligence_node
)

workflow.add_node(
    "performance",
    performance_node
)


workflow.add_node(
    "security",
    security_node
)


workflow.add_node(
    "governance",
    governance_node
)


workflow.add_node(
    "merge",
    merge_issues
)


workflow.add_node(
    "memory",
    retrieve_memory
)
workflow.add_node(
    "recommendation_intelligence",
    recommendation_intelligence_node
)


workflow.add_node(
    "reason",
    reason
)


workflow.add_node(
    "validate",
    validate
)


workflow.add_node(
    "approval",
    approval
)


workflow.add_node(
    "execution",
    execute
)


workflow.add_node(
    "verification",
    verify
)


workflow.add_node(
    "learning",
    learn
)


workflow.set_entry_point(
    "observe"
)



workflow.add_edge(
    "observe",
    "intelligence"
)


workflow.add_edge(
    "intelligence",
    "cost"
)

workflow.add_edge(
    "cost",
    "performance"
)


workflow.add_edge(
    "performance",
    "security"
)


workflow.add_edge(
    "security",
    "governance"
)


workflow.add_edge(
    "governance",
    "merge"
)


workflow.add_edge(
    "merge",
    "memory"
)


workflow.add_edge(
    "memory",
    "recommendation_intelligence"
)


workflow.add_edge(
    "recommendation_intelligence",
    "reason"
)

workflow.add_edge(
    "reason",
    "validate"
)


workflow.add_edge(
    "validate",
    "approval"
)


workflow.add_conditional_edges(

    "approval",

    lambda state:
        "execution"
        if len(
            state.get(
                "approved_recommendations",
                []
            )
        ) > 0
        else "learning",


    {

        "execution":
        "execution",

        "learning":
        "learning"

    }

)

workflow.add_edge(
    "execution",
    "verification"
)


workflow.add_edge(
    "verification",
    "learning"
)


workflow.add_edge(
    "learning",
    END
)

finops_agent = workflow.compile()
