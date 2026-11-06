"""Exercise public endpoints through the high-level executor and HTTPX2 wire contract."""

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx2
import pytest

from gigachat import GigaChat, RequestOptions
from gigachat.exceptions import APIConnectionError, APIResponseValidationError, ResponseError

FILE = {
    "id": "file",
    "object": "file",
    "bytes": 3,
    "created_at": 1,
    "filename": "output.jsonl",
    "purpose": "general",
    "access_policy": "private",
    "modalities": ["text"],
}
BATCH = {
    "id": "batch",
    "method": "chat_completions",
    "request_counts": {"total": 2},
    "status": "created",
    "created_at": 1,
    "updated_at": 2,
}
CASES = [
    (
        "rerank",
        {
            "model": "ranker",
            "input_": [{"query": "q", "documents": ["a", "b"]}],
            "include_documents": False,
            "options": {"extension": {}},
        },
        "/rerank",
        "POST",
        {
            "model": "ranker",
            "input": [{"query": "q", "documents": ["a", "b"]}],
            "include_documents": False,
            "options": {"extension": {}},
        },
        {
            "object": "list",
            "model": "ranker",
            "data": [{"object": "ranking", "index": 0, "usage": {"prompt_tokens": 3}, "ranking": [{"doc_index": 1}]}],
        },
    ),
    (
        "update_file_access",
        {"file_ids": ["file"], "access_policy": "private"},
        "/files/access",
        "POST",
        {"file_ids": ["file"], "access_policy": "private"},
        {"data": [FILE]},
    ),
    (
        "functions_validate",
        {"function": {"name": "lookup", "parameters": {"type": "object"}}},
        "/functions/validate",
        "POST",
        {"name": "lookup", "parameters": {"type": "object"}},
        {
            "status": 200,
            "message": "Invalid schema",
            "errors": [{"description": "Missing description", "path": ["description"], "future": {"detail": 1}}],
            "warnings": [],
        },
    ),
    (
        "functions_generate",
        {"input_": "Generate a lookup function", "model": "m"},
        "/functions/generate",
        "POST",
        {"input": "Generate a lookup function", "model": "m"},
        {"finish_reason": "blacklist", "content": "Generation refused"},
    ),
    (
        "functions_rank",
        {
            "messages": [{"role": "user", "content": "q"}],
            "functions": [{"name": "lookup"}],
            "options": {"mode": "auto", "top_n": 1, "embedder_model": "e"},
        },
        "/functions/rank",
        "POST",
        {
            "messages": [{"role": "user", "content": "q"}],
            "functions": [{"name": "lookup"}],
            "options": {"mode": "auto", "top_n": 1, "embedder_model": "e"},
        },
        {"functions": [{"name": "lookup"}]},
    ),
    (
        "instructions_generate",
        {"input_": "Write instructions", "model": "m"},
        "/instructions/generate",
        "POST",
        {"input": "Write instructions", "model": "m"},
        {"finish_reason": "error", "content": "Try later"},
    ),
    ("create_batch", {"data": b'{"input":"q"}\n', "method": "embedder"}, "/batches", "POST", b'{"input":"q"}\n', BATCH),
    (
        "get_batches",
        {"batch_id": "batch"},
        "/batches",
        "GET",
        None,
        {
            "batches": [
                {
                    **BATCH,
                    "status": "future_status",
                    "request_counts": {"total": 2, "completed": 1, "failed": 1},
                    "output_file_id": "file",
                }
            ]
        },
    ),
    (
        "share",
        {"thread_id": "thread"},
        "/threads/share",
        "POST",
        {"thread_id": "thread"},
        {"shared_thread_id": "copy", "link": "https://example.org/shared/copy"},
    ),
]


