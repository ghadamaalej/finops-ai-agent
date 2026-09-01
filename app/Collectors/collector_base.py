from app.services.azure_credential import get_azure_credential

credential = get_azure_credential()

def subscription_scope(subscription_id: str) -> str:
    return f"/subscriptions/{subscription_id}"