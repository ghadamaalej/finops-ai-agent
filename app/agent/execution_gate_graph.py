"""Mockable LangGraph harness for the Phase 5.7 execution safety gate.

It uses the production validation, approval, execution and verification nodes.
The observe/analyze/recommend inputs are injected so integration tests cannot
accidentally contact Azure or an LLM.
"""

from langgraph.graph import END, StateGraph

from app.agent.nodes.approval import approval
from app.agent.nodes.execution import execute
from app.agent.nodes.validator import validate
from app.agent.nodes.verification import verify
from app.agent.state import AgentState


def create_execution_gate_graph(observe, analyze, recommend):
    workflow = StateGraph(AgentState)
    workflow.add_node("observe", observe)
    workflow.add_node("analyze", analyze)
    workflow.add_node("recommend", recommend)
    workflow.add_node("validate", validate)
    workflow.add_node("approval", approval)
    workflow.add_node("execution", execute)
    workflow.add_node("verification", verify)
    workflow.set_entry_point("observe")
    workflow.add_edge("observe", "analyze")
    workflow.add_edge("analyze", "recommend")
    workflow.add_edge("recommend", "validate")
    workflow.add_edge("validate", "approval")
    workflow.add_edge("approval", "execution")
    workflow.add_edge("execution", "verification")
    workflow.add_edge("verification", END)
    return workflow.compile()
