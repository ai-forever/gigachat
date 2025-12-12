from enum import Enum
from typing import List, Literal, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

from gigachat.models.base import APIResponse
from gigachat.models.chat import (
    ChatFunctionCall,
    ChoicesChunk,
    Function,
    FunctionCall,
    Messages,
    MessagesRole,
    Usage,
)


class ThreadStatus(str, Enum):
    """Status of the thread run."""

    IN_PROGRESS = "in_progress"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class Thread(BaseModel):
    """Thread object."""

    id_: str = Field(alias="id")
    """The identifier, which can be referenced in API endpoints."""
    assistant_id: Optional[str] = None
    """The ID of the assistant. Passed with the first message."""
    model: str
    """Model alias."""
    created_at: int
    """The time at which the thread was created (Unix timestamp)."""
    updated_at: int
    """The time at which the thread was last updated (Unix timestamp)."""
    run_lock: bool
    """Current run status of the thread."""
    status: ThreadStatus
    """Thread status."""


class Threads(APIResponse):
    """List of threads."""

    threads: List[Thread]
    """List of thread objects."""


class ThreadCompletion(APIResponse):
    """Thread completion response."""

    object_: str = Field(alias="object")
    """Object type."""
    model: str
    """Model used for generation."""
    thread_id: str
    """Thread ID."""
    message_id: str
    """Message ID."""
    created: int
    """Creation timestamp (Unix time)."""
    usage: Usage
    """Usage statistics."""
    message: Messages
    """Generated message."""
    finish_reason: str
    """Reason why the generation finished."""


class ThreadCompletionChunk(APIResponse):
    """Thread completion stream chunk."""

    object_: str = Field(alias="object")
    """Object type."""
    model: str
    """Model used for generation."""
    thread_id: str
    """Thread ID."""
    message_id: str
    """Message ID."""
    created: int
    """Creation timestamp (Unix time)."""
    usage: Usage
    """Usage statistics."""
    choices: List[ChoicesChunk]
    """List of completion choice chunks."""


class ThreadMessageAttachment(BaseModel):
    """Attachment in a thread message."""

    file_id: str
    """File identifier."""
    name: str
    """File name."""


class ThreadMessage(BaseModel):
    """Thread message."""

    message_id: str
    """Message identifier."""
    role: MessagesRole
    """Role of the message author."""
    content: str = ""
    """Content of the message."""
    attachments: Optional[List[ThreadMessageAttachment]] = []
    """List of attachments."""
    created_at: int
    """Creation timestamp (Unix time)."""
    function_call: Optional[FunctionCall] = None
    """Function call."""
    finish_reason: Optional[str] = None
    """Finish reason."""

    model_config = ConfigDict(use_enum_values=True)


class ThreadMessages(APIResponse):
    """List of thread messages."""

    thread_id: str
    """Thread identifier."""
    messages: List[ThreadMessage]
    """List of messages."""


class ThreadMessageResponse(BaseModel):
    """Response for message creation."""

    created_at: int
    """Creation timestamp (Unix time)."""
    message_id: str
    """Message identifier."""


class ThreadMessagesResponse(APIResponse):
    """Response for messages creation."""

    thread_id: str
    """Thread identifier."""
    messages: List[ThreadMessageResponse]
    """List of created messages."""


class ThreadRunOptions(BaseModel):
    """Options for running a thread."""

    temperature: Optional[float] = None
    """Sampling temperature (range: 0.0 < temperature ≤ 2.0)."""
    top_p: Optional[float] = None
    """Nucleus sampling parameter."""
    limit: Optional[int] = None
    """Max context messages to send. If not set, sends all context."""
    max_tokens: Optional[int] = None
    """Max tokens to generate."""
    repetition_penalty: Optional[float] = None
    """Repetition penalty (allowed values: >0; 1.0 = neutral, >1.0 = reduce repetition, <1.0 = increase repetition)."""
    profanity_check: Optional[bool] = None
    """Enable profanity filtering."""
    flags: Optional[List[str]] = None
    """Feature flags."""
    function_call: Optional[Union[Literal["auto", "none"], ChatFunctionCall]] = None
    """Function call strategy."""
    functions: Optional[List[Function]] = None
    """List of available functions."""


class ThreadRunResponse(APIResponse):
    """Response for starting a thread run."""

    status: ThreadStatus
    """Run status."""
    thread_id: str
    """Thread identifier."""
    created_at: int
    """Start timestamp (Unix time)."""


class ThreadRunResult(APIResponse):
    """Result of a thread run status check."""

    status: ThreadStatus
    """Run status."""
    thread_id: str
    """Thread identifier."""
    updated_at: int
    """Last update timestamp (Unix time)."""
    model: str
    """Model name."""
    messages: Optional[List[ThreadMessage]] = None
    """Messages generated during the run."""
