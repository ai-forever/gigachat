"""Preserve the published assistants client imports."""

from gigachat.resources.assistants import AssistantsAsyncClient as AssistantsAsyncClient
from gigachat.resources.assistants import AssistantsSyncClient as AssistantsSyncClient

__all__ = ("AssistantsAsyncClient", "AssistantsSyncClient")
