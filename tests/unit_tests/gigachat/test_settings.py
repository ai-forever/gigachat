from gigachat.settings import Settings


def test_settings() -> None:
    assert Settings()


def test_settings_limits() -> None:
    settings = Settings(max_connections=1, max_auth_connections=2)
    assert settings.max_connections == 1
    assert settings.max_auth_connections == 2
