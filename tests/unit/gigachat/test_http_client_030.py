import asyncio
import gzip
import json
from collections.abc import AsyncIterator
from typing import Any, Literal, cast

import httpx2
import pytest

from gigachat import GigaChat, RequestOptions
from gigachat._http_client import DefaultAioHttpClient, DefaultAsyncHttpxClient, DefaultHttpxClient
from gigachat.exceptions import APIConnectionError
from tests.constants import MODELS


def test_native_defaults() -> None:
    with DefaultHttpxClient(trust_env=False) as client:
        assert client.timeout == httpx2.Timeout(30)
    assert DefaultAsyncHttpxClient(trust_env=False).timeout == httpx2.Timeout(30)


def test_aiohttp_rejects_unsupported_limits_and_timeouts() -> None:
    pytest.importorskip("aiohttp")
    with pytest.raises(ValueError, match="max_keepalive_connections"):
        DefaultAioHttpClient(limits=httpx2.Limits(max_keepalive_connections=1), trust_env=False)
    with pytest.raises(ValueError, match="write timeout"):
        DefaultAioHttpClient(timeout=httpx2.Timeout(5), trust_env=False)
    with pytest.raises(ValueError, match="equal connect and pool"):
        DefaultAioHttpClient(timeout=httpx2.Timeout(connect=1, read=2, write=None, pool=3), trust_env=False)
    client = DefaultAioHttpClient(timeout=5, trust_env=False)
    assert client.timeout.write is None
    request = client.build_request("GET", "https://example.com", timeout=7)
    assert request.extensions["timeout"]["write"] is None
    with pytest.raises(ValueError, match="write timeout"):
        client.build_request("GET", "https://example.com", timeout=httpx2.Timeout(7))


