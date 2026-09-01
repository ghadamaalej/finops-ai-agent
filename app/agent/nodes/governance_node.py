from app.agent.analyzers.governance_analyzer import GovernanceAnalyzer

analyzer = GovernanceAnalyzer()

def governance_node(state):


    issues = analyzer.analyze(
        state["azure_context"]
    )


    return {

        **state,

        "governance_issues":issues

    }