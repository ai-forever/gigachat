import asyncio
import threading
from unittest.mock import MagicMock, patch

import pytest

from gigachat import GigaChat


def test_lazy_init_sync() -> None:
    """Test that synchronous client usage does not create async clients."""
    with GigaChat() as giga:
        assert giga._client is not None
        assert giga._auth_client is not None
        assert giga._aclient_instance is None
        assert giga._auth_aclient_instance is None


@pytest.mark.asyncio
async def test_lazy_init_async() -> None:
    """Test that asynchronous client usage does not create sync clients."""
    async with GigaChat() as giga:
        assert giga._aclient is not None
        assert giga._auth_aclient is not None
        assert giga._client_instance is None
        assert giga._auth_client_instance is None


def test_lazy_init_manual_close() -> None:
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


def test_thread_safety_init() -> None:
    """Test that multiple threads initializing the client result in only one instance."""
    giga = GigaChat()

    # We'll track how many times httpx.Client is instantiated
    with patch("gigachat.client.httpx.Client") as mock_client_cls:
        mock_client_cls.return_value = MagicMock()

        def access_client() -> None:
            _ = giga._client

        threads = [threading.Thread(target=access_client) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should be called exactly once due to locking
        assert mock_client_cls.call_count == 1
        assert giga._client_instance is not None


@pytest.mark.asyncio
async def test_hybrid_cleanup_in_async_context() -> None:
    """Test that aclose() cleans up both sync and async clients if both were used."""
    giga = GigaChat()

    # Mock the internal instances so we can verify close calls
    mock_sync_client = MagicMock()
    mock_async_client = MagicMock()
    mock_async_client.aclose = MagicMock(return_value=asyncio.Future())
    mock_async_client.aclose.return_value.set_result(None)

    # Manually inject mocks (simulating lazy init completion)
    giga._client_instance = mock_sync_client
    giga._aclient_instance = mock_async_client

    # Act: Call aclose (simulating exit from async with)
    await giga.aclose()

    # Assert: Both should be closed
    mock_sync_client.close.assert_called_once()
    mock_async_client.aclose.assert_called_once()


@pytest.mark.asyncio
async def test_hybrid_cleanup_partial_usage() -> None:
    """Test that aclose() doesn't fail if sync client wasn't initialized."""
    giga = GigaChat()

    # Only async client initialized
    mock_async_client = MagicMock()
    mock_async_client.aclose = MagicMock(return_value=asyncio.Future())
    mock_async_client.aclose.return_value.set_result(None)
    giga._aclient_instance = mock_async_client

    # Sync client remains None
    assert giga._client_instance is None

    # Act
    await giga.aclose()

    # Assert
    mock_async_client.aclose.assert_called_once()
    # Should not raise error regarding NoneType for sync client
