import os
from openai import AzureOpenAI

client = AzureOpenAI(
    api_version="2024-12-01-preview",
    azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
    api_key=os.environ["AZURE_OPENAI_API_KEY"],
)

response = client.chat.completions.create(
    model=os.environ["AZURE_OPENAI_DEPLOYMENT"],
    messages=[
        {
            "role": "system",
            "content": "You are a FinOps assistant."
        },
        {
            "role": "user",
            "content": "Explain why an Azure VM with very low CPU utilization may be a cost optimization opportunity."
        }
    ],
    max_completion_tokens=1000,
)

print(response.choices[0].message.content)