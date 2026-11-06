from typing import TYPE_CHECKING, Any, TypeVar

import pydantic

from gigachat._execution import request_async, request_scope, request_sync
from gigachat._request_options import RequestOptions
from gigachat._response import RawResponse
from gigachat._streaming import AsyncStream, Stream
from gigachat.api.chat_completions import _get_chat_kwargs
from gigachat.api.utils import build_response
from gigachat.models import Chat, ChatCompletion, ChatCompletionRequest, ChatCompletionResponse
from gigachat.models.chat_completions import ChatCompletionChunk as PrimaryChatCompletionChunk

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient

ModelT = TypeVar("ModelT", bound=pydantic.BaseModel)
PrimaryPayload = ChatCompletionRequest | dict[str, Any] | str
LegacyPayload = Chat | dict[str, Any] | str


class RawChatNamespace:
    """Return buffered HTTP responses with synchronous typed parsing."""

    def __init__(self, base_client: "GigaChatSyncClient") -> None:
        self._base_client = base_client

    @request_scope
    def create(
        self, payload: PrimaryPayload, *, request_options: RequestOptions | None = None
    ) -> RawResponse[ChatCompletionResponse]:
        from gigachat._serialization import _parse_chat_completion

        client = self._base_client
        chat = _parse_chat_completion(payload, client._settings)
        response = request_sync(
            client._client, **_get_chat_kwargs(client._client, chat=chat, access_token=client.token)
        )
        return RawResponse(response, lambda result: build_response(result, ChatCompletionResponse))


class AsyncRawChatNamespace:
    """Return asynchronously read HTTP responses with synchronous typed parsing."""

    def __init__(self, base_client: "GigaChatAsyncClient") -> None:
        self._base_client = base_client

    @request_scope
    async def create(
        self, payload: PrimaryPayload, *, request_options: RequestOptions | None = None
    ) -> RawResponse[ChatCompletionResponse]:
        from gigachat._serialization import _parse_chat_completion

        client = self._base_client
        chat = _parse_chat_completion(payload, client._settings)
        response = await request_async(
            client._aclient, **_get_chat_kwargs(client._aclient, chat=chat, access_token=client.token)
        )
        return RawResponse(response, lambda result: build_response(result, ChatCompletionResponse))


class ChatNamespace:
    """Expose primary chat resources and the root compatibility shim."""

    def __init__(self, base_client: "GigaChatSyncClient") -> None:
        self._base_client = base_client
        self.with_raw_response = RawChatNamespace(base_client)

    def create(
        self, payload: PrimaryPayload, *, request_options: RequestOptions | None = None
    ) -> ChatCompletionResponse:
        """Create a primary chat completion."""
        return self._base_client._chat_create(payload, request_options=request_options)

    def stream(
        self, payload: PrimaryPayload, *, request_options: RequestOptions | None = None
    ) -> Stream[PrimaryChatCompletionChunk]:
        """Stream a primary chat completion; use with for guaranteed early cleanup."""
        return self._base_client._chat_stream(payload, request_options=request_options)

    def parse(
        self,
        payload: PrimaryPayload,
        *,
        response_format: type[ModelT],
        strict: bool = True,
        request_options: RequestOptions | None = None,
    ) -> tuple[ChatCompletionResponse, ModelT]:
        """Parse a primary chat completion into a model."""
        return self._base_client._chat_parse(
            payload, response_format=response_format, strict=strict, request_options=request_options
        )

    def __call__(self, payload: LegacyPayload, *, request_options: RequestOptions | None = None) -> ChatCompletion:
        """Call the root chat compatibility shim."""
        return self._base_client._chat(payload, request_options=request_options)


class AsyncChatNamespace:
    """Expose async primary chat resources and the root compatibility shim."""

    def __init__(self, base_client: "GigaChatAsyncClient") -> None:
        self._base_client = base_client
        self.with_raw_response = AsyncRawChatNamespace(base_client)

    async def create(
        self, payload: PrimaryPayload, *, request_options: RequestOptions | None = None
    ) -> ChatCompletionResponse:
        """Create a primary chat completion."""
        return await self._base_client._achat_create(payload, request_options=request_options)

    def stream(
        self, payload: PrimaryPayload, *, request_options: RequestOptions | None = None
    ) -> AsyncStream[PrimaryChatCompletionChunk]:
        """Stream a primary chat completion; use async with for early cleanup."""
        return self._base_client._achat_stream(payload, request_options=request_options)

    async def parse(
        self,
        payload: PrimaryPayload,
        *,
        response_format: type[ModelT],
        strict: bool = True,
        request_options: RequestOptions | None = None,
    ) -> tuple[ChatCompletionResponse, ModelT]:
        """Parse a primary chat completion into a model."""
        return await self._base_client._achat_parse(
            payload, response_format=response_format, strict=strict, request_options=request_options
        )

    async def __call__(
        self, payload: LegacyPayload, *, request_options: RequestOptions | None = None
    ) -> ChatCompletion:
        """Call the async root chat compatibility shim."""
        return await self._base_client._achat(payload, request_options=request_options)
