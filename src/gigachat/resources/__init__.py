from gigachat.resources._utils import warn_deprecated_resource_api
from gigachat.resources.assistants import AssistantsAsyncClient, AssistantsSyncClient
from gigachat.resources.chat import (
    AsyncChatNamespace,
    ChatNamespace,
    LegacyChatAsyncResource,
    LegacyChatSyncResource,
)
from gigachat.resources.embeddings import EmbeddingsAsyncResource, EmbeddingsSyncResource
from gigachat.resources.files import FilesAsyncResource, FilesSyncResource
from gigachat.resources.models import ModelsAsyncResource, ModelsSyncResource
from gigachat.resources.threads import ThreadsAsyncClient, ThreadsSyncClient
from gigachat.resources.tokens import TokensAsyncResource, TokensSyncResource

__all__ = (
    "AsyncChatNamespace",
    "AssistantsAsyncClient",
    "AssistantsSyncClient",
    "ChatNamespace",
    "EmbeddingsAsyncResource",
    "EmbeddingsSyncResource",
    "FilesAsyncResource",
    "FilesSyncResource",
    "LegacyChatAsyncResource",
    "LegacyChatSyncResource",
    "ModelsAsyncResource",
    "ModelsSyncResource",
    "ThreadsAsyncClient",
    "ThreadsSyncClient",
    "TokensAsyncResource",
    "TokensSyncResource",
    "warn_deprecated_resource_api",
)
