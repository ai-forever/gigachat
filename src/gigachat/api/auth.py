import base64
import binascii
import logging
import uuid
from http import HTTPStatus
from typing import Any, Dict

import httpx

from gigachat.api.utils import (
    USER_AGENT,
    _raise_for_status,
    build_headers,
    build_x_headers,
    execute_request_async,
    execute_request_sync,
)
from gigachat.models.auth import AccessToken, Token

logger = logging.getLogger(__name__)


def _get_auth_kwargs(*, url: str, credentials: str, scope: str) -> Dict[str, Any]:
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
        logger.warning(
            "Invalid credentials format. Please use only base64 credentials (Authorization data, not client secret!)"
        )


def _build_auth_response(response: httpx.Response) -> AccessToken:
    if response.status_code == HTTPStatus.OK:
        json_data = response.json()
        if "tok" in json_data:
            return AccessToken(
                x_headers=build_x_headers(response), access_token=json_data["tok"], expires_at=json_data["exp"]
            )
        else:
            return AccessToken(x_headers=build_x_headers(response), **json_data)
    else:
        _raise_for_status(response.url, response.status_code, response.content, response.headers)


def auth_sync(client: httpx.Client, *, url: str, credentials: str, scope: str) -> AccessToken:
    """Return an access token."""
    _validate_credentials(credentials)
    kwargs = _get_auth_kwargs(url=url, credentials=credentials, scope=scope)
    response = client.request(**kwargs)
    return _build_auth_response(response)


async def auth_async(client: httpx.AsyncClient, *, url: str, credentials: str, scope: str) -> AccessToken:
    """Return an access token."""
    _validate_credentials(credentials)
    kwargs = _get_auth_kwargs(url=url, credentials=credentials, scope=scope)
    response = await client.request(**kwargs)
    return _build_auth_response(response)


def _get_token_kwargs(
    *,
    user: str,
    password: str,
) -> Dict[str, Any]:
    headers = build_headers()

    return {
        "method": "POST",
        "url": "/token",
        "auth": (user, password),
        "headers": headers,
    }


def token_sync(
    client: httpx.Client,
    *,
    user: str,
    password: str,
) -> Token:
    """Return a token."""
    kwargs = _get_token_kwargs(user=user, password=password)
    return execute_request_sync(client, kwargs, Token)


async def token_async(
    client: httpx.AsyncClient,
    *,
    user: str,
    password: str,
) -> Token:
    """Return a token."""
    kwargs = _get_token_kwargs(user=user, password=password)
    return await execute_request_async(client, kwargs, Token)
