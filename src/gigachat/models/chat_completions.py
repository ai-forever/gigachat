import inspect
from typing import Any, Literal, Optional

import pydantic
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from gigachat.models.base import APIResponse


def _normalize_content_parts(value: Any) -> Any:
    """Normalize text-or-parts message content into a list of content parts."""
    if value is None:
        return value

    if isinstance(value, str):
        return [{"text": value}]

    if isinstance(value, dict):
        return [value]

    if isinstance(value, list):
        normalized = []
        for item in value:
            if isinstance(item, str):
                normalized.append({"text": item})
            else:
                normalized.append(item)
        return normalized

    return value


def _normalize_tool(value: Any) -> Any:
    """Normalize a shorthand tool name into the full tool object format."""
    supported_tools = (
        "code_interpreter",
        "image_generate",
        "web_search",
        "url_content_extraction",
        "model_3d_generate",
    )
    if isinstance(value, str):
        if value not in supported_tools:
            raise ValueError(
                "'tools' string items must be one of {supported}; got '{tool}'".format(
                    supported=", ".join(supported_tools), tool=value
                )
            )
        return {value: {}}
    return value


def _normalize_tools_state_id(values: dict[str, Any]) -> None:
    """Normalize known tool-state aliases to the primary wire field."""
    if values.get("tools_state_id") is None:
        for field_name in ("tool_state_id", "functions_state_id"):
            if values.get(field_name) is not None:
                values["tools_state_id"] = values[field_name]
                break

    values.pop("tool_state_id", None)
    values.pop("functions_state_id", None)


class _ChatCompletionsModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class _ChatCompletionsAPIResponse(APIResponse):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ChatSource(_ChatCompletionsModel):
    """Source metadata attached to model output."""

    url: str | None = Field(default=None, description="Source URL.")
    title: str | None = Field(default=None, description="Source title.")


class ChatInlineData(_ChatCompletionsModel):
    """Inline metadata attached to a content part."""

    images: list[dict[str, Any]] | None = Field(default=None, description="Inline images.")
    sources: dict[str, ChatSource] | None = Field(default=None, description="Inline sources.")
    widgets: list[dict[str, Any]] | None = Field(default=None, description="Inline widgets.")


class ChatContentFile(_ChatCompletionsModel):
    """File reference passed in request content or returned in response content."""

    id_: str = Field(alias="id", description="File identifier.")
    target: str | None = Field(default=None, description="Generated file target.")
    mime: str | None = Field(default=None, description="File MIME type.")


class ChatFunctionResult(_ChatCompletionsModel):
    """Tool result returned back to the model in message content."""

    id_: str | None = Field(alias="id", default=None, description="Matching function call identifier.")
    name: str = Field(description="Tool or function name.")
    result: Any = Field(description="Tool result payload.")


class ChatContentPart(_ChatCompletionsModel):
    """Structured content part for a chat message."""

    text: str | None = Field(default=None, description="Text content.")
    files: list[ChatContentFile] | None = Field(default=None, description="Referenced or generated files.")
    function_call: Optional["ChatFunctionCall"] = Field(default=None, description="Tool call payload.")
    function_result: ChatFunctionResult | None = Field(default=None, description="Tool result payload.")
    tool_execution: Optional["ChatToolExecution"] = Field(default=None, description="Tool execution state.")
    inline_data: ChatInlineData | None = Field(default=None, description="Inline metadata.")
    logprobs: list["ChatLogprob"] | None = Field(default=None, description="Per-token log probabilities.")


class ChatFunctionCall(_ChatCompletionsModel):
    """Requested or emitted function call."""

    id_: str | None = Field(alias="id", default=None, description="Function call identifier.")
    name: str = Field(description="Function name.")
    arguments: Any = Field(description="Function arguments.")


class ChatToolExecution(_ChatCompletionsModel):
    """Execution state for built-in or platform tool invocation."""

    name: str | None = Field(default=None, description="Tool name.")
    status: str | None = Field(default=None, description="Execution status.")
    seconds_left: int | None = Field(default=None, description="Seconds until completion.")
    censored: bool | None = Field(default=None, description="Whether execution was censored.")


