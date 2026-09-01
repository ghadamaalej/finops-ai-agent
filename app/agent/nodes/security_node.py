from app.agent.analyzers.security_analyzer import SecurityAnalyzer
analyzer = SecurityAnalyzer()

def security_node(state):


    issues = analyzer.analyze(
        state["azure_context"]
    )


    return {

        **state,

        "security_issues":issues

    }