from uuid import uuid4

import pytest

from backend.services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from backend.core.exceptions import AuthenticationError


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "test_password_123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_wrong_password_fails(self):
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_different_hashes_for_same_password(self):
        pwd = "same_password"
        hash1 = hash_password(pwd)
        hash2 = hash_password(pwd)
        assert hash1 != hash2


class TestJWT:
    def test_create_and_decode_token(self):
        user_id = uuid4()
        token = create_access_token(user_id=user_id, role="admin")
        payload = decode_access_token(token)
        assert payload["sub"] == str(user_id)
        assert payload["role"] == "admin"

    def test_token_contains_claims(self):
        token = create_access_token(user_id=uuid4(), role="reviewer")
        payload = decode_access_token(token)
        assert "exp" in payload
        assert "iat" in payload
        assert payload["role"] == "reviewer"

    def test_invalid_token_raises(self):
        with pytest.raises(AuthenticationError):
            decode_access_token("invalid.token.here")
