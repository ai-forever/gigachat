import base64
import binascii
import json
import logging
import uuid
from http import HTTPStatus
from typing import Any

import httpx2 as httpx
from pydantic import ValidationError

from gigachat._core.execution import request_async, request_sync
from gigachat.api.utils import (
    USER_AGENT,
    _raise_for_status,
    build_x_headers,
    execute_request_async,
    execute_request_sync,
)
from gigachat.exceptions import APIResponseValidationError
from gigachat.models.auth import AccessToken, Token

logger = logging.getLogger(__name__)


def _get_auth_kwargs(*, url: str, credentials: str, scope: str) -> dict[str, Any]:
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
        try:
            json_data = response.json()
            if "tok" in json_data:
                return AccessToken(
                    x_headers=build_x_headers(response), access_token=json_data["tok"], expires_at=json_data["exp"]
                )
            else:
                return AccessToken(x_headers=build_x_headers(response), **json_data)
        except (ValidationError, json.JSONDecodeError, KeyError, TypeError) as exc:
            raise APIResponseValidationError(
                "Invalid OAuth response", request_id=response.headers.get("x-request-id")
            ) from exc
    else:
        _raise_for_status(response.url, response.status_code, response.content, response.headers)


def auth_sync(client: httpx.Client, *, url: str, credentials: str, scope: str) -> AccessToken:
    """Return an access token."""
    _validate_credentials(credentials)
    kwargs = _get_auth_kwargs(url=url, credentials=credentials, scope=scope)
    response = request_sync(client, **kwargs)
    return _build_auth_response(response)


async def auth_async(client: httpx.AsyncClient, *, url: str, credentials: str, scope: str) -> AccessToken:
    """Return an access token."""
    _validate_credentials(credentials)
    kwargs = _get_auth_kwargs(url=url, credentials=credentials, scope=scope)
    response = await request_async(client, **kwargs)
    return _build_auth_response(response)


def _get_token_kwargs(
    *,
    user: str,
    password: str,
    url: str = "/token",
) -> dict[str, Any]:
    headers = {"User-Agent": USER_AGENT}

    return {
        "method": "POST",
        "url": url,
        "auth": (user, password),
        "headers": headers,
    }


def token_sync(
    client: httpx.Client,
    *,
    user: str,
    password: str,
    url: str = "/token",
) -> Token:
    """Return a token."""
    kwargs = _get_token_kwargs(user=user, password=password, url=url)
    return execute_request_sync(client, kwargs, Token)


async def token_async(
    client: httpx.AsyncClient,
    *,
    user: str,
    password: str,
    url: str = "/token",
) -> Token:
    """Return a token."""
    kwargs = _get_token_kwargs(user=user, password=password, url=url)
    return await execute_request_async(client, kwargs, Token)


def _build_access_token(token: Token) -> AccessToken:
    return AccessToken(
        access_token=token.tok,
        expires_at=token.exp * 1000 if 0 < token.exp < 100_000_000_000 else token.exp,
        x_headers=token.x_headers,
    )
