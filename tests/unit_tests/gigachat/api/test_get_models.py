import httpx
import pytest
from pytest_httpx import HTTPXMock

from gigachat.api import get_models
from gigachat.context import authorization_cvar, operation_id_cvar, request_id_cvar, service_id_cvar, session_id_cvar
from gigachat.exceptions import AuthenticationError, ResponseError
from gigachat.models import Models

from ....utils import get_json

BASE_URL = "http://testserver/api"
MODELS_URL = f"{BASE_URL}/models"

MODELS = get_json("models.json")


def test__kwargs_context_vars() -> None:
    token_authorization_cvar = authorization_cvar.set("authorization_cvar")
    token_request_id_cvar = request_id_cvar.set("request_id_cvar")
    token_session_id_cvar = session_id_cvar.set("session_id_cvar")
    token_service_id_cvar = service_id_cvar.set("service_id_cvar")
    token_operation_id_cvar = operation_id_cvar.set("operation_id_cvar")

    assert get_models._get_kwargs()

    authorization_cvar.reset(token_authorization_cvar)
    request_id_cvar.reset(token_request_id_cvar)
    session_id_cvar.reset(token_session_id_cvar)
    service_id_cvar.reset(token_service_id_cvar)
    operation_id_cvar.reset(token_operation_id_cvar)


def test_sync(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_models.sync(client)

    assert isinstance(response, Models)


def test_sync_value_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json={})

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ValueError, match="2 validation errors for Models*"):
            get_models.sync(client)


def test_sync_authentication_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, status_code=401)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(AuthenticationError):
            get_models.sync(client)


def test_sync_response_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, status_code=400)

    with httpx.Client(base_url=BASE_URL) as client:
        with pytest.raises(ResponseError):
            get_models.sync(client)


def test_sync_headers(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    with httpx.Client(base_url=BASE_URL) as client:
        response = get_models.sync(
            client,
            access_token="access_token",
        )

    assert isinstance(response, Models)


@pytest.mark.asyncio()
async def test_asyncio(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(url=MODELS_URL, json=MODELS)

    async with httpx.AsyncClient(base_url=BASE_URL) as client:
        response = await get_models.asyncio(client)

    assert isinstance(response, Models)
