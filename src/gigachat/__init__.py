import logging
from importlib.metadata import PackageNotFoundError, version

from gigachat.client import GigaChat, GigaChatAsyncClient, GigaChatSyncClient
from gigachat.context import custom_headers_cvar, request_id_cvar, session_id_cvar
from gigachat.exceptions import (
    AuthenticationError,
    BadRequestError,
    ContentFilterFinishReasonError,
    ContentParseError,
    ContentValidationError,
    ForbiddenError,
    GigaChatException,
    LengthFinishReasonError,
    NotFoundError,
    RateLimitError,
    RequestEntityTooLargeError,
    ResponseError,
    ServerError,
)
from gigachat.models import (
    Batch,
    Batches,
    Chat,
    ChatCompletion,
    ChatCompletionChunk,
    Choices,
    Embeddings,
    File,
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

try:
    __version__ = version("gigachat")
except PackageNotFoundError:
    __version__ = "0.2.1"

__all__ = [
    "__version__",
    "GigaChat",
    "GigaChatSyncClient",
    "GigaChatAsyncClient",
    "GigaChatException",
    "ResponseError",
    "AuthenticationError",
    "RateLimitError",
    "BadRequestError",
    "ContentFilterFinishReasonError",
    "ContentParseError",
    "ContentValidationError",
    "ForbiddenError",
    "LengthFinishReasonError",
    "NotFoundError",
    "RequestEntityTooLargeError",
    "ServerError",
    "Batch",
    "Batches",
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
    "File",
    "Image",
    "Model",
    "Models",
    "session_id_cvar",
    "request_id_cvar",
    "custom_headers_cvar",
]

logging.getLogger(__name__).addHandler(logging.NullHandler())