class ChatLogprobToken(_ChatCompletionsModel):
    """Token logprob entry."""

    token: str = Field(description="Token text.")
    token_id: int = Field(description="Token identifier.")
    logprob: float = Field(description="Token log probability.")


class ChatLogprob(_ChatCompletionsModel):
    """Per-position logprob information."""

    chosen: ChatLogprobToken | None = Field(default=None, description="Chosen token.")
    top: list[ChatLogprobToken] | None = Field(default=None, description="Top candidate tokens.")


class ChatUsageInputTokensDetails(_ChatCompletionsModel):
    """Detailed request token accounting."""

    prompt_tokens: int | None = Field(default=None, description="Prompt token count.")
    cached_tokens: int | None = Field(default=None, description="Tokens served from cache.")


class ChatUsage(_ChatCompletionsModel):
    """Usage information for the new chat completions contract."""

    input_tokens: int | None = Field(default=None, description="Input token count.")
    input_tokens_details: ChatUsageInputTokensDetails | None = Field(
        default=None, description="Detailed input token accounting."
    )
    output_tokens: int | None = Field(default=None, description="Output token count.")
    total_tokens: int | None = Field(default=None, description="Total token count.")


class ChatReasoning(_ChatCompletionsModel):
    """Reasoning controls."""

    effort: str | None = Field(default=None, description="Reasoning effort.")
    max_tokens: int | None = Field(default=None, description="Maximum reasoning tokens before the final answer.")


class ChatModelOptions(_ChatCompletionsModel):
    """Model generation options."""

    unnormalized_history: bool | None = None
    parallel_tool_calls: bool | None = Field(default=None, description="Allow parallel function calls.")
    temperature: float | None = Field(default=None, description="Sampling temperature.")
    top_p: float | None = Field(default=None, description="Nucleus sampling parameter.")
    max_tokens: int | None = Field(default=None, description="Maximum completion tokens.")
    repetition_penalty: float | None = Field(default=None, description="Repetition penalty.")
    update_interval: float | None = Field(default=None, description="Streaming update interval.")
    reasoning: ChatReasoning | None = Field(default=None, description="Reasoning settings.")
    response_format: Optional["ChatResponseFormat"] = Field(default=None, description="Response format settings.")


