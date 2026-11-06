from __future__ import annotations

import copy
import inspect
import json
from collections.abc import AsyncIterator, Iterator
from typing import TYPE_CHECKING, Any, TypeVar, cast

import pydantic

from gigachat._core.base_client import _BaseClient
from gigachat._core.execution import request_async, request_scope, request_sync
from gigachat._core.request import RequestOptions
from gigachat._core.response import RawResponse
from gigachat.api import chat, chat_completions
from gigachat.api.chat_completions import _get_chat_kwargs
from gigachat.api.utils import build_response
from gigachat.exceptions import LengthFinishReasonError
from gigachat.models import Chat, ChatCompletion, ChatCompletionRequest, ChatCompletionResponse
from gigachat.models.chat import ChatCompletionChunk, Messages, MessagesRole
from gigachat.models.chat_completions import ChatCompletionChunk as PrimaryChatCompletionChunk
from gigachat.models.chat_completions import ChatMessage, ChatResponseFormat, ChatStorage
from gigachat.models.response_format import JsonSchemaResponseFormat

if TYPE_CHECKING:
    from gigachat.client import GigaChatAsyncClient, GigaChatSyncClient

ModelT = TypeVar("ModelT", bound=pydantic.BaseModel)
PrimaryPayload = ChatCompletionRequest | dict[str, Any] | str
LegacyPayload = Chat | dict[str, Any] | str


class RawChatNamespace:
    """Return buffered HTTP responses with synchronous typed parsing."""

    def __init__(self, base_client: GigaChatSyncClient) -> None:
        self._base_client = base_client

    @request_scope
    def create(
        self, payload: PrimaryPayload, *, request_options: RequestOptions | None = None
    ) -> RawResponse[ChatCompletionResponse]:
        client = self._base_client
        chat = _parse_chat_completion(payload, client)
        response = request_sync(
            client._client, **_get_chat_kwargs(client._client, chat=chat, access_token=client.token)
        )
        return RawResponse(response, lambda result: build_response(result, ChatCompletionResponse))


class AsyncRawChatNamespace:
    """Return asynchronously read HTTP responses with synchronous typed parsing."""

    def __init__(self, base_client: GigaChatAsyncClient) -> None:
        self._base_client = base_client

    @request_scope
    async def create(
        self, payload: PrimaryPayload, *, request_options: RequestOptions | None = None
    ) -> RawResponse[ChatCompletionResponse]:
        client = self._base_client
        chat = _parse_chat_completion(payload, client)
        response = await request_async(
            client._aclient, **_get_chat_kwargs(client._aclient, chat=chat, access_token=client.token)
        )
        return RawResponse(response, lambda result: build_response(result, ChatCompletionResponse))


def _validate_response_format(payload: Chat | dict[str, Any] | str) -> None:
    """Raise TypeError if response_format is a Pydantic model on the root chat path."""
    if isinstance(payload, dict):
        response_format = payload.get("response_format")
    elif isinstance(payload, Chat):
        response_format = payload.response_format
    else:
        return
    if (
        response_format is not None
        and inspect.isclass(response_format)
        and issubclass(response_format, pydantic.BaseModel)
    ):
        raise TypeError(
            "You tried to pass a Pydantic model to `chat(response_format=...)`; "
            "use `client.chat_parse(payload, response_format=...)` or "
            "`client.achat_parse(payload, response_format=...)` instead"
        )


def _parse_chat(payload: Chat | dict[str, Any] | str, client: _BaseClient) -> Chat:
    if isinstance(payload, str):
        chat = Chat(messages=[Messages(role=MessagesRole.USER, content=payload)])
    else:
        chat = Chat.model_validate(copy.deepcopy(payload))
    using_assistant = chat.assistant_id is not None or (
        chat.storage is not None and (chat.storage.assistant_id or chat.storage.thread_id)
    )
    if not using_assistant:
        chat.model = client._resolve_model(chat.model)
    if chat.profanity_check is None:
        chat.profanity_check = client._settings.profanity_check
    if chat.flags is None:
        chat.flags = copy.deepcopy(client._settings.flags)
    return chat


def _prepare_chat_for_parse(
    payload: Chat | dict[str, Any] | str,
    client: _BaseClient,
    response_format: type[pydantic.BaseModel],
    strict: bool,
) -> Chat:
    """Prepare a Chat object with response_format derived from *response_format*."""
    chat_data = _parse_chat(payload, client)
    chat_data.response_format = JsonSchemaResponseFormat.model_validate({"schema": response_format, "strict": strict})
    return chat_data


