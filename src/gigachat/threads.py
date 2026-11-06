"""Preserve the published threads client imports."""

from gigachat.resources.threads import ThreadsAsyncClient as ThreadsAsyncClient
from gigachat.resources.threads import ThreadsSyncClient as ThreadsSyncClient

__all__ = ("ThreadsAsyncClient", "ThreadsSyncClient")
