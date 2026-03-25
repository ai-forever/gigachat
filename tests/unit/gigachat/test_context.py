from gigachat.context import (
    agent_id_cvar,
    authorization_cvar,
    chat_url_cvar,
    chat_v2_url_cvar,
    client_id_cvar,
    custom_headers_cvar,
    operation_id_cvar,
    request_id_cvar,
    service_id_cvar,
    session_id_cvar,
    trace_id_cvar,
)


def test_default_values() -> None:
    assert authorization_cvar.get() is None
    assert client_id_cvar.get() is None
    assert request_id_cvar.get() is None
    assert session_id_cvar.get() is None
    assert service_id_cvar.get() is None
    assert operation_id_cvar.get() is None
    assert trace_id_cvar.get() is None
    assert agent_id_cvar.get() is None
    assert custom_headers_cvar.get() is None
    assert chat_url_cvar.get() == "/chat/completions"
    assert chat_v2_url_cvar.get() is None


def test_set_values() -> None:
    authorization_token = authorization_cvar.set("token")
    client_id_token = client_id_cvar.set("client_id")
    request_id_token = request_id_cvar.set("request_id")
    session_id_token = session_id_cvar.set("session_id")
    service_id_token = service_id_cvar.set("service_id")
    operation_id_token = operation_id_cvar.set("operation_id")
    trace_id_token = trace_id_cvar.set("trace_id")
    agent_id_token = agent_id_cvar.set("agent_id")
    custom_headers_token = custom_headers_cvar.set({"header": "value"})
    chat_url_token = chat_url_cvar.set("/new/url")
    chat_v2_url_token = chat_v2_url_cvar.set("https://example.com/api/v2/chat/completions")

    try:
        assert authorization_cvar.get() == "token"
        assert client_id_cvar.get() == "client_id"
        assert request_id_cvar.get() == "request_id"
        assert session_id_cvar.get() == "session_id"
        assert service_id_cvar.get() == "service_id"
        assert operation_id_cvar.get() == "operation_id"
        assert trace_id_cvar.get() == "trace_id"
        assert agent_id_cvar.get() == "agent_id"
        assert custom_headers_cvar.get() == {"header": "value"}
        assert chat_url_cvar.get() == "/new/url"
        assert chat_v2_url_cvar.get() == "https://example.com/api/v2/chat/completions"
    finally:
        authorization_cvar.reset(authorization_token)
        client_id_cvar.reset(client_id_token)
        request_id_cvar.reset(request_id_token)
        session_id_cvar.reset(session_id_token)
        service_id_cvar.reset(service_id_token)
        operation_id_cvar.reset(operation_id_token)
        trace_id_cvar.reset(trace_id_token)
        agent_id_cvar.reset(agent_id_token)
        custom_headers_cvar.reset(custom_headers_token)
        chat_url_cvar.reset(chat_url_token)
        chat_v2_url_cvar.reset(chat_v2_url_token)

    assert authorization_cvar.get() is None
    assert client_id_cvar.get() is None
    assert request_id_cvar.get() is None
    assert session_id_cvar.get() is None
    assert service_id_cvar.get() is None
    assert operation_id_cvar.get() is None
    assert trace_id_cvar.get() is None
    assert agent_id_cvar.get() is None
    assert custom_headers_cvar.get() is None
    assert chat_url_cvar.get() == "/chat/completions"
    assert chat_v2_url_cvar.get() is None
