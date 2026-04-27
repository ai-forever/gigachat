from gigachat.resources._utils import warn_deprecated_resource_api
from gigachat.resources.chat import (
    AsyncChatNamespace,
    ChatNamespace,
    LegacyChatAsyncResource,
    LegacyChatSyncResource,
)

__all__ = (
    "AsyncChatNamespace",
    "ChatNamespace",
    "LegacyChatAsyncResource",
    "LegacyChatSyncResource",
    "warn_deprecated_resource_api",
)
