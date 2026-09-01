from app.services.memory_service import MemoryService


memory = MemoryService()


def retrieve_memory(state):

    context = []

    issues = state.get("issues", [])

    for issue in issues:

        history = memory.find_by_resource(
            issue.resource_id
        )

        context.extend(history)

    return {
        **state,
        "memory_context": context
    }