"""Authentication business logic (spec §17)."""

import logging

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.logging import log_event
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.repositories.user_repository import UserRepository

log = logging.getLogger(__name__)


class AuthService:
    def __init__(self, db: Session):
        self.users = UserRepository(db)

    def register(self, *, email: str, password: str, full_name: str | None) -> User:
        if self.users.get_by_email(email):
            raise ConflictError("An account with this email already exists.")
        user = self.users.create(
            email=email, hashed_password=hash_password(password), full_name=full_name
        )
        log_event(log, logging.INFO, "auth.registered", user_id=user.id)
        return user

    def authenticate(self, *, email: str, password: str) -> str:
        user = self.users.get_by_email(email)
        # Verify even when the user is missing would be ideal for timing; kept simple here.
        if not user or not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Incorrect email or password.")
        log_event(log, logging.INFO, "auth.login", user_id=user.id)
        return create_access_token(subject=user.id)

    def get_user(self, user_id: str) -> User | None:
        return self.users.get(user_id)
