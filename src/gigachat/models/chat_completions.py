import inspect
from typing import Any, Dict, List, Optional, Union

import pydantic
from pydantic import BaseModel, ConfigDict, Field, model_validator

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
        "functions",
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


class _ChatCompletionsModel(BaseModel):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class _ChatCompletionsAPIResponse(APIResponse):
    model_config = ConfigDict(extra="allow", populate_by_name=True)


class ChatSource(_ChatCompletionsModel):
    """Source metadata attached to model output."""

    url: Optional[str] = Field(default=None, description="Source URL.")
    title: Optional[str] = Field(default=None, description="Source title.")


class ChatInlineData(_ChatCompletionsModel):
    """Inline metadata attached to a content part."""

    images: Optional[List[Dict[str, Any]]] = Field(default=None, description="Inline images.")
    sources: Optional[Dict[str, ChatSource]] = Field(default=None, description="Inline sources.")


class ChatContentFile(_ChatCompletionsModel):
    """File reference passed in request content or returned in response content."""

    id_: str = Field(alias="id", description="File identifier.")
    target: Optional[str] = Field(default=None, description="Generated file target.")
    mime: Optional[str] = Field(default=None, description="File MIME type.")


class ChatFunctionResult(_ChatCompletionsModel):
    """Tool result returned back to the model in message content."""

    name: str = Field(description="Tool or function name.")
    result: Any = Field(description="Tool result payload.")


class ChatContentPart(_ChatCompletionsModel):
    """Structured content part for a chat message."""

    text: Optional[str] = Field(default=None, description="Text content.")
    files: Optional[List[ChatContentFile]] = Field(default=None, description="Referenced or generated files.")
    function_result: Optional[ChatFunctionResult] = Field(default=None, description="Tool result payload.")
    inline_data: Optional[ChatInlineData] = Field(default=None, description="Inline metadata.")


class ChatFunctionCall(_ChatCompletionsModel):
    """Requested or emitted function call."""

    name: str = Field(description="Function name.")
    arguments: Any = Field(description="Function arguments.")


class ChatToolExecution(_ChatCompletionsModel):
    """Execution state for built-in or platform tool invocation."""

    name: Optional[str] = Field(default=None, description="Tool name.")
    status: Optional[str] = Field(default=None, description="Execution status.")
    seconds_left: Optional[int] = Field(default=None, description="Seconds until completion.")
    censored: Optional[bool] = Field(default=None, description="Whether execution was censored.")


class ChatLogprobToken(_ChatCompletionsModel):
    """Token logprob entry."""

    token: str = Field(description="Token text.")
    token_id: int = Field(description="Token identifier.")
    logprob: float = Field(description="Token log probability.")


class ChatLogprob(_ChatCompletionsModel):
    """Per-position logprob information."""

    chosen: Optional[ChatLogprobToken] = Field(default=None, description="Chosen token.")
    top: Optional[List[ChatLogprobToken]] = Field(default=None, description="Top candidate tokens.")


class ChatUsageInputTokensDetails(_ChatCompletionsModel):
    """Detailed request token accounting."""

    cached_tokens: Optional[int] = Field(default=None, description="Tokens served from cache.")


class ChatUsage(_ChatCompletionsModel):
    """Usage information for the new chat completions contract."""

    input_tokens: Optional[int] = Field(default=None, description="Input token count.")
    input_tokens_details: Optional[ChatUsageInputTokensDetails] = Field(
        default=None, description="Detailed input token accounting."
    )
    output_tokens: Optional[int] = Field(default=None, description="Output token count.")
    total_tokens: Optional[int] = Field(default=None, description="Total token count.")


class ChatExecutionStep(_ChatCompletionsModel):
    """Execution-step metadata returned by the service."""

    pass


class ChatAdditionalData(_ChatCompletionsModel):
    """Additional response metadata."""

    execution_steps: Optional[List[ChatExecutionStep]] = Field(default=None, description="Execution steps.")


class ChatReasoning(_ChatCompletionsModel):
    """Reasoning controls."""

    effort: Optional[str] = Field(default=None, description="Reasoning effort.")


class ChatModelOptions(_ChatCompletionsModel):
    """Model generation options."""

    preset: Optional[str] = Field(default=None, description="Model preset.")
    temperature: Optional[float] = Field(default=None, description="Sampling temperature.")
    top_p: Optional[float] = Field(default=None, description="Nucleus sampling parameter.")
    max_tokens: Optional[int] = Field(default=None, description="Maximum completion tokens.")
    repetition_penalty: Optional[float] = Field(default=None, description="Repetition penalty.")
    update_interval: Optional[float] = Field(default=None, description="Streaming update interval.")
    unnormalized_history: Optional[bool] = Field(default=None, description="Disable history normalization.")
    top_logprobs: Optional[int] = Field(default=None, description="Top logprobs count.")


