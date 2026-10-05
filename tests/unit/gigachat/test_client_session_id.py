from typing import Optional

import pytest
from pytest_httpx import HTTPXMock

from gigachat.client import GigaChat, GigaChatAsyncClient, GigaChatSyncClient, _get_auth_kwargs
from gigachat.context import custom_headers_cvar, session_id_cvar
from gigachat.settings import Settings
from tests.constants import BASE_URL, CHAT_COMPLETION, CHAT_URL


@pytest.mark.parametrize("client_class", [GigaChat, GigaChatSyncClient, GigaChatAsyncClient])
def test_session_id_constructor_overrides_environment(client_class: type, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GIGACHAT_SESSION_ID", "environment-session")
    assert client_class()._settings.session_id == "environment-session"
    assert client_class(session_id="client-session")._settings.session_id == "client-session"


@pytest.mark.parametrize(
    ("session_id", "context_id", "custom_id", "expected"),
    [
        (None, None, None, None),
        ("client-session", None, None, "client-session"),
        ("client-session", "context-session", None, "context-session"),
        ("client-session", "context-session", "custom-session", "custom-session"),
    ],
)
@pytest.mark.parametrize("primary", [False, True])
async def test_session_id_headers_sync_and_async(
    httpx_mock: HTTPXMock,
    session_id: Optional[str],
    context_id: Optional[str],
    custom_id: Optional[str],
    expected: Optional[str],
    primary: bool,
) -> None:
    response = {"messages": [{"role": "assistant", "content": "ok"}]} if primary else CHAT_COMPLETION
    for _ in range(2):
        httpx_mock.add_response(url=CHAT_URL, json=response)
    session_token = session_id_cvar.set(context_id)
    custom_token = custom_headers_cvar.set({"X-Session-ID": custom_id} if custom_id else None)
    try:
        with GigaChatSyncClient(base_url=BASE_URL, model="model", session_id=session_id) as client:
            if primary:
                client.chat.create("hello")
            else:
                client.chat("hello")
        async with GigaChatAsyncClient(base_url=BASE_URL, model="model", session_id=session_id) as async_client:
            if primary:
                await async_client.achat.create("hello")
            else:
                await async_client.achat("hello")
    finally:
        custom_headers_cvar.reset(custom_token)
        session_id_cvar.reset(session_token)
    for request in httpx_mock.get_requests():
        assert request.headers.get("X-Session-ID") == expected


def test_session_id_is_scoped_to_client_and_not_oauth(httpx_mock: HTTPXMock) -> None:
    for _ in range(2):
        httpx_mock.add_response(url=CHAT_URL, json=CHAT_COMPLETION)
    for session_id in ("session-one", "session-two"):
        with GigaChat(base_url=BASE_URL, model="model", session_id=session_id) as client:
            client.chat("hello")
    assert [request.headers["X-Session-ID"] for request in httpx_mock.get_requests()] == [
        "session-one",
        "session-two",
    ]
    assert "headers" not in _get_auth_kwargs(Settings(session_id="api-only"))
