from typing import TYPE_CHECKING

from gigachat.api import models
from gigachat.authentication import _awith_auth, _with_auth
from gigachat.models.models import Model, Models
from gigachat.retry import _awith_retry, _with_retry

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient


class ModelsSyncResource:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self._base_client = base_client

    @_with_retry
    @_with_auth
    def list(self) -> Models:
        """Return a list of available models."""
        return models.get_models_sync(self._base_client._client, access_token=self._base_client.token)

    @_with_retry
    @_with_auth
    def retrieve(self, model: str) -> Model:
        """Return a description of a specific model."""
        return models.get_model_sync(self._base_client._client, model=model, access_token=self._base_client.token)


class ModelsAsyncResource:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self._base_client = base_client

    @_awith_retry
    @_awith_auth
    async def list(self) -> Models:
        """Return a list of available models."""
        return await models.get_models_async(self._base_client._aclient, access_token=self._base_client.token)

    @_awith_retry
    @_awith_auth
    async def retrieve(self, model: str) -> Model:
        """Return a description of a specific model."""
        return await models.get_model_async(
            self._base_client._aclient,
            model=model,
            access_token=self._base_client.token,
        )
