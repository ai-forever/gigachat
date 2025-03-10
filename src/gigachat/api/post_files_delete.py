from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import build_headers, build_response
from gigachat.models import DeletedFile


def _get_kwargs(
    *,
    file: str,
    access_token: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "method": "POST",
        "url": f"/files/{file}/delete",
        "files": {"file": file},
        "data": {},
        "headers": build_headers(access_token),
    }


def sync(
    client: httpx.Client,
    *,
    file: str,
    access_token: Optional[str] = None,
) -> DeletedFile:
    kwargs = _get_kwargs(file=file, access_token=access_token)
    response = client.request(**kwargs)
    return build_response(response, DeletedFile)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    file: str,
    access_token: Optional[str] = None,
) -> DeletedFile:
    kwargs = _get_kwargs(file=file, access_token=access_token)
    response = await client.request(**kwargs)
    return build_response(response, DeletedFile)
