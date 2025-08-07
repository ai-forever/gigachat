import json
from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.context import chat_url_cvar
from gigachat.models import Chat, ChatCompletion


def _get_kwargs(
    *,
    chat: Chat,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)
    headers["Content-Type"] = "application/json"
    json_data = chat.dict(exclude_none=True, by_alias=True, exclude={"stream"})
    fields = json_data.pop("additional_fields", None)

    if fields:
        json_data = {**json_data, **fields}
    return {
        "method": "POST",
        "url": chat_url_cvar.get(),
        "content": json.dumps(json_data, ensure_ascii=False),
        "headers": headers,
    }


def sync(
    client: httpx.Client,
    *,
    chat: Chat,
    access_token: Optional[str] = None,
) -> ChatCompletion:
    kwargs = _get_kwargs(chat=chat, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, ChatCompletion)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    chat: Chat,
    access_token: Optional[str] = None,
) -> ChatCompletion:
    kwargs = _get_kwargs(chat=chat, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, ChatCompletion)