async def invoke(sdk: GigaChat, mode: str, method: str, kwargs: dict[str, Any]) -> Any:
    if method == "share":
        resource = sdk.a_threads if mode == "async" else sdk.threads
        result: Any = resource.share(**kwargs)
    else:
        result = getattr(sdk, ("a" if mode == "async" else "") + method)(**kwargs)
    return await result if mode == "async" else result


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("encoding", ["json", "yaml"])
@pytest.mark.parametrize("findings", [None, "warnings", "errors"])
async def test_function_validation_numeric_status_with_warnings(mode: str, encoding: str, findings: str | None) -> None:
    payload = {
        "status": 200,
        "message": "Function is valid",
        "json_ai_rules_version": "1.0.6",
        "warnings": [
            {
                "description": "Value is null but should be object",
                "schema_location": "#/properties/return_parameters",
            },
            {
                "description": "Value is null but should be array",
                "schema_location": "#/properties/few_shot_examples",
            },
        ],
    }
    warnings = payload.pop("warnings")
    if findings is not None:
        payload[findings] = warnings
    payload["openapi_ai_rules_version"] = "1.0"
    function = {
        "name": "get_weather",
        "description": "Get weather for a city.",
        "parameters": {"type": "object", "properties": {"city": {"type": "string"}}, "required": ["city"]},
    }

    def handler(request: httpx2.Request) -> httpx2.Response:
        if encoding == "json":
            assert json.loads(request.content) == function
        else:
            assert request.content == b"openapi: 3.0.0\ninfo: {}\n"
        return httpx2.Response(200, json=payload, headers={"X-Request-ID": "validation-with-warnings"})

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as sync:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as async_:
            async with GigaChat(
                base_url="https://example.test/v1", access_token="token", http_client=sync, async_http_client=async_
            ) as sdk:
                result = await invoke(
                    sdk,
                    mode,
                    "functions_validate",
                    {"function": function if encoding == "json" else b"openapi: 3.0.0\ninfo: {}\n"},
                )

    assert type(result.status) is int
    assert result.status == 200
    assert result.request_id == "validation-with-warnings"
    assert result.model_dump(exclude_none=True, exclude={"x_headers"}) == payload


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize(("name", "kwargs", "path", "verb", "body", "payload"), CASES)
async def test_open_endpoint_contract(
    mode: str, name: str, kwargs: dict[str, Any], path: str, verb: str, body: Any, payload: dict[str, Any]
) -> None:
    captured: list[httpx2.Request] = []

    def handler(request: httpx2.Request) -> httpx2.Response:
        captured.append(request)
        return httpx2.Response(200, json=payload, headers={"X-Request-ID": "response-id"})

    options = RequestOptions(
        extra_headers={"x-contract": "call"},
        extra_query=[("tag", "one"), ("tag", "two")],
        extra_body={"provider_extension": {}} if isinstance(body, dict) else None,
    )
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as sync:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as async_:
            sdk = GigaChat(
                base_url="https://example.org/api/v1", access_token="token", http_client=sync, async_http_client=async_
            )
            result = await invoke(sdk, mode, name, {**kwargs, "request_options": options})
            assert result.request_id == "response-id"
            (request,) = captured
            assert request.url.path == "/api/v1" + path
            assert request.method == verb
            assert request.headers["authorization"] == "Bearer token"
            assert request.headers["x-contract"] == "call"
            assert request.url.params.get_list("tag") == ["one", "two"]
            if isinstance(body, dict):
                assert request.headers["content-type"] == "application/json"
                assert json.loads(request.content) == {**body, "provider_extension": {}}
            elif isinstance(body, bytes):
                assert request.content == body
                assert request.headers["content-type"] == "application/octet-stream"
                assert request.url.params["method"] == "embedder"
            else:
                assert request.url.params["batch_id"] == "batch"
                assert not request.content
            if name == "functions_validate":
                assert result.errors[0].model_extra["future"] == {"detail": 1}
            if name == "rerank":
                assert result.data[0].ranking[0].score is None
                assert result.data[0].ranking[0].document is None
            if name == "get_batches":
                assert result.batches[0].status == "future_status"
            sdk.close()
            await sdk.aclose()
            assert not sync.is_closed
            assert not async_.is_closed


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("status", [204, 302, 400, 401, 429, 500])
@pytest.mark.parametrize(("name", "kwargs", "path", "verb", "body", "payload"), CASES)
async def test_endpoint_status_contract(
    mode: str, status: int, name: str, kwargs: dict[str, Any], path: str, verb: str, body: Any, payload: dict[str, Any]
) -> None:
    calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        return httpx2.Response(status, json=payload, headers={"x-request-id": "status-id"})

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as sync:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as async_:
            sdk = GigaChat(base_url="https://example.org/v1", http_client=sync, async_http_client=async_)
            with pytest.raises(ResponseError) as caught:
                await invoke(sdk, mode, name, kwargs)
            assert caught.value.status_code == status
            assert caught.value.request_id == "status-id"
            assert calls == 1


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("kind", ["yaml", "batch"])
@pytest.mark.parametrize("override_content_type", [False, True])
async def test_raw_body_rejects_json_extra_body(mode: str, kind: str, override_content_type: bool) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        pytest.fail("Invalid raw-body options must be rejected before sending")

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as sync:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as async_:
            sdk = GigaChat(base_url="https://example.org/v1", http_client=sync, async_http_client=async_)
            kwargs: dict[str, Any] = {
                "request_options": RequestOptions(
                    extra_body={"extension": True},
                    extra_headers={"Content-Type": "application/json"} if override_content_type else None,
                )
            }
            if kind == "yaml":
                name = "functions_validate"
                kwargs["function"] = '{"openapi":"3.0.0"}'
            else:
                name = "create_batch"
                kwargs.update(data=b'{"input":"q"}\n', method="embedder")
            with pytest.raises(ValueError, match="JSON"):
                await invoke(sdk, mode, name, kwargs)