def _prepare_chat_completion_for_parse(
    payload: ChatCompletionRequest | dict[str, Any] | str,
    client: _BaseClient,
    response_format: type[pydantic.BaseModel],
    strict: bool,
) -> ChatCompletionRequest:
    """Prepare a primary chat completion request with a structured response schema."""
    chat_data = _parse_chat_completion(payload, client)
    chat_data.response_format = ChatResponseFormat.model_validate(
        {"type": "json_schema", "schema": response_format, "strict": strict}
    )
    return chat_data


def _parse_chat_completion(
    payload: ChatCompletionRequest | dict[str, Any] | str,
    client: _BaseClient,
) -> ChatCompletionRequest:
    if isinstance(payload, str):
        chat = ChatCompletionRequest(messages=[ChatMessage(role="user", content=payload)])
    else:
        chat = ChatCompletionRequest.model_validate(copy.deepcopy(payload))

    using_assistant = chat.assistant_id is not None or (
        isinstance(chat.storage, ChatStorage) and chat.storage.thread_id is not None
    )
    if not using_assistant:
        chat.model = client._resolve_model(chat.model)
    if chat.disable_filter is None and client._settings.profanity_check is not None:
        chat.disable_filter = not client._settings.profanity_check
    if chat.flags is None:
        chat.flags = copy.deepcopy(client._settings.flags)
    return chat


def _parse_completion(
    completion: ChatCompletion,
    response_format: type[ModelT],
) -> ModelT:
    """Parse and validate message content from *completion* into *response_format*."""
    if not completion.choices:
        raise ValueError("Response has no choices")

    choice = completion.choices[0]

    if choice.finish_reason == "length":
        raise LengthFinishReasonError(completion)

    data = json.loads(choice.message.content)
    return response_format.model_validate(data)


def _parse_primary_completion(
    completion: ChatCompletionResponse,
    response_format: type[ModelT],
) -> ModelT:
    """Parse and validate assistant text content from *completion* into *response_format*."""
    if not completion.messages:
        raise ValueError("Response has no messages")

    if completion.finish_reason == "length":
        raise LengthFinishReasonError(completion)

    found_assistant_message = False

    for message in completion.messages:
        if message.role != "assistant":
            continue

        found_assistant_message = True

        if message.finish_reason == "length":
            raise LengthFinishReasonError(completion)

        if not message.content:
            continue

        raw_content = "".join(part.text for part in message.content if part.text is not None)
        if not raw_content:
            continue

        data = json.loads(raw_content)
        return response_format.model_validate(data)

    if not found_assistant_message:
        raise ValueError("Response has no assistant messages")

    raise ValueError("Response has no assistant text content")


