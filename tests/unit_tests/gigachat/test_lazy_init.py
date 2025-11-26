import pytest

from gigachat import GigaChat


def test_lazy_init_sync():
    """Test that synchronous client usage does not create async clients."""
    with GigaChat() as giga:
        assert giga._client is not None
        assert giga._auth_client is not None
        assert giga._aclient_instance is None
        assert giga._auth_aclient_instance is None


@pytest.mark.asyncio()
async def test_lazy_init_async():
    """Test that asynchronous client usage does not create sync clients."""
    async with GigaChat() as giga:
        assert giga._aclient is not None
        assert giga._auth_aclient is not None
        assert giga._client_instance is None
        assert giga._auth_client_instance is None


def test_lazy_init_manual_close():
    """Test that manual close only closes initialized clients."""
    giga = GigaChat()

    assert giga._client_instance is None
    assert giga._auth_client_instance is None
    assert giga._aclient_instance is None
    assert giga._auth_aclient_instance is None

    _ = giga._client
    assert giga._client_instance is not None

    giga.close()

    assert giga._aclient_instance is None
    assert giga._auth_aclient_instance is None
