from enum import Enum
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

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
    FROZEN = "frozen"


class Thread(BaseModel):
    """Thread object."""

    id_: str = Field(
        alias="id",
        validation_alias=AliasChoices("thread_id", "id"),
        description="The identifier, which can be referenced in API endpoints.",
    )
    assistant_id: str | None = Field(
        default=None, description="The ID of the assistant. Passed with the first message."
    )
    model: str = Field(description="Model alias.")
    created_at: int = Field(description="The time at which the thread was created (Unix timestamp).")
    updated_at: int = Field(description="The time at which the thread was last updated (Unix timestamp).")
    metadata: dict[str, Any] | None = None
    access_policy: str | None = None
    last_message: Any = None
    run_lock: bool = Field(description="Current run status of the thread.")
    status: ThreadStatus | str = Field(description="Thread status.", union_mode="left_to_right")


class Threads(APIResponse):
    """List of threads."""

    threads: list[Thread] = Field(description="List of thread objects.")


class ThreadCompletion(APIResponse):
    """Thread completion response."""

    object_: str = Field(alias="object", description="Object type.")
    model: str = Field(description="Model used for generation.")
    thread_id: str = Field(description="Thread ID.")
    message_id: str = Field(description="Message ID.")
    created: int = Field(description="Creation timestamp (Unix time).")
    usage: Usage = Field(description="Usage statistics.")
    message: Messages = Field(description="Generated message.")
    finish_reason: str = Field(description="Reason why the generation finished.")


class ThreadCompletionChunk(APIResponse):
    """Thread completion stream chunk."""

    object_: str = Field(alias="object", description="Object type.")
    model: str = Field(description="Model used for generation.")
    thread_id: str = Field(description="Thread ID.")
    message_id: str = Field(description="Message ID.")
    created: int = Field(description="Creation timestamp (Unix time).")
    usage: Usage | None = Field(default=None, description="Usage statistics, usually sent in the final chunk.")
    choices: list[ChoicesChunk] = Field(description="List of completion choice chunks.")


class ThreadMessageAttachment(BaseModel):
    """Attachment in a thread message."""

    file_id: str = Field(description="File identifier.")
    name: str = Field(description="File name.")


class ThreadMessage(BaseModel):
    """Thread message."""

    model: str | None = None
    notasearch_sources: Any = None
    additional_data: Any = None
    message_id: str = Field(description="Message identifier.")
    role: MessagesRole = Field(description="Role of the message author.")
    content: str = Field(default="", description="Content of the message.")
    attachments: list[ThreadMessageAttachment] | None = Field(default=[], description="List of attachments.")
    created_at: int = Field(description="Creation timestamp (Unix time).")
    function_call: FunctionCall | None = Field(default=None, description="Function call.")
    finish_reason: str | None = Field(default=None, description="Finish reason.")

    model_config = ConfigDict(use_enum_values=True)


class ThreadMessages(APIResponse):
    """List of thread messages."""

    thread_id: str = Field(description="Thread identifier.")
    messages: list[ThreadMessage] = Field(description="List of messages.")


class ThreadMessageResponse(BaseModel):
    """Response for message creation."""

    created_at: int = Field(description="Creation timestamp (Unix time).")
    message_id: str = Field(description="Message identifier.")


class ThreadMessagesResponse(APIResponse):
    """Response for messages creation."""

    thread_id: str = Field(description="Thread identifier.")
    messages: list[ThreadMessageResponse] = Field(description="List of created messages.")


class ThreadRunOptions(BaseModel):
    """Options for running a thread."""

    unnormalized_history: bool | None = None
    temperature: float | None = Field(
        default=None, description="Sampling temperature (range: 0.0 < temperature ≤ 2.0)."
    )
    top_p: float | None = Field(default=None, description="Nucleus sampling parameter.")
    limit: int | None = Field(default=None, description="Max context messages to send. If not set, sends all context.")
    max_tokens: int | None = Field(default=None, description="Max tokens to generate.")
    repetition_penalty: float | None = Field(
        default=None,
        description=(
            "Repetition penalty (allowed values: >0; 1.0 = neutral, "
            ">1.0 = reduce repetition, <1.0 = increase repetition)."
        ),
    )
    profanity_check: bool | None = Field(default=None, description="Enable profanity filtering.")
    flags: list[str] | None = Field(default=None, description="Feature flags.")
    function_call: Literal["auto", "none"] | ChatFunctionCall | None = Field(
        default=None, description="Function call strategy."
    )
    functions: list[Function] | None = Field(default=None, description="List of available functions.")


class ThreadRunResponse(APIResponse):
    """Response for starting a thread run."""

    status: ThreadStatus | str = Field(description="Run status.", union_mode="left_to_right")
    thread_id: str = Field(description="Thread identifier.")
    created_at: int = Field(description="Start timestamp (Unix time).")


class ThreadRunResult(APIResponse):
    """Result of a thread run status check."""

    status: ThreadStatus | str = Field(description="Run status.", union_mode="left_to_right")
    thread_id: str = Field(description="Thread identifier.")
    updated_at: int = Field(description="Last update timestamp (Unix time).")
    model: str = Field(description="Model name.")
    messages: list[ThreadMessage] | None = Field(default=None, description="Messages generated during the run.")


class SharedThread(APIResponse):
    """Read-only shared copy of a thread."""

    shared_thread_id: str
    link: str
