from app.agent.analyzers.performance_analyzer import PerformanceAnalyzer

analyzer = PerformanceAnalyzer()

def performance_node(state):

    issues = analyzer.analyze(
        state["finops_context"]
    )

    return {
        **state,
        "performance_issues": issues
    }