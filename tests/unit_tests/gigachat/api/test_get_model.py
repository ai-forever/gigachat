import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.api import get_model
from gigachat.context import (
    agent_id_cvar,
    authorization_cvar,
    chat_url_cvar,
    custom_headers_cvar,
    operation_id_cvar,
    request_id_cvar,
    service_id_cvar,
    session_id_cvar,
    trace_id_cvar,
)
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Model

from ....utils import get_json

BASE_URL = "http://testserver/api"
MODEL_URL = f"{BASE_URL}/models/model"

MODEL = get_json("model.json")


def test__kwargs_context_vars() -> None:
    token_authorization_cvar = authorization_cvar.set("authorization_cvar")
    token_request_id_cvar = request_id_cvar.set("request_id_cvar")
    token_session_id_cvar = session_id_cvar.set("session_id_cvar")
    token_service_id_cvar = service_id_cvar.set("service_id_cvar")
    token_operation_id_cvar = operation_id_cvar.set("operation_id_cvar")
    token_trace_id_cvar = trace_id_cvar.set("trace_id_cvar")
    token_agent_id_cvar = agent_id_cvar.set("agent_id_cvar")
    token_custom_headers_cvar = custom_headers_cvar.set({"custom_headers_cvar": "val"})
    token_chat_url_cvar = chat_url_cvar.set("/chat/completions")

    assert get_model._get_kwargs(model="model")

    authorization_cvar.reset(token_authorization_cvar)
    request_id_cvar.reset(token_request_id_cvar)
    session_id_cvar.reset(token_session_id_cvar)
    service_id_cvar.reset(token_service_id_cvar)
    operation_id_cvar.reset(token_operation_id_cvar)
    trace_id_cvar.reset(token_trace_id_cvar)
    agent_id_cvar.reset(token_agent_id_cvar)
    custom_headers_cvar.reset(token_custom_headers_cvar)
    chat_url_cvar.reset(token_chat_url_cvar)


def test_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_model.sync(client, model="model")

    assert isinstance(response, Model)


def test_sync_value_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json={})

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ValueError, match="3 validation errors for Model*"):
            get_model.sync(client, model="model")


def test_sync_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, status_code=401)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(AuthenticationError):
            get_model.sync(client, model="model")


def test_sync_response_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, status_code=400)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ResponseError):
            get_model.sync(client, model="model")


def test_sync_headers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_model.sync(
            client,
            model="model",
            access_token="access_token",
        )

    assert isinstance(response, Model)


@pytest.mark.asyncio()
async def test_asyncio(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_model.asyncio(client, model="model")

    assert isinstance(response, Model)