async def test_aiohttp_wire_stream_decompression_and_owned_session() -> None:
    pytest.importorskip("aiohttp")
    body = gzip.compress(b"hello world")

    async def serve(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await reader.readuntil(b"\r\n\r\n")
        writer.write(
            b"HTTP/1.1 200 OK\r\nContent-Encoding: gzip\r\nContent-Length: "
            + str(len(body)).encode()
            + b"\r\n\r\n"
            + body
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(serve, "127.0.0.1", 0)
    port = server.sockets[0].getsockname()[1]
    try:
        async with DefaultAioHttpClient(trust_env=False) as client:
            transport = cast(Any, client._transport)
            assert transport.session is None
            response = await client.get(f"http://127.0.0.1:{port}/")
            assert response.content == b"hello world"
            session = cast(Any, transport.session)
            assert not session.closed
        assert session.closed
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.parametrize("backend", ["httpx2", "aiohttp"])
async def test_wire_multipart_pool_limit_and_cancel(backend: str) -> None:
    pytest.importorskip("aiohttp")
    from aiohttp import web

    cls = DefaultAioHttpClient if backend == "aiohttp" else DefaultAsyncHttpxClient
    entered = asyncio.Event()
    release = asyncio.Event()
    multipart_seen = []

    async def slow(request: Any) -> Any:
        entered.set()
        await release.wait()
        return web.Response(text="done")

    async def upload(request: Any) -> Any:
        reader = await request.multipart()
        part = await reader.next()
        multipart_seen.append((part.name, part.filename, await part.read()))
        return web.Response(text="uploaded")

    app = web.Application()
    app.router.add_get("/slow", slow)
    app.router.add_post("/upload", upload)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = cast(Any, site)._server.sockets[0].getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    limits = httpx2.Limits(max_connections=1, max_keepalive_connections=None)
    try:
        async with cls(limits=limits, trust_env=False) as client:
            first = asyncio.create_task(client.get(url + "/slow"))
            await asyncio.wait_for(entered.wait(), 2)
            blocked = asyncio.create_task(client.post(url + "/upload", files={"file": ("sample.txt", b"hello")}))
            await asyncio.sleep(0.05)
            assert not blocked.done()
            blocked.cancel()
            with pytest.raises(asyncio.CancelledError):
                await blocked
            release.set()
            assert (await asyncio.wait_for(first, 2)).text == "done"
            response = await asyncio.wait_for(client.post(url + "/upload", files={"file": ("sample.txt", b"hello")}), 2)
            assert response.text == "uploaded"
            assert multipart_seen == [("file", "sample.txt", b"hello")]
    finally:
        release.set()
        await runner.cleanup()


@pytest.mark.parametrize("backend", ["httpx2", "aiohttp"])
async def test_wire_explicit_proxy_environment_and_no_proxy(backend: str, monkeypatch: pytest.MonkeyPatch) -> None:
    if backend == "aiohttp":
        pytest.importorskip("aiohttp")
    cls = DefaultAioHttpClient if backend == "aiohttp" else DefaultAsyncHttpxClient
    received = []

    async def serve(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        request = await reader.readuntil(b"\r\n\r\n")
        received.append(request.split(b"\r\n", 1)[0])
        writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok")
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    proxy = await asyncio.start_server(serve, "127.0.0.1", 0)
    origin = await asyncio.start_server(serve, "127.0.0.1", 0)
    proxy_url = f"http://127.0.0.1:{proxy.sockets[0].getsockname()[1]}"
    origin_url = f"http://127.0.0.1:{origin.sockets[0].getsockname()[1]}"
    try:
        async with cls(proxy=proxy_url, trust_env=False) as client:
            assert (await client.get("http://example.invalid/path")).text == "ok"
        assert received.pop(0) == b"GET http://example.invalid/path HTTP/1.1"
        monkeypatch.setenv("HTTP_PROXY", proxy_url)
        monkeypatch.setenv("NO_PROXY", "")
        async with cls(trust_env=True) as client:
            assert (await client.get("http://example.invalid/env")).text == "ok"
        assert received.pop(0) == b"GET http://example.invalid/env HTTP/1.1"
        monkeypatch.setenv("NO_PROXY", "127.0.0.1")
        async with cls(trust_env=True) as client:
            assert (await client.get(origin_url + "/direct")).text == "ok"
        assert received.pop(0) == b"GET /direct HTTP/1.1"
        monkeypatch.setenv("NO_PROXY", "")
        async with cls(trust_env=False) as client:
            assert (await client.get(origin_url + "/no-env")).text == "ok"
        assert received.pop(0) == b"GET /no-env HTTP/1.1"
    finally:
        proxy.close()
        origin.close()
        await proxy.wait_closed()
        await origin.wait_closed()


@pytest.mark.parametrize("backend", ["httpx2", "aiohttp"])
async def test_wire_chunked_upload_and_interrupted_stream_cleanup(backend: str) -> None:
    pytest.importorskip("aiohttp")
    from aiohttp import web

    cls = DefaultAioHttpClient if backend == "aiohttp" else DefaultAsyncHttpxClient
    received = []

    async def upload(request: Any) -> Any:
        received.append((request.headers.get("Transfer-Encoding"), await request.read()))
        return web.Response(text="ok")

    async def broken(request: Any) -> Any:
        response = web.StreamResponse(headers={"Content-Length": "100"})
        await response.prepare(request)
        await response.write(b"partial")
        request.transport.close()
        return response

    async def healthy(request: Any) -> Any:
        return web.Response(text="healthy")

    async def chunks() -> AsyncIterator[bytes]:
        yield b"one"
        yield b"two"

    app = web.Application()
    app.router.add_post("/upload", upload)
    app.router.add_get("/broken", broken)
    app.router.add_get("/healthy", healthy)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    port = cast(Any, site)._server.sockets[0].getsockname()[1]
    url = f"http://127.0.0.1:{port}"
    limits = httpx2.Limits(max_connections=1, max_keepalive_connections=None)
    try:
        async with cls(limits=limits, trust_env=False) as client:
            assert (await client.post(url + "/upload", content=chunks())).text == "ok"
            assert received == [("chunked", b"onetwo")]

            async def consume_broken() -> None:
                async with client.stream("GET", url + "/broken") as response:
                    async for _ in response.aiter_bytes():
                        pass

            with pytest.raises(httpx2.TransportError):
                await consume_broken()
            assert (await asyncio.wait_for(client.get(url + "/healthy"), 2)).text == "healthy"
    finally:
        await runner.cleanup()


async def test_aiohttp_request_timeout_modes_on_wire() -> None:
    pytest.importorskip("aiohttp")
    arrived = asyncio.Event()
    release = asyncio.Event()

    async def serve(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            await reader.readuntil(b"\r\n\r\n")
            arrived.set()
            await release.wait()
            writer.write(b"HTTP/1.1 200 OK\r\nContent-Length: 2\r\nConnection: close\r\n\r\nok")
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    server = await asyncio.start_server(serve, "127.0.0.1", 0)
    url = f"http://127.0.0.1:{server.sockets[0].getsockname()[1]}/"
    try:
        async with DefaultAioHttpClient(trust_env=False) as client:
            with pytest.raises(httpx2.ReadTimeout):
                await client.get(url, timeout=0.05)
            assert arrived.is_set()
            with pytest.raises(ValueError, match="write timeout"):
                await client.get(url, timeout=httpx2.Timeout(1))
            release.set()
            timeout = httpx2.Timeout(connect=1, read=1, write=None, pool=None)
            assert (await client.get(url, timeout=timeout)).text == "ok"
    finally:
        release.set()
        server.close()
        await server.wait_closed()


async def test_aiohttp_raw_session_injection_is_not_supported() -> None:
    aiohttp = pytest.importorskip("aiohttp")
    async with aiohttp.ClientSession() as session:
        with pytest.raises(TypeError, match="session"):
            DefaultAioHttpClient(session=session, trust_env=False)
        assert not session.closed


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf"), -float("inf")])
@pytest.mark.parametrize("field", [None, "connect", "read", "pool", "write"])
async def test_aiohttp_rejects_invalid_timeout_before_sending(value: float, field: str | None) -> None:
    pytest.importorskip("aiohttp")
    timeout = value if field is None else httpx2.Timeout(None, **{field: value})
    with pytest.raises(ValueError, match="finite and positive"):
        DefaultAioHttpClient(timeout=timeout, trust_env=False)
    async with DefaultAioHttpClient(trust_env=False) as transport:
        async with GigaChat(async_http_client=transport, access_token="fixture", trust_env=False) as client:
            with pytest.raises(ValueError, match="finite and positive"):
                await client.aget_models(request_options=RequestOptions(timeout=timeout))
        assert not transport.is_closed
        # A caller can send a pre-built Request without invoking build_request.
        extensions = {"timeout": httpx2.Timeout(timeout).as_dict()}
        with pytest.raises(ValueError, match="finite and positive"):
            await transport.send(httpx2.Request("GET", "http://example.invalid/", extensions=extensions))
        assert cast(Any, transport._transport).session is None


@pytest.mark.parametrize("timeout", [None, 1, httpx2.Timeout(connect=None, read=1, write=None, pool=None)])
async def test_aiohttp_accepts_positive_and_disabled_timeouts(timeout: Any) -> None:
    pytest.importorskip("aiohttp")
    async with DefaultAioHttpClient(timeout=timeout, trust_env=False) as client:
        request = client.build_request("GET", "http://example.invalid/", timeout=timeout)
        assert request.extensions["timeout"]["write"] is None


@pytest.mark.parametrize("backend", ["httpx2", "aiohttp"])
@pytest.mark.parametrize("max_retries", [0, 1])
@pytest.mark.parametrize("failures", [1, 2])
async def test_wire_network_retries_follow_sdk_budget(
    backend: Literal["httpx2", "aiohttp"], max_retries: int, failures: int
) -> None:
    if backend == "aiohttp":
        pytest.importorskip("aiohttp")
    requests = 0

    async def serve(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        nonlocal requests
        try:
            await reader.readuntil(b"\r\n\r\n")
            requests += 1
            if requests > failures:
                body = json.dumps(MODELS).encode()
                writer.write(
                    b"HTTP/1.1 200 OK\r\nContent-Type: application/json\r\nContent-Length: "
                    + str(len(body)).encode()
                    + b"\r\nConnection: close\r\n\r\n"
                    + body
                )
                await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    server = await asyncio.start_server(serve, "127.0.0.1", 0)
    base_url = f"http://127.0.0.1:{server.sockets[0].getsockname()[1]}/v1"
    try:
        async with GigaChat(
            base_url=base_url,
            access_token="fixture",
            async_backend=backend,
            trust_env=False,
            max_retries=max_retries,
            retry_backoff_factor=0,
        ) as client:
            if max_retries < failures:
                with pytest.raises(APIConnectionError):
                    await client.aget_models()
            else:
                assert (await client.aget_models()).data
        assert requests == max_retries + 1
    finally:
        server.close()
        await server.wait_closed()


@pytest.mark.parametrize("backend", ["httpx2", "aiohttp"])
async def test_wire_cookie_retry_snapshot_and_public_clear(backend: str) -> None:
    if backend == "aiohttp":
        pytest.importorskip("aiohttp")
    seen: list[str | None] = []

    async def serve(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        try:
            raw = await reader.readuntil(b"\r\n\r\n")
            headers = httpx2.Headers(
                [
                    (key, value.strip())
                    for line in raw.split(b"\r\n")[1:]
                    if b":" in line
                    for key, value in [line.split(b":", 1)]
                ]
            )
            seen.append(headers.get("cookie"))
            body = json.dumps(MODELS).encode()
            status = b"503 Service Unavailable" if len(seen) == 1 else b"200 OK"
            cookie = b"Set-Cookie: server=late; Path=/\r\n" if len(seen) == 1 else b""
            writer.write(
                b"HTTP/1.1 "
                + status
                + b"\r\n"
                + cookie
                + b"Content-Type: application/json\r\nContent-Length: "
                + str(len(body)).encode()
                + b"\r\nConnection: close\r\n\r\n"
                + body
            )
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    server = await asyncio.start_server(serve, "127.0.0.1", 0)
    base_url = f"http://localhost:{server.sockets[0].getsockname()[1]}/v1"
    cls = DefaultAioHttpClient if backend == "aiohttp" else DefaultAsyncHttpxClient
    try:
        async with cls(cookies={"session": "initial"}, trust_env=False) as http:
            async with GigaChat(base_url=base_url, async_http_client=http, max_retries=1) as client:
                await client.aget_models()
                assert http.cookies.get("server") == "late"
                http.cookies.clear()
                await client.aget_models()
        assert seen == ["session=initial", "session=initial", None]
    finally:
        server.close()
        await server.wait_closed()
