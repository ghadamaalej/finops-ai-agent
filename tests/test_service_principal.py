# test_service_principal.py
import os
from azure.identity import ClientSecretCredential
from dotenv import load_dotenv

load_dotenv()

tenant_id = os.getenv("AZURE_TENANT_ID")
client_id = os.getenv("AZURE_CLIENT_ID")
client_secret = os.getenv("AZURE_CLIENT_SECRET")

print(f"Tenant ID: {tenant_id}")
print(f"Client ID: {client_id}")
print(f"Client Secret: {'SET' if client_secret else 'NOT SET'}")

try:
    credential = ClientSecretCredential(
        tenant_id=tenant_id,
        client_id=client_id,
        client_secret=client_secret
    )
    token = credential.get_token("https://management.azure.com/.default")
    print("✅ Authentication successful!")
except Exception as e:
    print(f"❌ Authentication failed: {e}")