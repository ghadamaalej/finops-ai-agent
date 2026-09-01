"""Strict single-tenant OIDC ID-token validation for the FastAPI boundary."""

from functools import lru_cache
import logging

import jwt
import requests
from fastapi import HTTPException, status

from config.settings import settings


ISSUER = f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/v2.0"
JWKS_URL = f"https://login.microsoftonline.com/{settings.AZURE_TENANT_ID}/discovery/v2.0/keys"
logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _jwks():
    return requests.get(JWKS_URL, timeout=5).json()["keys"]


def validate_id_token(token: str, audience: str | None = None):
    try:
        header = jwt.get_unverified_header(token)
        key = next(item for item in _jwks() if item["kid"] == header["kid"])
        claims = jwt.decode(token, jwt.algorithms.RSAAlgorithm.from_jwk(key), algorithms=["RS256"], audience=audience or settings.AZURE_CLIENT_ID, issuer=ISSUER)
        if claims.get("tid") != settings.AZURE_TENANT_ID:
            raise ValueError("unexpected tenant")
        if not claims.get("sub"):
            raise ValueError("missing subject")
        return claims
    except Exception as exc:
        logger.warning("Entra ID token validation failed: %s", exc)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid Microsoft Entra ID token") from exc


def validate_azure_management_token(token: str):
    try:
        header = jwt.get_unverified_header(token)

        key = next(
            item for item in _jwks()
            if item["kid"] == header["kid"]
        )

        claims = jwt.decode(
            token,
            jwt.algorithms.RSAAlgorithm.from_jwk(key),
            algorithms=["RS256"],
            options={
                "verify_iss": False,
                "verify_aud": False,
            },
        )

        allowed_audiences = {
            "https://management.azure.com",
            "https://management.azure.com/",
            "https://management.core.windows.net",
            "https://management.core.windows.net/",
        }

        if claims.get("aud") not in allowed_audiences:
            raise ValueError(
                f"unexpected Azure audience: {claims.get('aud')}"
            )

        if claims.get("tid") != settings.AZURE_TENANT_ID:
            raise ValueError("unexpected Azure tenant")

        if not claims.get("oid"):
            raise ValueError("missing Azure object ID")

        return claims

    except Exception as exc:
        logger.warning(
            "Azure Management token validation failed: %s",
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Azure Management access token",
        ) from exc