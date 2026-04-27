from typing import TYPE_CHECKING, List, Optional

from gigachat.api import tools
from gigachat.authentication import _awith_auth, _with_auth
from gigachat.models.tools import TokensCount
from gigachat.retry import _awith_retry, _with_retry

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient


class TokensSyncResource:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self._base_client = base_client

    @_with_retry
    @_with_auth
    def count(self, input_: List[str], model: Optional[str] = None) -> List[TokensCount]:
        """Return the number of tokens in a string."""
        if model is None:
            from gigachat.client import GIGACHAT_MODEL

            model = self._base_client._settings.model or GIGACHAT_MODEL

        return tools.tokens_count_sync(
            self._base_client._client,
            input_=input_,
            model=model,
            access_token=self._base_client.token,
        )


class TokensAsyncResource:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self._base_client = base_client

    @_awith_retry
    @_awith_auth
    async def count(self, input_: List[str], model: Optional[str] = None) -> List[TokensCount]:
        """Return the number of tokens in a string."""
        if model is None:
            from gigachat.client import GIGACHAT_MODEL

            model = self._base_client._settings.model or GIGACHAT_MODEL

        return await tools.tokens_count_async(
            self._base_client._aclient,
            input_=input_,
            model=model,
            access_token=self._base_client.token,
        )
