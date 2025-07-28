import base64
import binascii
import logging
import uuid
from http import HTTPStatus
from typing import Any, Dict

import httpx

from gigachat.api.utils import USER_AGENT, build_x_headers
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import AccessToken

_logger = logging.getLogger(__name__)


def _get_kwargs(*, url: str, credentials: str, scope: str) -> Dict[str, Any]:
    headers = {
        "Authorization": f"Basic {credentials}",
        "RqUID": str(uuid.uuid4()),
        "User-Agent": USER_AGENT,
    }
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


def build_response(response: httpx.Response) -> AccessToken:
    if response.status_code == HTTPStatus.OK:
        json_data = response.json()
        if "tok" in json_data:
            return AccessToken(
                x_headers=build_x_headers(response), access_token=json_data["tok"], expires_at=json_data["exp"]
            )
        else:
            return AccessToken(x_headers=build_x_headers(response), **json_data)
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)


def sync(client: httpx.Client, *, url: str, credentials: str, scope: str) -> AccessToken:
    _validate_credentials(credentials)
    kwargs = _get_kwargs(url=url, credentials=credentials, scope=scope)
    response = client.request(**kwargs)
    return build_response(response)


async def asyncio(client: httpx.AsyncClient, *, url: str, credentials: str, scope: str) -> AccessToken:
    _validate_credentials(credentials)
    kwargs = _get_kwargs(url=url, credentials=credentials, scope=scope)
    response = await client.request(**kwargs)
    return build_response(response)
