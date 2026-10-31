"""Password hashing and token encoding/decoding."""

import bcrypt
import pytest

from app.core.security import create_access_token, decode_token, hash_password, verify_password


def test_new_hashes_are_argon2():
    assert hash_password("secret").startswith("$argon2")


def test_legacy_bcrypt_hashes_still_verify():
    legacy = bcrypt.hashpw(b"secret", bcrypt.gensalt(rounds=4)).decode()
    assert verify_password("secret", legacy)
    assert not verify_password("wrong", legacy)


def test_token_roundtrip_carries_subject_and_role():
    token, _ = create_access_token(42, "agent", 7)
    payload = decode_token(token)
    assert payload["sub"] == "42"
    assert payload["role"] == "agent"
    assert payload["ref_id"] == 7


def test_garbage_token_raises_value_error():
    with pytest.raises(ValueError):
        decode_token("not-a-token")
