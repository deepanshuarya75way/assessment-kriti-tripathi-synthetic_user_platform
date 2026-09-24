"""Unit tests for password hashing and JWT handling (spec §21 security)."""

import time

import pytest

from app.core.exceptions import UnauthorizedError
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_password_hash_roundtrip():
    hashed = hash_password("s3cret-pass")
    assert hashed != "s3cret-pass"  # never plaintext
    assert verify_password("s3cret-pass", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_roundtrip():
    token = create_access_token("user-123")
    assert decode_access_token(token) == "user-123"


def test_jwt_invalid_token_rejected():
    with pytest.raises(UnauthorizedError):
        decode_access_token("not.a.jwt")


def test_jwt_expired_token_rejected():
    token = create_access_token("user-123", expires_minutes=-1)
    time.sleep(0.01)
    with pytest.raises(UnauthorizedError):
        decode_access_token(token)
