# HTTPX2-native aiohttp adapter

Based on httpx-aiohttp 0.2.0, commit 52266a66f6bd73f828133d0fd09114179fd45b60, via OpenAI's HTTPX2-native fork. The original BSD-3-Clause license is included in LICENSE.

Local changes: lazy optional imports, borrowed session ownership with hidden default auth rejection, strict timeout and pool validation, no automatic decompression, explicit proxy and TLS handling, and corrected connection exception mapping. Client integration is in `gigachat._http_client`.

To update, compare the HTTPX2 transport and client modules at https://github.com/karpetrosyan/httpx-aiohttp/tree/52266a66f6bd73f828133d0fd09114179fd45b60 with the latest upstream release; retain the license and reapply and test local changes.

For a local comparison: `git clone https://github.com/karpetrosyan/httpx-aiohttp.git /tmp/httpx-aiohttp && git -C /tmp/httpx-aiohttp diff 52266a66f6bd73f828133d0fd09114179fd45b60 HEAD -- src`.
