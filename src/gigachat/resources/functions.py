from typing import TYPE_CHECKING, Any, Dict, Union

from gigachat.api import tools
from gigachat.authentication import _awith_auth, _with_auth
from gigachat.models.chat import Function
from gigachat.models.tools import FunctionValidationResult, OpenApiFunctions
from gigachat.retry import _awith_retry, _with_retry

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient


class FunctionsSyncResource:
    def __init__(self, base_client: "GigaChatSyncClient"):
        self._base_client = base_client

    @_with_retry
    @_with_auth
    def convert_openapi(self, openapi_function: str) -> OpenApiFunctions:
        """Convert OpenAPI function definition to GigaChat format."""
        return tools.functions_convert_sync(
            self._base_client._client,
            openapi_function=openapi_function,
            access_token=self._base_client.token,
        )

    @_with_retry
    @_with_auth
    def validate(self, function: Union[Function, Dict[str, Any]]) -> FunctionValidationResult:
        """Validate a GigaChat function definition."""
        return tools.function_validate_sync(
            self._base_client._client,
            function=function,
            access_token=self._base_client.token,
        )


class FunctionsAsyncResource:
    def __init__(self, base_client: "GigaChatAsyncClient"):
        self._base_client = base_client

    @_awith_retry
    @_awith_auth
    async def convert_openapi(self, openapi_function: str) -> OpenApiFunctions:
        """Convert OpenAPI function definition to GigaChat format."""
        return await tools.functions_convert_async(
            self._base_client._aclient,
            openapi_function=openapi_function,
            access_token=self._base_client.token,
        )

    @_awith_retry
    @_awith_auth
    async def validate(self, function: Union[Function, Dict[str, Any]]) -> FunctionValidationResult:
        """Validate a GigaChat function definition."""
        return await tools.function_validate_async(
            self._base_client._aclient,
            function=function,
            access_token=self._base_client.token,
        )