class ChatResponseFormat(_ChatCompletionsModel):
    """Response format request for the primary chat completions contract."""

    type: str = Field(default="text", description="Requested response format.")
    schema_: Optional[Union[Dict[str, Any], str]] = Field(
        alias="schema", default=None, description="JSON Schema or raw schema payload."
    )
    strict: Optional[bool] = Field(default=None, description="Strict schema adherence.")

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
    """Filtering settings for one response/request content category."""

    neuro: Optional[bool] = Field(default=None, description="Neuro censor toggle.")
    blacklist: Optional[bool] = Field(default=None, description="Blacklist filter toggle.")
    whitelist: Optional[bool] = Field(default=None, description="Whitelist filter toggle.")


class ChatFilterConfig(_ChatCompletionsModel):
    """Filtering configuration."""

    request_content: Optional[ChatFilterContentConfig] = Field(default=None, description="Request filtering settings.")
    response_content: Optional[ChatFilterContentConfig] = Field(
        default=None, description="Response filtering settings."
    )


class ChatStorage(_ChatCompletionsModel):
    """Context storage configuration."""

    limit: Optional[int] = Field(default=None, description="History size limit.")
    assistant_id: Optional[str] = Field(default=None, description="Assistant identifier.")
    thread_id: Optional[str] = Field(default=None, description="Thread identifier.")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Thread metadata.")


class ChatRankerOptions(_ChatCompletionsModel):
    """Tool or function ranking settings."""

    enabled: Optional[bool] = Field(default=None, description="Whether ranking is enabled.")
    top_n: Optional[int] = Field(default=None, description="Number of ranked tools to keep.")
    embeddings_model: Optional[str] = Field(default=None, description="Embeddings model alias.")


class ChatUserInfo(_ChatCompletionsModel):
    """User metadata that may improve model answers."""

    timezone: Optional[str] = Field(default=None, description="IANA timezone.")


class ChatToolConfig(_ChatCompletionsModel):
    """Tool-calling policy."""

    mode: Optional[str] = Field(default=None, description="Tool calling mode.")
    tool_name: Optional[str] = Field(default=None, description="Forced built-in tool name.")
    function_name: Optional[str] = Field(default=None, description="Forced client function name.")


class ChatFunctionExample(_ChatCompletionsModel):
    """Few-shot example for function specification."""

    request: str = Field(description="User request example.")
    params: Dict[str, Any] = Field(description="Function call parameters example.")


class ChatFunctionSpecification(_ChatCompletionsModel):
    """Client function specification exposed to the model."""

    name: str = Field(description="Function name.")
    description: Optional[str] = Field(default=None, description="Function description.")
    parameters: Dict[str, Any] = Field(description="Function parameters JSON Schema.")
    few_shot_examples: Optional[List[ChatFunctionExample]] = Field(
        default=None, description="Few-shot examples for tool calling."
    )
    return_parameters: Optional[Dict[str, Any]] = Field(default=None, description="Return value JSON Schema.")

    @model_validator(mode="before")
    @classmethod
    def _fix_title_and_parameters(cls, values: Any) -> Any:
        if isinstance(values, dict):
            values = dict(values)

            if values.get("name") in (None, "") and values.get("title"):
                values["name"] = values.pop("title", None)

            if values.get("parameters") in (None, "", {}) and "properties" in values:
                values["parameters"] = {
                    "type": "object",
                    "properties": values.pop("properties", {}),
                }

        return values


class ChatFunctionsTool(_ChatCompletionsModel):
    """Tool wrapper for client-defined functions."""

    specifications: Optional[List[ChatFunctionSpecification]] = Field(
        default=None, description="Available function specifications."
    )


class ChatWebSearchTool(_ChatCompletionsModel):
    """Configuration for the web-search built-in tool."""

    type: Optional[str] = Field(default=None, description="Search mode.")
    indexes: Optional[List[str]] = Field(default=None, description="Search index names.")
    flags: Optional[List[str]] = Field(default=None, description="Provider-specific flags.")


class ChatTool(_ChatCompletionsModel):
    """One tool entry in the tools list."""

    code_interpreter: Optional[Dict[str, Any]] = Field(default=None, description="Code interpreter config.")
    image_generate: Optional[Dict[str, Any]] = Field(default=None, description="Image generation config.")
    web_search: Optional[ChatWebSearchTool] = Field(default=None, description="Web search config.")
    url_content_extraction: Optional[Dict[str, Any]] = Field(default=None, description="URL extraction config.")
    model_3d_generate: Optional[Dict[str, Any]] = Field(default=None, description="3D generation config.")
    functions: Optional[ChatFunctionsTool] = Field(default=None, description="Client function tool config.")

    @model_validator(mode="before")
    @classmethod
    def _normalize_shorthand_tool(cls, values: Any) -> Any:
        return _normalize_tool(values)


