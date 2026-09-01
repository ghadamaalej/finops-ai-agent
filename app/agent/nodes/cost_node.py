from app.agent.analyzers.cost_analyzer import CostAnalyzer


def cost_node(state):

    intelligence = state.get(
        "finops_context"
    )

    if intelligence is None:
        return {
            **state,
            "cost_issues": []
        }

    analyzer = CostAnalyzer()

    issues = analyzer.analyze(
        intelligence
    )

    return {
        **state,
        "cost_issues": issues
    }