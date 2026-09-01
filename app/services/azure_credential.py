import time

from azure.core.credentials import AccessToken
from azure.identity import AzureCliCredential


def get_azure_credential():

    print("Using Azure CLI Credential")
    
    credential = AzureCliCredential()

    return credential


class DelegatedArmCredential:
    """Ephemeral Azure SDK credential backed by the user's ARM access token."""
    def __init__(self, access_token: str):
        self.access_token = access_token

    def get_token(self, *scopes, **kwargs):
        # The signed token is validated at the API boundary and is used only
        # during this request; it is never stored in PostgreSQL or a cache.
        return AccessToken(self.access_token, int(time.time()) + 300)
