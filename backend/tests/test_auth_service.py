import uuid
from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException

from app.models.user import User
from app.services.auth import (
    create_access_token,
    get_current_user,
    get_optional_user,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_and_verify(self):
        password = "secure_password_123"
        hashed = hash_password(password)

        assert hashed != password
        assert verify_password(password, hashed)

    def test_wrong_password_fails(self):
        hashed = hash_password("correct_password")
        assert not verify_password("wrong_password", hashed)

    def test_different_hashes_for_same_password(self):
        """Bcrypt should produce different salts each time."""
        h1 = hash_password("same_password")
        h2 = hash_password("same_password")
        assert h1 != h2


class TestJWT:
    def test_create_and_decode_token(self, db, sample_user):
        token = create_access_token(sample_user.id)

        assert isinstance(token, str)
        assert len(token) > 0

        # Token should work with get_current_user
        user = get_current_user(token=token, db=db)
        assert user.id == sample_user.id

    def test_invalid_token_raises(self, db):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token="invalid.token.here", db=db)
        assert exc_info.value.status_code == 401

    def test_no_token_raises(self, db):
        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=None, db=db)
        assert exc_info.value.status_code == 401

    def test_token_with_nonexistent_user_raises(self, db):
        fake_id = uuid.uuid4()
        token = create_access_token(fake_id)

        with pytest.raises(HTTPException) as exc_info:
            get_current_user(token=token, db=db)
        assert exc_info.value.status_code == 401


class TestOptionalUser:
    def test_returns_user_when_valid(self, db, sample_user):
        token = create_access_token(sample_user.id)
        user = get_optional_user(token=token, db=db)
        assert user is not None
        assert user.id == sample_user.id

    def test_returns_none_when_no_token(self, db):
        user = get_optional_user(token=None, db=db)
        assert user is None

    def test_returns_none_when_invalid_token(self, db):
        user = get_optional_user(token="bad.token", db=db)
        assert user is None
