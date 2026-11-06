"""Check an installed wheel outside the checkout, with or without aiohttp."""

import asyncio
import importlib.metadata
import importlib.util
import sys
from pathlib import Path

import httpx2

import gigachat
from gigachat.assistants import AssistantsAsyncClient, AssistantsSyncClient
from gigachat.resources.assistants import AssistantsAsyncClient as ResourceAssistantsAsyncClient
from gigachat.resources.assistants import AssistantsSyncClient as ResourceAssistantsSyncClient
from gigachat.resources.threads import ThreadsAsyncClient as ResourceThreadsAsyncClient
from gigachat.resources.threads import ThreadsSyncClient as ResourceThreadsSyncClient
from gigachat.threads import ThreadsAsyncClient, ThreadsSyncClient


def check_installation(*, aiohttp: bool) -> None:
    """Verify package contents, public aliases, and optional transport loading."""
    assert sys.version_info.releaselevel == "final"
    assert gigachat.__file__ is not None
    package = Path(gigachat.__file__).parent
    assert "site-packages" in package.parts
    assert importlib.util.find_spec("httpx") is None
    assert (importlib.util.find_spec("aiohttp") is not None) is aiohttp
    assert "aiohttp" not in sys.modules
    assert all(hasattr(gigachat, name) for name in gigachat.__all__)
    assert AssistantsSyncClient is ResourceAssistantsSyncClient
    assert AssistantsAsyncClient is ResourceAssistantsAsyncClient
    assert ThreadsSyncClient is ResourceThreadsSyncClient
    assert ThreadsAsyncClient is ResourceThreadsAsyncClient
    for path in ("py.typed", "_vendor/httpx_aiohttp/LICENSE", "_vendor/httpx_aiohttp/FORK.md"):
        assert (package / path).is_file(), path
    files = importlib.metadata.files("gigachat")
    assert files is not None
    assert any(str(path).endswith(".dist-info/licenses/LICENSE") for path in files)
    assert {path.stem for path in (package / "_core").glob("*.py")} == {
        "__init__",
        "base_client",
        "http_client",
        "request",
        "execution",
        "response",
        "streaming",
    }
    if aiohttp:
        asyncio.run(check_optional_client())
    print(f"Installed wheel passed on Python {sys.version.split()[0]} (aiohttp={aiohttp}): {package}")


async def check_optional_client() -> None:
    async with gigachat.DefaultAioHttpClient(trust_env=False) as client:
        assert isinstance(client, httpx2.AsyncClient)


if __name__ == "__main__":
    check_installation(aiohttp="--aiohttp" in sys.argv)
