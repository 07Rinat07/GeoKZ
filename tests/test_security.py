from app.core.security import hash_password, hash_token, issue_opaque_token, verify_password


def test_password_hash_round_trip_and_wrong_password() -> None:
    encoded = hash_password("GeoKZ-Test-Password-2026!")
    assert encoded.startswith("scrypt-v1$")
    assert verify_password("GeoKZ-Test-Password-2026!", encoded) is True
    assert verify_password("GeoKZ-Wrong-Password-2026!", encoded) is False


def test_password_hash_rejects_short_password() -> None:
    try:
        hash_password("short")
    except ValueError as error:
        assert "12" in str(error)
    else:
        raise AssertionError("short password must be rejected")


def test_opaque_tokens_are_random_and_only_hash_is_stable() -> None:
    first = issue_opaque_token()
    second = issue_opaque_token()
    assert first != second
    assert len(first) >= 48
    assert len(hash_token(first)) == 64
    assert hash_token(first) == hash_token(first)
    assert hash_token(first) != hash_token(second)
