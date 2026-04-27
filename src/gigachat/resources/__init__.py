from gigachat.resources._utils import warn_deprecated_resource_api
from gigachat.resources.assistants import AssistantsAsyncClient, AssistantsSyncClient
from gigachat.resources.chat import (
    AsyncChatNamespace,
    ChatNamespace,
    LegacyChatAsyncResource,
    LegacyChatSyncResource,
)
from gigachat.resources.threads import ThreadsAsyncClient, ThreadsSyncClient

__all__ = (
    "AsyncChatNamespace",
    "AssistantsAsyncClient",
    "AssistantsSyncClient",
    "ChatNamespace",
    "LegacyChatAsyncResource",
    "LegacyChatSyncResource",
    "ThreadsAsyncClient",
    "ThreadsSyncClient",
    "warn_deprecated_resource_api",
)
