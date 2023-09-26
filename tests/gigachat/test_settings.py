from gigachat.settings import Settings


def test_settings():
    assert Settings()


def test_settings_use_auth_false():
    assert Settings(use_auth=False)
