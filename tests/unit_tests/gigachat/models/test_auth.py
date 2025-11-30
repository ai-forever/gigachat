from gigachat.models.auth import AccessToken, Token


def test_access_token_creation() -> None:
    data = {"access_token": "token-123", "expires_at": 1234567890}
    token = AccessToken.model_validate(data)
    assert token.access_token == "token-123"
    assert token.expires_at == 1234567890


def test_token_creation() -> None:
    data = {"tok": "token-456", "exp": 1234567890}
    token = Token.model_validate(data)
    assert token.tok == "token-456"
    assert token.exp == 1234567890
