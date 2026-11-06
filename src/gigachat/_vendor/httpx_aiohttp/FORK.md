# HTTPX2-native aiohttp adapter

Based on httpx-aiohttp 0.2.0, commit 52266a66f6bd73f828133d0fd09114179fd45b60, via OpenAI's HTTPX2-native fork. The original BSD-3-Clause license is included in LICENSE.

Local changes: lazy optional imports, owned lazy sessions, strict timeout and pool validation, no automatic decompression, explicit proxy and TLS handling, and corrected connection exception mapping. Client integration is in `gigachat._http_client`.

SDK-created sessions set `ClientSession._retry_connection = False`: aiohttp 3.14.5 has no public constructor switch for its implicit idempotent-request retry. This isolated private access keeps all network retries under the SDK executor's count/time/replayability budget. Loopback regressions count actual requests with retries disabled and enabled; recheck this switch when upgrading aiohttp. Raw `ClientSession` injection is not supported. Finite timeouts must be positive; `None` disables the corresponding budget.

To update, compare the HTTPX2 transport and client modules at https://github.com/karpetrosyan/httpx-aiohttp/tree/52266a66f6bd73f828133d0fd09114179fd45b60 with the latest upstream release; retain the license and reapply and test local changes.

For a local comparison: `git clone https://github.com/karpetrosyan/httpx-aiohttp.git /tmp/httpx-aiohttp && git -C /tmp/httpx-aiohttp diff 52266a66f6bd73f828133d0fd09114179fd45b60 HEAD -- src`.
