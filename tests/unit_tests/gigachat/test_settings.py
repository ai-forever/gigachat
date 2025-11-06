from gigachat.settings import Settings


def test_settings() -> None:
    assert Settings()


def test_settings_env(monkeypatch) -> None:
    monkeypatch.setenv("GIGACHAT_MAX_CONNECTIONS", "5")
    monkeypatch.setenv("GIGACHAT_MAX_AUTH_CONNECTIONS", "7")

    settings = Settings()

    assert settings.max_connections == 5
    assert settings.max_auth_connections == 7
