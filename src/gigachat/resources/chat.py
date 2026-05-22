from typing import TYPE_CHECKING, Any, AsyncIterator, Dict, Iterator, Tuple, Type, TypeVar, Union

import pydantic

from gigachat.models import Chat, ChatCompletion, ChatCompletionRequest, ChatCompletionResponse
from gigachat.models.chat_completions import ChatCompletionChunk as PrimaryChatCompletionChunk

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient

ModelT = TypeVar("ModelT", bound=pydantic.BaseModel)


class ChatNamespace:
    """Chat namespace reserved for chat resources and compatibility shims."""

    def __init__(self, base_client: "GigaChatSyncClient") -> None:
        self._base_client = base_client

    def create(self, payload: Union[ChatCompletionRequest, Dict[str, Any], str]) -> ChatCompletionResponse:
        """Create a primary chat completion."""
        return self._base_client._chat_create(payload)

    def stream(
        self, payload: Union[ChatCompletionRequest, Dict[str, Any], str]
    ) -> Iterator[PrimaryChatCompletionChunk]:
        """Stream a primary chat completion."""
        return self._base_client._chat_stream(payload)

    def parse(
        self,
        payload: Union[ChatCompletionRequest, Dict[str, Any], str],
        *,
        response_format: Type[ModelT],
        strict: bool = True,
    ) -> Tuple[ChatCompletionResponse, ModelT]:
        """Parse a primary chat completion into a model."""
        return self._base_client._chat_parse(
            payload,
            response_format=response_format,
            strict=strict,
        )

    def __call__(self, payload: Union[Chat, Dict[str, Any], str]) -> ChatCompletion:
        """Call the root chat compatibility shim."""
        return self._base_client._chat(payload)


class AsyncChatNamespace:
    """Async chat namespace reserved for chat resources and compatibility shims."""

    def __init__(self, base_client: "GigaChatAsyncClient") -> None:
        self._base_client = base_client

    async def create(self, payload: Union[ChatCompletionRequest, Dict[str, Any], str]) -> ChatCompletionResponse:
        """Create a primary chat completion."""
        return await self._base_client._achat_create(payload)

    def stream(
        self, payload: Union[ChatCompletionRequest, Dict[str, Any], str]
    ) -> AsyncIterator[PrimaryChatCompletionChunk]:
        """Stream a primary chat completion."""
        return self._base_client._achat_stream(payload)

    async def parse(
        self,
        payload: Union[ChatCompletionRequest, Dict[str, Any], str],
        *,
        response_format: Type[ModelT],
        strict: bool = True,
    ) -> Tuple[ChatCompletionResponse, ModelT]:
        """Parse a primary chat completion into a model."""
        return await self._base_client._achat_parse(
            payload,
            response_format=response_format,
            strict=strict,
        )

    async def __call__(self, payload: Union[Chat, Dict[str, Any], str]) -> ChatCompletion:
        """Call the async root chat compatibility shim."""
        return await self._base_client._achat(payload)
