"""Run a bounded loopback HTTP/1.1 transport comparison; no live service is contacted."""

# Closures are fully awaited before each scenario advances.
# ruff: noqa: B023, C901

import argparse
import asyncio
import json
import os
import platform
import resource
import time
from pathlib import Path

import aiohttp
import httpx2
from aiohttp import web

from gigachat._http_client import DefaultAioHttpClient, DefaultAsyncHttpxClient

PAYLOAD = b"a" * 65536


def fd_count():
    try:
        return len(os.listdir("/dev/fd"))
    except OSError:
        return None


def percentile(values, fraction):
    values = sorted(values)
    return values[round((len(values) - 1) * fraction)] if values else None


async def main(args):
    async def json_handler(request):
        return web.json_response({"value": "ok", "sequence": list(range(16))})

    async def upload_handler(request):
        return web.json_response({"bytes": len(await request.read())})

    async def download_handler(request):
        return web.Response(body=PAYLOAD)

    async def sse_handler(request):
        response = web.StreamResponse(headers={"Content-Type": "text/event-stream"})
        await response.prepare(request)
        try:
            for index in range(3):
                await response.write(f"data: {index}\n\n".encode())
                await asyncio.sleep(0.002)
            await response.write_eof()
        except ConnectionResetError:
            pass
        return response

    app = web.Application()
    app.router.add_get("/json", json_handler)
    app.router.add_post("/upload", upload_handler)
    app.router.add_get("/download", download_handler)
    app.router.add_get("/sse", sse_handler)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    site = web.TCPSite(runner, "127.0.0.1", 0)
    await site.start()
    url = f"http://127.0.0.1:{site._server.sockets[0].getsockname()[1]}"
    results = []
    limits = httpx2.Limits(max_connections=100, max_keepalive_connections=None)
    try:
        for backend, cls in (("httpx2", DefaultAsyncHttpxClient), ("aiohttp", DefaultAioHttpClient)):
            baseline_fd = fd_count()
            async with cls(trust_env=False, timeout=10.0, limits=limits, http2=False) as client:
                await client.get(url + "/json")
                for workload in ("json", "sse", "upload", "download"):
                    for concurrency in (1, 10, 50, 100):
                        durations, ttfts, lag = [], [], []
                        errors = 0
                        running = True

                        async def sample_lag():
                            while running:
                                before = time.perf_counter()
                                await asyncio.sleep(0.01)
                                lag.append(max(0, (time.perf_counter() - before - 0.01) * 1000))

                        async def call():
                            nonlocal errors
                            started = time.perf_counter()
                            try:
                                if workload == "sse":
                                    async with client.stream("GET", url + "/sse") as response:
                                        response.raise_for_status()
                                        first = True
                                        async for chunk in response.aiter_bytes():
                                            if chunk and first:
                                                ttfts.append((time.perf_counter() - started) * 1000)
                                                first = False
                                elif workload == "upload":
                                    response = await client.post(url + "/upload", content=PAYLOAD)
                                    response.raise_for_status()
                                elif workload == "download":
                                    async with client.stream("GET", url + "/download") as response:
                                        response.raise_for_status()
                                        async for _ in response.aiter_bytes():
                                            pass
                                else:
                                    response = await client.get(url + "/json")
                                    response.raise_for_status()
                                durations.append((time.perf_counter() - started) * 1000)
                            except Exception:
                                errors += 1

                        fd_before = fd_count()
                        cpu_before = time.process_time()
                        wall_before = time.perf_counter()
                        monitor = asyncio.create_task(sample_lag())
                        for _ in range(args.rounds):
                            await asyncio.gather(*(call() for _ in range(concurrency)))
                        running = False
                        await monitor
                        elapsed = time.perf_counter() - wall_before
                        results.append(
                            {
                                "backend": backend,
                                "workload": workload,
                                "concurrency": concurrency,
                                "attempts": concurrency * args.rounds,
                                "completed": len(durations),
                                "errors": errors,
                                "wall_seconds": elapsed,
                                "cpu_seconds": time.process_time() - cpu_before,
                                "latency_ms_p50": percentile(durations, 0.5),
                                "latency_ms_p95": percentile(durations, 0.95),
                                "latency_ms_p99": percentile(durations, 0.99),
                                "ttft_ms_p50": percentile(ttfts, 0.5),
                                "ttft_ms_p95": percentile(ttfts, 0.95),
                                "loop_lag_ms_p99": percentile(lag, 0.99),
                                "rss_high_water_native_units": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                                "fd_before": fd_before,
                                "fd_after": fd_count(),
                            }
                        )
                before_cancel = fd_count()
                tasks = [asyncio.create_task(client.get(url + "/sse")) for _ in range(20)]
                await asyncio.sleep(0.001)
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
                await asyncio.sleep(0.1)
                healthy = (await client.get(url + "/json")).status_code == 200
                results.append(
                    {
                        "backend": backend,
                        "workload": "cancel_cleanup",
                        "tasks": len(tasks),
                        "cancelled": sum(t.cancelled() for t in tasks),
                        "fd_before": before_cancel,
                        "fd_after": fd_count(),
                        "subsequent_request_ok": healthy,
                    }
                )
            await asyncio.sleep(0.1)
            results.append(
                {
                    "backend": backend,
                    "workload": "client_close",
                    "fd_before_client": baseline_fd,
                    "fd_after_client_close": fd_count(),
                }
            )
    finally:
        await runner.cleanup()
    output = {
        "protocol": "loopback HTTP/1.1, no TLS, timeout=10s, retries=0, max_connections=100",
        "platform": platform.platform(),
        "python": platform.python_version(),
        "httpx2": httpx2.__version__,
        "aiohttp": aiohttp.__version__,
        "rounds": args.rounds,
        "rss_units": "bytes on macOS, KiB on Linux; process high-water, not scenario delta",
        "caveats": "Single process client/server, short sample, no production quality or throughput claim.",
        "results": results,
    }
    Path(args.output).write_text(json.dumps(output, indent=2) + "\n")
    print(f"Wrote {len(results)} rows to {args.output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rounds", type=int, default=2)
    parser.add_argument("--output", default="artifacts/release-0.3.0/transport-benchmark.json")
    asyncio.run(main(parser.parse_args()))
