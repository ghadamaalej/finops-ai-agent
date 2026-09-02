from app.services.llm_service import ask_llm

response = ask_llm(
    """
    Return a JSON object with exactly these fields:
    {
      "provider": "Azure OpenAI",
      "model": "gpt-5.6-luna",
      "status": "success"
    }
    """,
    request_id="azure-openai-test",
)

print("\nFINAL RESPONSE:")
print(response)