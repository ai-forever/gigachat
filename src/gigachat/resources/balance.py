from typing import TYPE_CHECKING

from gigachat.api import tools
from gigachat.authentication import _awith_auth, _with_auth
from gigachat.models.tools import Balance
from gigachat.retry import _awith_retry, _with_retry

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient


class BalanceSyncResource:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self._base_client = base_client

    @_with_retry
    @_with_auth
    def get(self) -> Balance:
        """
        Return the balance of available tokens.

        Only for prepaid clients, otherwise HTTP 403.
        """
        return tools.get_balance_sync(self._base_client._client, access_token=self._base_client.token)


class BalanceAsyncResource:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self._base_client = base_client

    @_awith_retry
    @_awith_auth
    async def get(self) -> Balance:
        """
        Return the balance of available tokens.

        Only for prepaid clients, otherwise HTTP 403.
        """
        return await tools.get_balance_async(self._base_client._aclient, access_token=self._base_client.token)
