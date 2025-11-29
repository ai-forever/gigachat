import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.api import models
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
from gigachat.exceptions import AuthenticationError, BadRequestError
from gigachat.models import Model, Models

from ....utils import get_json

BASE_URL = "http://testserver/api"
MODEL_URL = f"{BASE_URL}/models/model"
MODELS_URL = f"{BASE_URL}/models"

MODEL = get_json("model.json")
MODELS = get_json("models.json")


def test_get_model_kwargs_context_vars() -> None:
    token_authorization_cvar = authorization_cvar.set("authorization_cvar")
    token_request_id_cvar = request_id_cvar.set("request_id_cvar")
    token_session_id_cvar = session_id_cvar.set("session_id_cvar")
    token_service_id_cvar = service_id_cvar.set("service_id_cvar")
    token_operation_id_cvar = operation_id_cvar.set("operation_id_cvar")
    token_trace_id_cvar = trace_id_cvar.set("trace_id_cvar")
    token_agent_id_cvar = agent_id_cvar.set("agent_id_cvar")
    token_custom_headers_cvar = custom_headers_cvar.set({"custom_headers_cvar": "val"})
    token_chat_url_cvar = chat_url_cvar.set("/chat/completions")

    assert models._get_model_kwargs(model="model")

    authorization_cvar.reset(token_authorization_cvar)
    request_id_cvar.reset(token_request_id_cvar)
    session_id_cvar.reset(token_session_id_cvar)
    service_id_cvar.reset(token_service_id_cvar)
    operation_id_cvar.reset(token_operation_id_cvar)
    trace_id_cvar.reset(token_trace_id_cvar)
    agent_id_cvar.reset(token_agent_id_cvar)
    custom_headers_cvar.reset(token_custom_headers_cvar)
    chat_url_cvar.reset(token_chat_url_cvar)


def test_get_model_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    with httpx.Client(base_url=BASE_URL) as client:
        response = models.get_model_sync(client, model="model")

    assert isinstance(response, Model)


def test_get_model_sync_value_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json={})

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ValueError, match="3 validation errors for Model*"):
            models.get_model_sync(client, model="model")


def test_get_model_sync_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, status_code=401)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(AuthenticationError):
            models.get_model_sync(client, model="model")


def test_get_model_sync_response_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, status_code=400)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(BadRequestError) as exc_info:
            models.get_model_sync(client, model="model")

    assert exc_info.value.status_code == 400
    assert str(exc_info.value.url) == MODEL_URL


def test_get_model_sync_headers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    with httpx.Client(base_url=BASE_URL) as client:
        response = models.get_model_sync(
            client,
            model="model",
            access_token="access_token",
        )

    assert isinstance(response, Model)


@pytest.mark.asyncio()
async def test_get_model_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODEL_URL, json=MODEL)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await models.get_model_async(client, model="model")

    assert isinstance(response, Model)


def test_get_models_kwargs_context_vars() -> None:
    token_authorization_cvar = authorization_cvar.set("authorization_cvar")
    token_request_id_cvar = request_id_cvar.set("request_id_cvar")
    token_session_id_cvar = session_id_cvar.set("session_id_cvar")
    token_service_id_cvar = service_id_cvar.set("service_id_cvar")
    token_operation_id_cvar = operation_id_cvar.set("operation_id_cvar")
    token_trace_id_cvar = trace_id_cvar.set("trace_id_cvar")
    token_agent_id_cvar = agent_id_cvar.set("agent_id_cvar")
    token_custom_headers_cvar = custom_headers_cvar.set({"custom_headers_cvar": "val"})
    token_chat_url_cvar = chat_url_cvar.set("/chat/completions")

    assert models._get_models_kwargs()

    authorization_cvar.reset(token_authorization_cvar)
    request_id_cvar.reset(token_request_id_cvar)
    session_id_cvar.reset(token_session_id_cvar)
    service_id_cvar.reset(token_service_id_cvar)
    operation_id_cvar.reset(token_operation_id_cvar)
    trace_id_cvar.reset(token_trace_id_cvar)
    agent_id_cvar.reset(token_agent_id_cvar)
    custom_headers_cvar.reset(token_custom_headers_cvar)
    chat_url_cvar.reset(token_chat_url_cvar)


def test_get_models_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    with httpx.Client(base_url=BASE_URL) as client:
        response = models.get_models_sync(client)

    assert isinstance(response, Models)


def test_get_models_sync_value_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json={})

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ValueError, match="2 validation errors for Models*"):
            models.get_models_sync(client)


def test_get_models_sync_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, status_code=401)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(AuthenticationError):
            models.get_models_sync(client)


def test_get_models_sync_response_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, status_code=400)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(BadRequestError) as exc_info:
            models.get_models_sync(client)

    assert exc_info.value.status_code == 400
    assert str(exc_info.value.url) == MODELS_URL


def test_get_models_sync_headers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    with httpx.Client(base_url=BASE_URL) as client:
        response = models.get_models_sync(
            client,
            access_token="access_token",
        )

    assert isinstance(response, Models)


@pytest.mark.asyncio()
async def test_get_models_async(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await models.get_models_async(client)

    assert isinstance(response, Models)
