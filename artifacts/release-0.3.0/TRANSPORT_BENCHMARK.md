# Local transport benchmark: bounded sample

This is an exploratory loopback sample, not a production performance qualification. Run from the repository root with the SDK and aiohttp extra installed:

```bash
PYTHONPATH=src python artifacts/release-0.3.0/benchmark_transports.py --rounds 2
```

The recorded run used Python 3.12.12 on macOS arm64, HTTPX2 2.16.0 and aiohttp 3.14.5. Both clients used HTTP/1.1, a 10-second scalar timeout, no retries or proxy, a 100-connection limit, and no separate idle-connection cap. Client and server ran in the same process without TLS. Each scenario used two batches at each concurrency of 1, 10, 50 and 100; one JSON request warmed the client. JSON returned a small object, SSE sent three events at 2 ms intervals, and upload/download bodies were 64 KiB. The measurements include server and event-loop overhead.

All 1,288 measured requests per backend completed without reported errors. At concurrency 100, each row below contains 200 requests; latency and SSE time to first byte are in milliseconds.

| Workload | HTTPX2 p50 / p95 / p99 | aiohttp p50 / p95 / p99 |
|---|---:|---:|
| JSON | 49.7 / 67.6 / 69.9 | 11.4 / 17.2 / 17.9 |
| SSE completion | 68.0 / 88.3 / 95.9 | 15.5 / 17.4 / 17.7 |
| SSE first byte p50 / p95 | 28.5 / 65.3 | 8.5 / 11.0 |
| Upload | 59.3 / 79.9 / 86.3 | 10.5 / 13.5 / 14.1 |
| Download | 53.9 / 68.9 / 71.4 | 9.4 / 11.2 / 11.6 |

The JSON file contains all scenario rows, including CPU time, process RSS high-water mark, loop-lag samples and file-descriptor counts. CPU and RSS include the server; RSS is cumulative high-water memory and cannot compare the two clients independently. The file-descriptor count includes both ends of loopback connections. After a 20-task cancellation exercise, a subsequent request succeeded for each client; closing each client returned the process descriptor count from its prior baseline of 8 to 8.

The very short, fixed-order, single-process run is sensitive to warm-up, scheduling and cache effects. Tail percentiles from two small batches are illustrative only; no live GigaChat requests, TLS overhead, long-running reliability, cold/warm isolation, or fault-rate benchmark was measured. Repeat with randomized order, independent processes, sustained duration and representative production workloads before drawing performance conclusions.
