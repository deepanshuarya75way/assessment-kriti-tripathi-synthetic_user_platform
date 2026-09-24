"""Shared FastAPI dependencies: DB session + current authenticated user."""

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models import User
from app.services.auth_service import AuthService

_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None or not credentials.credentials:
        raise UnauthorizedError("Not authenticated.")
    user_id = decode_access_token(credentials.credentials)
    user = AuthService(db).get_user(user_id)
    if user is None:
        raise UnauthorizedError("User no longer exists.")
    return user
