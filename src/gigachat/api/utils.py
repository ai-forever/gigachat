import logging
from http import HTTPStatus
from typing import Dict, Optional, Type, TypeVar

import httpx

from gigachat.context import (
    authorization_cvar,
    client_id_cvar,
    operation_id_cvar,
    request_id_cvar,
    service_id_cvar,
    session_id_cvar,
)
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.pydantic_v1 import BaseModel

_logger = logging.getLogger(__name__)

USER_AGENT = "GigaChat-python-lib"


def build_headers(access_token: Optional[str] = None) -> Dict[str, str]:
    headers = {}

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    headers["User-Agent"] = USER_AGENT

    authorization = authorization_cvar.get()
    session_id = session_id_cvar.get()
    request_id = request_id_cvar.get()
    service_id = service_id_cvar.get()
    operation_id = operation_id_cvar.get()
    client_id = client_id_cvar.get()

    if authorization:
        headers["Authorization"] = authorization
    if session_id:
        headers["X-Session-ID"] = session_id
    if request_id:
        headers["X-Request-ID"] = request_id
    if service_id:
        headers["X-Service-ID"] = service_id
    if operation_id:
        headers["X-Operation-ID"] = operation_id
    if client_id:
        headers["X-Client-ID"] = client_id
    return headers


T = TypeVar("T", bound=BaseModel)


def parse_chunk(line: str, model_class: Type[T]) -> Optional[T]:
    try:
        name, _, value = line.partition(": ")
        if name == "data":
            if value == "[DONE]":
                return None
            else:
                return model_class.parse_raw(value)
    except Exception as e:
        _logger.error("Error parsing chunk from server: %s, raw value: %s", e, line)
        raise e
    else:
        return None


def build_x_headers(response: httpx.Response) -> Dict[str, Optional[str]]:
    return {
        "x-request-id": response.headers.get("x-request-id"),
        "x-session-id": response.headers.get("x-session-id"),
        "x-client-id": response.headers.get("x-client-id"),
    }


def build_response(response: httpx.Response, model_class: Type[T]) -> T:
    if response.status_code == HTTPStatus.OK:
        return model_class(x_headers=build_x_headers(response), **response.json())
    elif response.status_code == HTTPStatus.UNAUTHORIZED:
        raise AuthenticationError(response.url, response.status_code, response.content, response.headers)
    else:
        raise ResponseError(response.url, response.status_code, response.content, response.headers)