class ChatNamespace:
    """Expose primary and legacy chat operations."""

    def __init__(self, base_client: GigaChatSyncClient) -> None:
        self._base_client = base_client
        self.with_raw_response = RawChatNamespace(base_client)

    @request_scope
    def create(
        self, payload: ChatCompletionRequest | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> ChatCompletionResponse:
        """Return a primary chat completion based on the provided messages."""
        chat_data = _parse_chat_completion(payload, self._base_client)
        return chat_completions.chat_sync(
            self._base_client._client, chat=chat_data, access_token=self._base_client.token
        )

    @request_scope
    def stream(
        self, payload: ChatCompletionRequest | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> Iterator[PrimaryChatCompletionChunk]:
        """Return a primary streaming chat completion based on the provided messages."""
        chat_data = _parse_chat_completion(payload, self._base_client)
        yield from chat_completions.stream_sync(
            self._base_client._client, chat=chat_data, access_token=self._base_client.token
        )

    @request_scope
    def parse(
        self,
        payload: ChatCompletionRequest | dict[str, Any] | str,
        *,
        response_format: type[ModelT],
        strict: bool = True,
        request_options: RequestOptions | None = None,
    ) -> tuple[ChatCompletionResponse, ModelT]:
        """Send a primary chat request and parse the response into a structured object."""
        chat_data = _prepare_chat_completion_for_parse(payload, self._base_client, response_format, strict)
        completion = chat_completions.chat_sync(
            self._base_client._client, chat=chat_data, access_token=self._base_client.token
        )
        parsed = _parse_primary_completion(completion, response_format)
        return completion, parsed

    @request_scope
    def __call__(
        self, payload: Chat | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> ChatCompletion:
        """Return a root chat completion based on the provided messages."""
        _validate_response_format(payload)
        chat_data = _parse_chat(payload, self._base_client)
        return chat.chat_sync(self._base_client._client, chat=chat_data, access_token=self._base_client.token)

    @request_scope
    def _legacy_stream(
        self, payload: Chat | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> Iterator[ChatCompletionChunk]:
        """Return a root streaming chat completion based on the provided messages."""
        chat_data = _parse_chat(payload, self._base_client)

        yield from chat.stream_sync(self._base_client._client, chat=chat_data, access_token=self._base_client.token)

    @request_scope
    def _legacy_parse(
        self,
        payload: Chat | dict[str, Any] | str,
        *,
        response_format: type[ModelT],
        strict: bool = True,
        request_options: RequestOptions | None = None,
    ) -> tuple[ChatCompletion, ModelT]:
        """Send a root chat request and parse the response into a structured object."""
        chat_data = _prepare_chat_for_parse(payload, self._base_client, response_format, strict)
        completion = chat.chat_sync(self._base_client._client, chat=chat_data, access_token=self._base_client.token)
        parsed = _parse_completion(completion, response_format)
        return completion, parsed


class AsyncChatNamespace:
    """Expose primary and legacy chat operations."""

    def __init__(self, base_client: GigaChatAsyncClient) -> None:
        self._base_client = base_client
        self.with_raw_response = AsyncRawChatNamespace(base_client)

    @request_scope
    async def __call__(
        self, payload: Chat | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> ChatCompletion:
        """Return a root chat completion based on the provided messages."""
        _validate_response_format(payload)
        chat_data = _parse_chat(payload, self._base_client)

        return await chat.chat_async(self._base_client._aclient, chat=chat_data, access_token=self._base_client.token)

    @request_scope
    async def create(
        self, payload: ChatCompletionRequest | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> ChatCompletionResponse:
        """Return a primary chat completion based on the provided messages."""
        chat_data = _parse_chat_completion(payload, self._base_client)
        return await chat_completions.chat_async(
            self._base_client._aclient, chat=chat_data, access_token=self._base_client.token
        )

    @request_scope
    async def stream(
        self, payload: ChatCompletionRequest | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> AsyncIterator[PrimaryChatCompletionChunk]:
        """Return a primary streaming chat completion based on the provided messages."""
        chat_data = _parse_chat_completion(payload, self._base_client)
        iterator = chat_completions.stream_async(
            self._base_client._aclient, chat=chat_data, access_token=self._base_client.token
        )
        try:
            async for chunk in iterator:
                yield chunk
        finally:
            await cast(Any, iterator).aclose()

    @request_scope
    async def _legacy_stream(
        self, payload: Chat | dict[str, Any] | str, *, request_options: RequestOptions | None = None
    ) -> AsyncIterator[ChatCompletionChunk]:
        """Return a root streaming chat completion based on the provided messages."""
        chat_data = _parse_chat(payload, self._base_client)
        iterator = chat.stream_async(self._base_client._aclient, chat=chat_data, access_token=self._base_client.token)
        try:
            async for chunk in iterator:
                yield chunk
        finally:
            await cast(Any, iterator).aclose()

    @request_scope
    async def parse(
        self,
        payload: ChatCompletionRequest | dict[str, Any] | str,
        *,
        response_format: type[ModelT],
        strict: bool = True,
        request_options: RequestOptions | None = None,
    ) -> tuple[ChatCompletionResponse, ModelT]:
        """Send a primary chat request and parse the response into a structured object."""
        chat_data = _prepare_chat_completion_for_parse(payload, self._base_client, response_format, strict)
        completion = await chat_completions.chat_async(
            self._base_client._aclient, chat=chat_data, access_token=self._base_client.token
        )
        parsed = _parse_primary_completion(completion, response_format)
        return completion, parsed

    @request_scope
    async def _legacy_parse(
        self,
        payload: Chat | dict[str, Any] | str,
        *,
        response_format: type[ModelT],
        strict: bool = True,
        request_options: RequestOptions | None = None,
    ) -> tuple[ChatCompletion, ModelT]:
        """Send a root chat request and parse the response into *response_format*."""
        chat_data = _prepare_chat_for_parse(payload, self._base_client, response_format, strict)
        completion = await chat.chat_async(
            self._base_client._aclient, chat=chat_data, access_token=self._base_client.token
        )
        parsed = _parse_completion(completion, response_format)
        return completion, parsed