class _ChatMessageBase(_ChatCompletionsModel):
    content: Optional[List[ChatContentPart]] = Field(default=None, description="Structured message content.")
    tools_state_id: Optional[str] = Field(default=None, description="Tool execution state identifier.")
    inline_data: Optional[ChatInlineData] = Field(default=None, description="Message-level inline data.")
    function_call: Optional[ChatFunctionCall] = Field(default=None, description="Function call payload.")
    tool_execution: Optional[ChatToolExecution] = Field(default=None, description="Tool execution state.")
    logprobs: Optional[List[ChatLogprob]] = Field(default=None, description="Logprob metadata.")
    finish_reason: Optional[str] = Field(default=None, description="Generation finish reason.")

    @model_validator(mode="before")
    @classmethod
    def _normalize_fields(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        values = dict(values)

        if values.get("tools_state_id") is None and values.get("functions_state_id") is not None:
            values["tools_state_id"] = values.pop("functions_state_id")

        if "content" in values:
            values["content"] = _normalize_content_parts(values.get("content"))

        return values


class ChatMessage(_ChatMessageBase):
    """Message for the primary chat completions contract."""

    role: str = Field(description="Message author role.")


class ChatMessageChunk(_ChatMessageBase):
    """Streaming message fragment for the primary chat completions contract."""

    role: Optional[str] = Field(default=None, description="Message author role.")


class ChatCompletionRequest(_ChatCompletionsModel):
    """Primary chat completions request."""

    model: Optional[str] = Field(default=None, description="Model identifier.")
    messages: List[ChatMessage] = Field(description="Chat messages.")
    assistant_id: Optional[str] = Field(default=None, description="Assistant identifier.")
    tools_state_id: Optional[str] = Field(default=None, description="Tool execution state identifier.")
    model_options: Optional[ChatModelOptions] = Field(default=None, description="Model generation options.")
    reasoning: Optional[ChatReasoning] = Field(default=None, description="Reasoning settings.")
    response_format: Optional[ChatResponseFormat] = Field(default=None, description="Response format settings.")
    filter_config: Optional[ChatFilterConfig] = Field(default=None, description="Filtering configuration.")
    storage: Optional[ChatStorage] = Field(default=None, description="Thread storage settings.")
    ranker_options: Optional[ChatRankerOptions] = Field(default=None, description="Tool ranking settings.")
    tool_config: Optional[ChatToolConfig] = Field(default=None, description="Tool calling configuration.")
    tools: Optional[List[ChatTool]] = Field(default=None, description="Available tools.")
    user_info: Optional[ChatUserInfo] = Field(default=None, description="End-user metadata.")
    stream: Optional[bool] = Field(default=None, description="Stream response fragments.")
    disable_filter: Optional[bool] = Field(default=None, description="Disable filtering.")
    flags: Optional[List[str]] = Field(default=None, description="Feature flags.")

    @model_validator(mode="before")
    @classmethod
    def _normalize_fields(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        values = dict(values)

        if values.get("tools_state_id") is None and values.get("functions_state_id") is not None:
            values["tools_state_id"] = values.pop("functions_state_id")

        return values


class ChatCompletionResponse(_ChatCompletionsAPIResponse):
    """Primary chat completions response."""

    model: Optional[str] = Field(default=None, description="Resolved model identifier.")
    created_at: Optional[int] = Field(default=None, description="Response creation timestamp.")
    messages: List[ChatMessage] = Field(description="Returned chat messages.")
    message_id: Optional[str] = Field(default=None, description="Message identifier.")
    thread_id: Optional[str] = Field(default=None, description="Thread identifier.")
    usage: Optional[ChatUsage] = Field(default=None, description="Usage information.")
    tool_execution: Optional[ChatToolExecution] = Field(default=None, description="Top-level tool execution state.")
    logprobs: Optional[List[ChatLogprob]] = Field(default=None, description="Top-level logprob metadata.")
    additional_data: Optional[ChatAdditionalData] = Field(default=None, description="Additional response metadata.")

    @model_validator(mode="before")
    @classmethod
    def _normalize_fields(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        values = dict(values)

        if values.get("created_at") is None and values.get("created") is not None:
            values["created_at"] = values.pop("created")

        return values


class ChatCompletionChunk(_ChatCompletionsAPIResponse):
    """Primary chat completions stream chunk."""

    model: Optional[str] = Field(default=None, description="Resolved model identifier.")
    created_at: Optional[int] = Field(default=None, description="Chunk creation timestamp.")
    messages: Optional[List[ChatMessageChunk]] = Field(default=None, description="Returned message fragments.")
    message_id: Optional[str] = Field(default=None, description="Message identifier.")
    thread_id: Optional[str] = Field(default=None, description="Thread identifier.")
    usage: Optional[ChatUsage] = Field(default=None, description="Usage information.")
    tool_execution: Optional[ChatToolExecution] = Field(default=None, description="Top-level tool execution state.")
    logprobs: Optional[List[ChatLogprob]] = Field(default=None, description="Top-level logprob metadata.")
    additional_data: Optional[ChatAdditionalData] = Field(default=None, description="Additional response metadata.")

    @model_validator(mode="before")
    @classmethod
    def _normalize_fields(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        values = dict(values)

        if values.get("created_at") is None and values.get("created") is not None:
            values["created_at"] = values.pop("created")

        return values


__all__ = (
    "ChatAdditionalData",
    "ChatCompletionChunk",
    "ChatCompletionRequest",
    "ChatCompletionResponse",
    "ChatContentFile",
    "ChatContentPart",
    "ChatExecutionStep",
    "ChatFilterConfig",
    "ChatFilterContentConfig",
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
