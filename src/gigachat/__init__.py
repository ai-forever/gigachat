import logging

from gigachat.client import GigaChat, GigaChatAsyncClient, GigaChatSyncClient
from gigachat.context import custom_headers_cvar, request_id_cvar, session_id_cvar
from gigachat.exceptions import (
    AuthenticationError,
    BadRequestError,
    ForbiddenError,
    GigaChatException,
    NotFoundError,
    RateLimitError,
    RequestEntityTooLargeError,
    ResponseError,
    ServerError,
)
from gigachat.models import (
    Chat,
    ChatCompletion,
    ChatCompletionChunk,
    Choices,
    Embeddings,
    Function,
    FunctionCall,
    FunctionParameters,
    Image,
    Messages,
    MessagesRole,
    Model,
    Models,
    Usage,
)

__all__ = [
    "GigaChat",
    "GigaChatSyncClient",
    "GigaChatAsyncClient",
    "GigaChatException",
    "ResponseError",
    "AuthenticationError",
    "RateLimitError",
    "BadRequestError",
    "ForbiddenError",
    "NotFoundError",
    "RequestEntityTooLargeError",
    "ServerError",
    "Chat",
    "ChatCompletion",
    "ChatCompletionChunk",
    "Messages",
    "MessagesRole",
    "Function",
    "FunctionCall",
    "FunctionParameters",
    "Choices",
    "Usage",
    "Embeddings",
    "Image",
    "Model",
    "Models",
    "session_id_cvar",
    "request_id_cvar",
    "custom_headers_cvar",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())
