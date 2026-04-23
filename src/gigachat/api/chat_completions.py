import json
from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers, execute_request_sync
from gigachat.context import chat_completions_url_cvar
from gigachat.models.chat_completions import ChatCompletionRequest, ChatCompletionResponse


def _build_request_json(chat: ChatCompletionRequest) -> Dict[str, Any]:
    """Serialize *chat* to a JSON-ready dict."""
    return chat.model_dump(exclude_none=True, by_alias=True, exclude={"stream"})


def _get_chat_kwargs(
    *,
    chat: ChatCompletionRequest,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    headers["Content-Type"] = "application/json"

    return {
        "method": "POST",
        "url": chat_completions_url_cvar.get(),
        "content": json.dumps(_build_request_json(chat), ensure_ascii=False),
        "headers": headers,
    }


def chat_sync(
    client: httpx.Client,
    *,
    chat: ChatCompletionRequest,
    access_token: Optional[str] = None,
) -> ChatCompletionResponse:
    """Return a primary chat completion based on the provided messages."""
    kwargs = _get_chat_kwargs(chat=chat, access_token=access_token)
    return execute_request_sync(client, kwargs, ChatCompletionResponse)


__all__ = [
    "_build_request_json",
    "_get_chat_kwargs",
    "chat_sync",
]
