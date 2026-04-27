import asyncio
import threading
from unittest.mock import MagicMock, patch

from gigachat import GigaChat
from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient
from gigachat.resources.ai_check import AICheckAsyncResource, AICheckSyncResource
from gigachat.resources.balance import BalanceAsyncResource, BalanceSyncResource
from gigachat.resources.batches import BatchesAsyncResource, BatchesSyncResource
from gigachat.resources.embeddings import EmbeddingsAsyncResource, EmbeddingsSyncResource
from gigachat.resources.files import FilesAsyncResource, FilesSyncResource
from gigachat.resources.functions import FunctionsAsyncResource, FunctionsSyncResource
from gigachat.resources.models import ModelsAsyncResource, ModelsSyncResource
from gigachat.resources.threads import ThreadsAsyncClient, ThreadsSyncClient
from gigachat.resources.tokens import TokensAsyncResource, TokensSyncResource


def test_lazy_init_sync() -> None:
    """Test that synchronous client usage does not create async clients."""
    with GigaChat() as giga:
        assert giga._client is not None
        assert giga._auth_client is not None
        assert giga._aclient_instance is None
        assert giga._auth_aclient_instance is None


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


def test_sync_resources_are_cached_properties() -> None:
    client = GigaChatSyncClient()

    assert "chat" not in client.__dict__
    assert "assistants" not in client.__dict__
    assert "models" not in client.__dict__
    assert "embeddings" not in client.__dict__
    assert "batches" not in client.__dict__
    assert "files" not in client.__dict__
    assert "tokens" not in client.__dict__
    assert "balance" not in client.__dict__
    assert "functions" not in client.__dict__
    assert "ai_check" not in client.__dict__
    assert "threads" not in client.__dict__

    chat = client.chat
    legacy_chat = chat.legacy
    assistants = client.assistants
    models = client.models
    embeddings = client.embeddings
    batches = client.batches
    files = client.files
    tokens = client.tokens
    balance = client.balance
    functions = client.functions
    ai_check = client.ai_check
    threads = client.threads

    assert chat is client.chat
    assert legacy_chat is chat.legacy
    assert legacy_chat is client.chat.legacy
    assert assistants is client.assistants
    assert models is client.models
    assert embeddings is client.embeddings
    assert batches is client.batches
    assert files is client.files
    assert tokens is client.tokens
    assert balance is client.balance
    assert functions is client.functions
    assert ai_check is client.ai_check
    assert threads is client.threads
    assert isinstance(models, ModelsSyncResource)
    assert isinstance(embeddings, EmbeddingsSyncResource)
    assert isinstance(batches, BatchesSyncResource)
    assert isinstance(files, FilesSyncResource)
    assert isinstance(tokens, TokensSyncResource)
    assert isinstance(balance, BalanceSyncResource)
    assert isinstance(functions, FunctionsSyncResource)
    assert isinstance(ai_check, AICheckSyncResource)
    assert isinstance(threads, ThreadsSyncClient)


async def test_async_resources_are_cached_properties() -> None:
    client = GigaChatAsyncClient()

    assert "achat" not in client.__dict__
    assert "a_assistants" not in client.__dict__
    assert "a_models" not in client.__dict__
    assert "a_embeddings" not in client.__dict__
    assert "a_batches" not in client.__dict__
    assert "a_files" not in client.__dict__
    assert "a_tokens" not in client.__dict__
    assert "a_balance" not in client.__dict__
    assert "a_functions" not in client.__dict__
    assert "a_ai_check" not in client.__dict__
    assert "a_threads" not in client.__dict__

    chat = client.achat
    legacy_chat = chat.legacy
    assistants = client.a_assistants
    models = client.a_models
    embeddings = client.a_embeddings
    batches = client.a_batches
    files = client.a_files
    tokens = client.a_tokens
    balance = client.a_balance
    functions = client.a_functions
    ai_check = client.a_ai_check
    threads = client.a_threads

    assert chat is client.achat
    assert legacy_chat is chat.legacy
    assert legacy_chat is client.achat.legacy
    assert assistants is client.a_assistants
    assert models is client.a_models
    assert embeddings is client.a_embeddings
    assert batches is client.a_batches
    assert files is client.a_files
    assert tokens is client.a_tokens
    assert balance is client.a_balance
    assert functions is client.a_functions
    assert ai_check is client.a_ai_check
    assert threads is client.a_threads
    assert isinstance(models, ModelsAsyncResource)
    assert isinstance(embeddings, EmbeddingsAsyncResource)
    assert isinstance(batches, BatchesAsyncResource)
    assert isinstance(files, FilesAsyncResource)
    assert isinstance(tokens, TokensAsyncResource)
    assert isinstance(balance, BalanceAsyncResource)
    assert isinstance(functions, FunctionsAsyncResource)
    assert isinstance(ai_check, AICheckAsyncResource)
    assert isinstance(threads, ThreadsAsyncClient)
