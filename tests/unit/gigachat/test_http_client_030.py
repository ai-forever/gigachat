import asyncio
import gzip
from collections.abc import AsyncIterator
from typing import Any, cast

import httpx2
import pytest

from gigachat._http_client import DefaultAioHttpClient, DefaultAsyncHttpxClient, DefaultHttpxClient


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


async def test_aiohttp_wire_stream_decompression_and_borrowed_session() -> None:
    aiohttp = pytest.importorskip("aiohttp")
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
    async with aiohttp.ClientSession() as session:
        async with DefaultAioHttpClient(session=session, trust_env=False) as client:
            response = await client.get(f"http://127.0.0.1:{port}/")
            assert response.content == b"hello world"
        assert not session.closed
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


async def test_borrowed_aiohttp_session_rejects_default_auth() -> None:
    import warnings

    aiohttp = pytest.importorskip("aiohttp")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        session = aiohttp.ClientSession(auth=aiohttp.BasicAuth("fixture-user", "fixture-secret"))
    async with session:
        with pytest.raises(ValueError, match="configure HTTPX2 client headers") as error:
            DefaultAioHttpClient(session=session, trust_env=False)
        assert "fixture-secret" not in str(error.value)
        assert not session.closed


async def test_borrowed_aiohttp_session_rejects_authorization_header() -> None:
    aiohttp = pytest.importorskip("aiohttp")
    async with aiohttp.ClientSession(headers={"aUtHoRiZaTiOn": "Bearer fixture-secret"}) as session:
        with pytest.raises(ValueError, match="configure HTTPX2 client headers") as error:
            DefaultAioHttpClient(session=session, trust_env=False)
        assert "fixture-secret" not in str(error.value)
        assert not session.closed


async def test_borrowed_aiohttp_session_rechecks_mutated_headers() -> None:
    aiohttp = pytest.importorskip("aiohttp")
    async with aiohttp.ClientSession() as session:
        async with DefaultAioHttpClient(session=session, trust_env=False) as client:
            session.headers["Authorization"] = "Bearer fixture-secret"
            with pytest.raises(ValueError, match="configure HTTPX2 client headers") as error:
                await client.get("http://example.invalid")
            assert "fixture-secret" not in str(error.value)
        assert not session.closed
