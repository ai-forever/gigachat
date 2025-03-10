from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.models import UploadedFile


def _get_kwargs(
    *,
    file: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    headers = build_headers(access_token)

    return {
        "method": "GET",
        "url": f"/files/{file}",
        "headers": headers,
    }


def sync(
    client: httpx.Client,
    *,
    file: str,
    access_token: Optional[str] = None,
) -> UploadedFile:
    """Возвращает объект с описанием указанного файла."""
    kwargs = _get_kwargs(file=file, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, UploadedFile)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    file: str,
    access_token: Optional[str] = None,
) -> UploadedFile:
    """Возвращает объект с описанием указанного файла."""
    kwargs = _get_kwargs(file=file, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, UploadedFile)
