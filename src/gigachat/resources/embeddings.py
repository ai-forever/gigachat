from typing import TYPE_CHECKING, List

from gigachat.api import embeddings
from gigachat.authentication import _awith_auth, _with_auth
from gigachat.models.embeddings import Embeddings
from gigachat.resources._utils import warn_deprecated_resource_api
from gigachat.retry import _awith_retry, _with_retry

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient


class EmbeddingsSyncResource:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self._base_client = base_client

    def __call__(self, texts: List[str], model: str = "Embeddings") -> Embeddings:
        """Return embeddings via deprecated callable shim."""
        warn_deprecated_resource_api("client.embeddings(...)", "client.embeddings.create(...)")
        return self.create(texts, model=model)

    @_with_retry
    @_with_auth
    def create(self, texts: List[str], model: str = "Embeddings") -> Embeddings:
        """Return embeddings."""
        return embeddings.embeddings_sync(
            self._base_client._client,
            access_token=self._base_client.token,
            input_=texts,
            model=model,
        )


class EmbeddingsAsyncResource:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self._base_client = base_client

    @_awith_retry
    @_awith_auth
    async def create(self, texts: List[str], model: str = "Embeddings") -> Embeddings:
        """Return embeddings."""
        return await embeddings.embeddings_async(
            self._base_client._aclient,
            access_token=self._base_client.token,
            input_=texts,
            model=model,
        )