class ChatResponseFormat(_ChatCompletionsModel):
    """Response format request for the primary chat completions contract."""

    type: str = Field(default="text", description="Requested response format.")
    schema_: dict[str, Any] | str | None = Field(
        alias="schema", default=None, description="JSON Schema or raw schema payload."
    )
    strict: bool | None = Field(default=None, description="Strict schema adherence.")
    regex: str | None = Field(default=None, description="Regular expression response format.")

    @model_validator(mode="before")
    @classmethod
    def _validate_and_convert_schema(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        schema = values.get("schema")
        if schema is None:
            return values

        if inspect.isclass(schema) and issubclass(schema, pydantic.BaseModel):
            values = dict(values)
            values["schema"] = schema.model_json_schema()
            return values

        if isinstance(schema, pydantic.BaseModel):
            values = dict(values)
            values["schema"] = schema.__class__.model_json_schema()
            return values

        if isinstance(schema, (dict, str)):
            return values

        raise ValueError(
            "'schema' must be a dict, string, BaseModel instance, or pydantic.BaseModel subclass; "
            f"got {type(schema).__name__}"
        )


class ChatFilterContentConfig(_ChatCompletionsModel):
    """Filtering settings for request content."""

    neuro: bool | None = Field(default=None, description="Neuro censor toggle.")
    blacklist: bool | None = Field(default=None, description="Blacklist filter toggle.")
    whitelist: bool | None = Field(default=None, description="Whitelist filter toggle.")


class ChatFilterResponseContentConfig(_ChatCompletionsModel):
    """Filtering settings for response content."""

    blacklist: bool | None = Field(default=None, description="Blacklist filter toggle.")


class ChatFilterConfig(_ChatCompletionsModel):
    """Filtering configuration."""

    request_content: ChatFilterContentConfig | None = Field(default=None, description="Request filtering settings.")
    response_content: ChatFilterResponseContentConfig | None = Field(
        default=None, description="Response filtering settings."
    )


class ChatStorage(_ChatCompletionsModel):
    """Context storage configuration."""

    limit: int | None = Field(default=None, description="History size limit.")
    thread_id: str | None = Field(default=None, description="Thread identifier.")
    metadata: dict[str, Any] | None = Field(default=None, description="Thread metadata.")


class ChatRankerOptions(_ChatCompletionsModel):
    """Tool or function ranking settings."""

    mode: str | None = None
    ignored_functions: list[str] | None = None
    enabled: bool | None = Field(default=None, description="Whether ranking is enabled.")
    top_n: int | None = Field(default=None, description="Number of ranked tools to keep.")
    embeddings_model: str | None = Field(default=None, description="Embeddings model alias.")


class ChatUserInfo(_ChatCompletionsModel):
    """User metadata that may improve model answers."""

    timezone: str | None = Field(default=None, description="IANA timezone.")


class ChatToolConfig(_ChatCompletionsModel):
    """Tool-calling policy."""

    mode: Literal["auto", "none", "forced", "any"] | None = Field(default=None, description="Tool calling mode.")
    tool_name: str | None = Field(default=None, description="Forced built-in tool name.")
    function_name: str | None = Field(default=None, description="Forced client function name.")
    functions_names_any: list[str] | None = Field(default=None, description="Eligible function names for any mode.")


class ChatFunctionExample(_ChatCompletionsModel):
    """Few-shot example for function specification."""

    request: str = Field(description="User request example.")
    params: dict[str, Any] = Field(description="Function call parameters example.")


class ChatFunctionSpecification(_ChatCompletionsModel):
    """Client function specification exposed to the model."""

    name: str = Field(description="Function name.")
    description: str | None = Field(default=None, description="Function description.")
    parameters: dict[str, Any] = Field(description="Function parameters JSON Schema.")
    few_shot_examples: list[ChatFunctionExample] | None = Field(
        default=None, description="Few-shot examples for tool calling."
    )
    return_parameters: dict[str, Any] | None = Field(default=None, description="Return value JSON Schema.")

    @model_validator(mode="before")
    @classmethod
    def _fix_title_and_parameters(cls, values: Any) -> Any:
        if isinstance(values, dict):
            values = dict(values)

            if values.get("name") in (None, "") and values.get("title"):
                values["name"] = values.pop("title", None)

            if "parameters" not in values and "properties" in values:
                metadata = {"name", "description", "few_shot_examples", "return_parameters"}
                parameters = {key: values.pop(key) for key in list(values) if key not in metadata}
                parameters.setdefault("type", "object")
                values["parameters"] = parameters

        return values


class ChatFunctionsTool(_ChatCompletionsModel):
    """Tool wrapper for client-defined functions."""

    specifications: list[ChatFunctionSpecification] | None = Field(
        default=None, description="Available function specifications."
    )


class ChatWebSearchTool(_ChatCompletionsModel):
    """Configuration for the web-search built-in tool."""

    type: str | None = Field(default=None, description="Search mode.")
    indexes: list[str] | None = Field(default=None, description="Search index names.")
    flags: list[str] | None = Field(default=None, description="Provider-specific flags.")


class ChatTool(_ChatCompletionsModel):
    """One tool entry in the tools list."""

    code_interpreter: dict[str, Any] | None = Field(default=None, description="Code interpreter config.")
    image_generate: dict[str, Any] | None = Field(default=None, description="Image generation config.")
    url_content_extraction: dict[str, Any] | None = Field(default=None, description="URL extraction config.")
    model_3d_generate: dict[str, Any] | None = Field(default=None, description="3D generation config.")
    functions: ChatFunctionsTool | None = Field(default=None, description="Client function tool config.")

    @model_validator(mode="before")
    @classmethod
    def _normalize_shorthand_tool(cls, values: Any) -> Any:
        return _normalize_tool(values)


class _ChatMessageBase(_ChatCompletionsModel):
    message_id: str | None = Field(default=None, description="Message identifier.")
    content: list[ChatContentPart] | None = Field(default=None, description="Structured message content.")
    tools_state_id: str | None = Field(default=None, description="Tool execution state identifier.")
    inline_data: ChatInlineData | None = Field(default=None, description="Message-level inline data.")
    function_call: ChatFunctionCall | None = Field(default=None, description="Function call payload.")
    tool_execution: ChatToolExecution | None = Field(default=None, description="Tool execution state.")
    logprobs: list[ChatLogprob] | None = Field(default=None, description="Logprob metadata.")
    finish_reason: str | None = Field(default=None, description="Generation finish reason.")

    @model_validator(mode="before")
    @classmethod
    def _normalize_fields(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        values = dict(values)

        _normalize_tools_state_id(values)

        return values

    @field_validator(
        "content",
        mode="before",
        json_schema_input_type=str | dict[str, Any] | list[str | ChatContentPart | dict[str, Any]] | None,
    )
    @classmethod
    def _normalize_content(cls, value: Any) -> Any:
        return _normalize_content_parts(value)


class ChatMessage(_ChatMessageBase):
    """Message for the primary chat completions contract."""

    role: str = Field(description="Message author role.")


class ChatMessageChunk(_ChatMessageBase):
    """Streaming message fragment for the primary chat completions contract."""

    role: str | None = Field(default=None, description="Message author role.")


class ChatCompletionRequest(_ChatCompletionsModel):
    """Primary chat completions request."""

    model: str | None = Field(default=None, description="Model identifier.")
    messages: list[ChatMessage] = Field(description="Chat messages.")
    assistant_id: str | None = Field(default=None, description="Assistant identifier.")
    tools_state_id: str | None = Field(default=None, description="Tool execution state identifier.")
    ranker_options: ChatRankerOptions | None = None
    model_options: ChatModelOptions | None = Field(default=None, description="Model generation options.")
    additional_fields: dict[str, Any] | None = Field(
        default=None, description="Additional fields to merge into the API request body."
    )
    storage: ChatStorage | bool | None = Field(
        default=None,
        description="Thread storage settings. `True` enables storage with defaults; `False` disables it.",
    )
    tool_config: ChatToolConfig | None = Field(default=None, description="Tool calling configuration.")
    tools: list[ChatTool] | None = Field(default=None, description="Available tools.")
    user_info: ChatUserInfo | None = Field(default=None, description="End-user metadata.")
    stream: bool | None = Field(default=None, description="Stream response fragments.")
    disable_filter: bool | None = Field(default=None, description="Disable filtering.")
    profanity_check: bool | None = Field(
        default=None,
        exclude=True,
        description="Enable profanity filtering.",
    )
    flags: list[str] | None = Field(default=None, description="Feature flags.")

    @model_validator(mode="before")
    @classmethod
    def _normalize_fields(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        values = dict(values)

        _normalize_tools_state_id(values)

        storage = values.get("storage")
        if storage is True:
            values["storage"] = {}
        elif storage is False:
            values["storage"] = None

        model_options = values.get("model_options")
        if model_options is None:
            model_options = {}
        elif isinstance(model_options, BaseModel):
            model_options = model_options.model_dump(exclude_unset=True, by_alias=True)
        elif not isinstance(model_options, dict):
            return values
        else:
            model_options = dict(model_options)

        for field_name in (*ChatModelOptions.model_fields, "preset", "unnormalized_history", "top_logprobs"):
            if field_name in values:
                model_options.setdefault(field_name, values.pop(field_name))

        if model_options:
            values["model_options"] = model_options

        return values

    @model_validator(mode="after")
    def _map_profanity_check(self) -> "ChatCompletionRequest":
        if self.disable_filter is None and self.profanity_check is not None:
            self.disable_filter = not self.profanity_check
        return self

    @property
    def reasoning(self) -> ChatReasoning | None:
        """Return reasoning settings from model options."""
        if self.model_options is None:
            return None
        return self.model_options.reasoning

    @reasoning.setter
    def reasoning(self, value: ChatReasoning | None) -> None:
        if self.model_options is None:
            self.model_options = ChatModelOptions()
        self.model_options.reasoning = value

    @property
    def response_format(self) -> ChatResponseFormat | None:
        """Return response format settings from model options."""
        if self.model_options is None:
            return None
        return self.model_options.response_format

    @response_format.setter
    def response_format(self, value: ChatResponseFormat | None) -> None:
        if self.model_options is None:
            self.model_options = ChatModelOptions()
        self.model_options.response_format = value


class ChatCompletionResponse(_ChatCompletionsAPIResponse):
    """Primary chat completions response."""

    model: str | None = Field(default=None, description="Resolved model identifier.")
    created_at: int | None = Field(default=None, description="Response creation timestamp.")
    messages: list[ChatMessage] = Field(description="Returned chat messages.")
    message_id: str | None = Field(default=None, description="Message identifier.")
    thread_id: str | None = Field(default=None, description="Thread identifier.")
    finish_reason: str | None = Field(default=None, description="Generation finish reason.")
    usage: ChatUsage | None = Field(default=None, description="Usage information.")
    tool_execution: ChatToolExecution | None = Field(default=None, description="Top-level tool execution state.")
    logprobs: list[ChatLogprob] | None = Field(default=None, description="Top-level logprob metadata.")
    additional_data: dict[str, Any] | list[dict[str, Any]] | None = Field(
        default=None, description="Additional response metadata; legacy lists remain supported."
    )
    error_details: dict[str, Any] | None = Field(default=None, description="Completion error details.")

    @model_validator(mode="before")
    @classmethod
    def _normalize_fields(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        values = dict(values)

        if values.get("created_at") is None and values.get("created") is not None:
            values["created_at"] = values.pop("created")
        _normalize_tools_state_id(values)

        return values


class ChatCompletionChunk(_ChatCompletionsAPIResponse):
    """Primary chat completions stream chunk."""

    event: str | None = Field(default=None, description="SSE event name.")
    model: str | None = Field(default=None, description="Resolved model identifier.")
    created_at: int | None = Field(default=None, description="Chunk creation timestamp.")
    messages: list[ChatMessageChunk] | None = Field(default=None, description="Returned message fragments.")
    message_id: str | None = Field(default=None, description="Message identifier.")
    thread_id: str | None = Field(default=None, description="Thread identifier.")
    tools_state_id: str | None = Field(default=None, description="Tool execution state identifier.")
    finish_reason: str | None = Field(default=None, description="Generation finish reason.")
    usage: ChatUsage | None = Field(default=None, description="Usage information.")
    tool_execution: ChatToolExecution | None = Field(default=None, description="Top-level tool execution state.")
    logprobs: list[ChatLogprob] | None = Field(default=None, description="Top-level logprob metadata.")
    additional_data: dict[str, Any] | list[dict[str, Any]] | None = Field(
        default=None, description="Additional response metadata; legacy lists remain supported."
    )
    error_details: dict[str, Any] | None = Field(default=None, description="Completion error details.")

    @model_validator(mode="before")
    @classmethod
    def _normalize_fields(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        values = dict(values)

        if values.get("created_at") is None and values.get("created") is not None:
            values["created_at"] = values.pop("created")
        _normalize_tools_state_id(values)

        return values


__all__ = (
    "ChatCompletionChunk",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatContentFile",
    "ChatContentPart",
    "ChatFilterConfig",
    "ChatFilterContentConfig",
    "ChatFilterResponseContentConfig",
    "ChatFunctionCall",
    "ChatFunctionExample",
    "ChatFunctionResult",
    "ChatFunctionSpecification",
    "ChatFunctionsTool",
    "ChatInlineData",
    "ChatLogprob",
    "ChatLogprobToken",
    "ChatMessage",
    "ChatMessageChunk",
    "ChatModelOptions",
    "ChatRankerOptions",
    "ChatReasoning",
    "ChatResponseFormat",
    "ChatSource",
    "ChatStorage",
    "ChatTool",
    "ChatToolConfig",
    "ChatToolExecution",
    "ChatUsage",
    "ChatUsageInputTokensDetails",
    "ChatUserInfo",
    "ChatWebSearchTool",
)