@pytest.mark.parametrize("mode", ["sync", "async"])
async def test_validate_raw_yaml(mode: str) -> None:
    yaml = b"openapi: 3.0.0\ninfo: {}\n"

    def handler(request: httpx2.Request) -> httpx2.Response:
        assert request.content == yaml
        assert request.headers["content-type"] == "application/x-yaml"
        return httpx2.Response(200, json={"status": 200, "message": "OK"})

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as sync:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as async_:
            sdk = GigaChat(base_url="https://example.org/v1", http_client=sync, async_http_client=async_)
            result = await invoke(sdk, mode, "functions_validate", {"function": yaml})
            assert result.status == 200


@pytest.mark.parametrize("mode", ["sync", "async"])
@pytest.mark.parametrize("streamed", [False, True])
async def test_batch_ambiguous_failure_is_not_replayed(mode: str, streamed: bool) -> None:
    calls = 0

    def handler(request: httpx2.Request) -> httpx2.Response:
        nonlocal calls
        calls += 1
        assert request.content == b'{"input":"q"}\n'
        raise httpx2.ReadError("response lost", request=request)

    async def parts() -> AsyncIterator[bytes]:
        yield b'{"input":'
        yield b'"q"}\n'

    data: Any = b'{"input":"q"}\n'
    if streamed:
        data = parts() if mode == "async" else iter([b'{"input":', b'"q"}\n'])
    with httpx2.Client(transport=httpx2.MockTransport(handler)) as sync:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as async_:
            sdk = GigaChat(base_url="https://example.org/v1", http_client=sync, async_http_client=async_, max_retries=3)
            with pytest.raises(APIConnectionError):
                await invoke(sdk, mode, "create_batch", {"data": data, "method": "embedder"})
            assert calls == 1


@pytest.mark.parametrize("mode", ["sync", "async"])
async def test_invalid_endpoint_response_has_metadata(mode: str) -> None:
    def handler(request: httpx2.Request) -> httpx2.Response:
        return httpx2.Response(200, json={"batches": "invalid"}, headers={"x-request-id": "invalid-id"})

    with httpx2.Client(transport=httpx2.MockTransport(handler)) as sync:
        async with httpx2.AsyncClient(transport=httpx2.MockTransport(handler)) as async_:
            sdk = GigaChat(base_url="https://example.org/v1", http_client=sync, async_http_client=async_)
            with pytest.raises(APIResponseValidationError) as caught:
                await invoke(sdk, mode, "get_batches", {})
            assert caught.value.request_id == "invalid-id"
            assert caught.value.__cause__ is not None
