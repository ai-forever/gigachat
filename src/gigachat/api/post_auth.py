import base64
import binascii
import logging
import uuid
from typing import Any, Dict, Optional

import httpx

from gigachat.api.utils import USER_AGENT, build_response
from gigachat.models import AccessToken

_logger = logging.getLogger(__name__)


def _get_kwargs(
    *, url: str, credentials: str, scope: str, custom_headers: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Bearer {credentials}",
        "RqUID": str(uuid.uuid4()),
        "User-Agent": USER_AGENT,
    }
    if custom_headers:
        headers.update(custom_headers)
    return {
        "method": "POST",
        "url": url,
        "data": {"scope": scope},
        "headers": headers,
    }


def _validate_credentials(credentials: str) -> None:
    try:
        base64.b64decode(credentials, validate=True)
    except (ValueError, binascii.Error):
        _logger.warning(
            "Invalid credentials format. Please use only base64 credentials (Authorization data, not client secret!)"
        )


def sync(
    client: httpx.Client, *, url: str, credentials: str, scope: str, custom_headers: Optional[Dict[str, str]] = None
) -> AccessToken:
    _validate_credentials(credentials)
    kwargs = _get_kwargs(url=url, credentials=credentials, scope=scope, custom_headers=custom_headers)
    response = client.request(**kwargs)
    return build_response(response, AccessToken)


async def asyncio(
    client: httpx.AsyncClient,
    *,
    url: str,
    credentials: str,
    scope: str,
    custom_headers: Optional[Dict[str, str]] = None,
) -> AccessToken:
    _validate_credentials(credentials)
    kwargs = _get_kwargs(url=url, credentials=credentials, scope=scope, custom_headers=custom_headers)
    response = await client.request(**kwargs)
    return build_response(response, AccessToken)
