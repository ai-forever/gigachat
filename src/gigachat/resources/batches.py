from typing import TYPE_CHECKING, Literal

from gigachat._types import FileContent
from gigachat.api import batches
from gigachat.authentication import _awith_auth, _with_auth
from gigachat.models.batches import Batch, Batches
from gigachat.retry import _awith_retry, _with_retry

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient


class BatchesSyncResource:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self._base_client = base_client

    @_with_retry
    @_with_auth
    def create(self, file: FileContent, method: Literal["chat_completions", "embedder"]) -> Batch:
        """Create a batch task for asynchronous processing."""
        return batches.create_batch_sync(
            self._base_client._client,
            file=file,
            method=method,
            access_token=self._base_client.token,
        )

    @_with_retry
    @_with_auth
    def list(self) -> Batches:
        """Return batch tasks."""
        return batches.get_batches_sync(self._base_client._client, access_token=self._base_client.token)

    @_with_retry
    @_with_auth
    def retrieve(self, batch_id: str) -> Batches:
        """Return a specific batch task."""
        return batches.get_batches_sync(
            self._base_client._client,
            batch_id=batch_id,
            access_token=self._base_client.token,
        )


class BatchesAsyncResource:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self._base_client = base_client

    @_awith_retry
    @_awith_auth
    async def create(self, file: FileContent, method: Literal["chat_completions", "embedder"]) -> Batch:
        """Create a batch task for asynchronous processing."""
        return await batches.create_batch_async(
            self._base_client._aclient,
            file=file,
            method=method,
            access_token=self._base_client.token,
        )

    @_awith_retry
    @_awith_auth
    async def list(self) -> Batches:
        """Return batch tasks."""
        return await batches.get_batches_async(self._base_client._aclient, access_token=self._base_client.token)

    @_awith_retry
    @_awith_auth
    async def retrieve(self, batch_id: str) -> Batches:
        """Return a specific batch task."""
        return await batches.get_batches_async(
            self._base_client._aclient,
            batch_id=batch_id,
            access_token=self._base_client.token,
        )
