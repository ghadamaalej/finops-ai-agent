"""Entra application identity persistence; intentionally token-free."""

from datetime import datetime

from app.database.models import ApplicationUser, AzureConnection


class IdentityRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def upsert_user(self, claims):
        session = self.session_factory()
        try:
            user = session.query(ApplicationUser).filter_by(entra_subject_id=claims["sub"], tenant_id=claims["tid"]).first()
            if user is None:
                user = ApplicationUser(entra_subject_id=claims["sub"], tenant_id=claims["tid"])
                session.add(user)
            user.email = claims.get("preferred_username") or claims.get("email")
            user.display_name = claims.get("name")
            user.last_login = datetime.utcnow()
            session.commit()
            session.refresh(user)
            return user
        finally:
            session.close()

    def save_connection(self, user_id, tenant_id, subscription_id, subscription_name=None, permissions_status="UNVERIFIED"):
        session = self.session_factory()
        try:
            connection = session.query(AzureConnection).filter_by(user_id=user_id, subscription_id=subscription_id).first()
            if connection is None:
                connection = AzureConnection(user_id=user_id, tenant_id=tenant_id, subscription_id=subscription_id)
                session.add(connection)
            connection.subscription_name = subscription_name
            connection.permissions_status = permissions_status
            session.commit()
            session.refresh(connection)
            return connection
        finally:
            session.close()
