"""Describe replayability without buffering uploads."""

from __future__ import annotations

import copy
import inspect
import json
from typing import Any, TypeVar

import pydantic

from gigachat.exceptions import LengthFinishReasonError, ModelNotSpecifiedError
from gigachat.models.auth import AccessToken, Token
from gigachat.models.chat import Chat, ChatCompletion, Messages, MessagesRole
from gigachat.models.chat_completions import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatMessage,
    ChatResponseFormat,
    ChatStorage,
)
from gigachat.models.response_format import JsonSchemaResponseFormat
from gigachat.settings import Settings

ModelT = TypeVar("ModelT", bound=pydantic.BaseModel)


class OffsetFile:
    """Expose the caller's current position as the multipart file origin."""

    def __init__(self, file: Any, offset: int) -> None:
        self.file = file
        self.offset = offset
        self.name = getattr(file, "name", "upload")

    def read(self, size: int = -1) -> bytes:
        return bytes(self.file.read(size))

    def tell(self) -> int:
        return int(self.file.tell()) - self.offset

    def seek(self, offset: int, whence: int = 0) -> int:
        position = self.file.seek(offset + self.offset if whence == 0 else offset, whence)
        return int(position) - self.offset


class BodyReplay:
    def __init__(self, kwargs: dict[str, Any]) -> None:
        self.files: list[tuple[Any, int]] = []
        self.replayable = True
        files = dict(kwargs.get("files") or {})
        if files:
            kwargs["files"] = files
        for name, item in files.items():
            body = item[1] if isinstance(item, tuple) else item
            if isinstance(body, (str, bytes)):
                continue
            try:
                if not body.seekable():
                    self.replayable = False
                    continue
                offset = body.tell()
                body.seek(offset)
                self.files.append((body, offset))
                wrapped = OffsetFile(body, offset)
                files[name] = (item[0], wrapped, *item[2:]) if isinstance(item, tuple) else wrapped
            except (AttributeError, OSError, ValueError):
                self.replayable = False
        content = kwargs.get("content")
        if content is not None and not isinstance(content, (str, bytes)):
            self.replayable = False

    def rewind(self) -> None:
        for body, offset in self.files:
            body.seek(offset)


# Request normalization is independent from mutable client/transport state.


def _resolve_model(model: str | None, settings: Settings) -> str:
    """Return the request or configured model, or raise if neither is set."""
    if model is not None and model.strip():
        return model

    if settings.model is not None and settings.model.strip():
        return settings.model

    raise ModelNotSpecifiedError()


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


def _parse_chat(payload: Chat | dict[str, Any] | str, settings: Settings) -> Chat:
    if isinstance(payload, str):
        chat = Chat(messages=[Messages(role=MessagesRole.USER, content=payload)])
    else:
        chat = Chat.model_validate(copy.deepcopy(payload))
    using_assistant = chat.assistant_id is not None or (
        chat.storage is not None and (chat.storage.assistant_id or chat.storage.thread_id)
    )
    if not using_assistant:
        chat.model = _resolve_model(chat.model, settings)
    if chat.profanity_check is None:
        chat.profanity_check = settings.profanity_check
    if chat.flags is None:
        chat.flags = copy.deepcopy(settings.flags)
    return chat


def _prepare_chat_for_parse(
    payload: Chat | dict[str, Any] | str,
    settings: Settings,
    response_format: type[pydantic.BaseModel],
    strict: bool,
) -> Chat:
    """Prepare a Chat object with response_format derived from *response_format*."""
    chat_data = _parse_chat(payload, settings)
    chat_data.response_format = JsonSchemaResponseFormat(schema=response_format, strict=strict)
    return chat_data


def _prepare_chat_completion_for_parse(
    payload: ChatCompletionRequest | dict[str, Any] | str,
    settings: Settings,
    response_format: type[pydantic.BaseModel],
    strict: bool,
) -> ChatCompletionRequest:
    """Prepare a primary chat completion request with a structured response schema."""
    chat_data = _parse_chat_completion(payload, settings)
    chat_data.response_format = ChatResponseFormat(type="json_schema", schema=response_format, strict=strict)
    return chat_data


def _parse_chat_completion(
    payload: ChatCompletionRequest | dict[str, Any] | str,
    settings: Settings,
) -> ChatCompletionRequest:
    if isinstance(payload, str):
        chat = ChatCompletionRequest(messages=[ChatMessage(role="user", content=payload)])
    else:
        chat = ChatCompletionRequest.model_validate(copy.deepcopy(payload))

    using_assistant = chat.assistant_id is not None or (
        isinstance(chat.storage, ChatStorage) and chat.storage.thread_id is not None
    )
    if not using_assistant:
        chat.model = _resolve_model(chat.model, settings)
    if chat.disable_filter is None and settings.profanity_check is not None:
        chat.disable_filter = not settings.profanity_check
    if chat.flags is None:
        chat.flags = copy.deepcopy(settings.flags)
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


def _build_access_token(token: Token) -> AccessToken:
    return AccessToken(
        access_token=token.tok,
        expires_at=token.exp * 1000 if 0 < token.exp < 100_000_000_000 else token.exp,
        x_headers=token.x_headers,
    )
