import requests
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.database.connection import SessionLocal
from app.services.entra_tokens import validate_azure_management_token, validate_id_token
from app.services.identity_service import IdentityRepository


router = APIRouter(prefix="/auth", tags=["authentication"])
repository = IdentityRepository(SessionLocal)


class EntraSession(BaseModel):
    id_token: str = Field(min_length=20)


class SubscriptionSelection(BaseModel):
    subscription_id: str
    subscription_name: str | None = None
    permissions_status: str = "UNVERIFIED"


class AzureAccessContext(EntraSession):
    azure_access_token: str = Field(min_length=20)


def current_claims(payload: EntraSession):
    return validate_id_token(payload.id_token)


@router.post("/session")
def establish_session(payload: EntraSession):
    claims = current_claims(payload)
    try:
        user = repository.upsert_user(claims)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Identity store unavailable") from exc
    return {"user": {"id": user.id, "email": user.email, "display_name": user.display_name, "tenant_id": user.tenant_id}}


@router.post("/azure-connections")
def connect_subscription(selection: SubscriptionSelection, payload: EntraSession):
    claims = current_claims(payload)
    try:
        user = repository.upsert_user(claims)
        connection = repository.save_connection(user.id, claims["tid"], selection.subscription_id, selection.subscription_name, selection.permissions_status)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Connection store unavailable") from exc
    return {"connection": {"id": connection.id, "subscription_id": connection.subscription_id, "subscription_name": connection.subscription_name, "status": connection.connection_status}}


@router.post("/subscriptions")
def list_subscriptions(payload: AzureAccessContext):
    """Use delegated Azure access for this request only; never persist the token."""
    identity = current_claims(payload)
    azure_claims = validate_azure_management_token(payload.azure_access_token)
    if not identity.get("oid") or identity.get("oid") != azure_claims.get("oid"):
        raise HTTPException(status_code=401, detail="Azure access token does not belong to the signed-in user")
    try:
        response = requests.get("https://management.azure.com/subscriptions?api-version=2020-01-01", headers={"Authorization": f"Bearer {payload.azure_access_token}"}, timeout=10)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise HTTPException(status_code=403, detail="Unable to list Azure subscriptions with the granted permissions") from exc
    return {"tenant_id": identity["tid"], "subscriptions": [{"subscription_id": item["subscriptionId"], "subscription_name": item.get("displayName"), "state": item.get("state")} for item in response.json().get("value", [])]}
