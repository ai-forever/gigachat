from gigachat.models.auth import AccessToken, Token
from tests.constants import EXPIRES_AT_VALID, PASSWORD_EXPIRES_AT_VALID


def test_access_token_creation() -> None:
    data = {"access_token": "token-123", "expires_at": EXPIRES_AT_VALID}
    token = AccessToken.model_validate(data)
    assert token.access_token == "token-123"
    assert token.expires_at == EXPIRES_AT_VALID


def test_access_token_normalizes_seconds() -> None:
    """Backends returning the expiration in seconds must end up in milliseconds."""
    token = AccessToken.model_validate({"access_token": "token-123", "expires_at": PASSWORD_EXPIRES_AT_VALID})
    assert token.expires_at == EXPIRES_AT_VALID


def test_access_token_keeps_milliseconds() -> None:
    token = AccessToken.model_validate({"access_token": "token-123", "expires_at": EXPIRES_AT_VALID})
    assert token.expires_at == EXPIRES_AT_VALID


def test_access_token_keeps_never_expiring() -> None:
    """Zero marks a token without expiration and must not be scaled."""
    token = AccessToken.model_validate({"access_token": "token-123", "expires_at": 0})
    assert token.expires_at == 0


def test_token_creation() -> None:
    data = {"tok": "token-456", "exp": 1234567890}
    token = Token.model_validate(data)
    assert token.tok == "token-456"
    assert token.exp == 1234567890
