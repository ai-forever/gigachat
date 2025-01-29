from typing import Any, Dict, Literal, Optional

import httpx

from gigachat._types import FileTypes
from gigachat.api.utils import build_headers, build_response
from gigachat.models import UploadedFile


def _get_kwargs(
    *,
    file: FileTypes,
    purpose: Literal["general", "assistant"] = "general",
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "POST",
        "url": "/files",
        "files": {"file": file},
        "data": {"purpose": purpose},
        "headers": headers,
    }


def sync(
    client: httpx.Client,
    *,
    file: FileTypes,
    purpose: Literal["general", "assistant"] = "general",
    access_token: Optional[str] = None,
) -> UploadedFile:
    kwargs = _get_kwargs(file=file, purpose=purpose, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, UploadedFile)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    file: FileTypes,
    purpose: Literal["general", "assistant"] = "general",
    access_token: Optional[str] = None,
) -> UploadedFile:
    kwargs = _get_kwargs(file=file, purpose=purpose, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, UploadedFile)
