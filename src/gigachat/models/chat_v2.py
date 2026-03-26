from __future__ import annotations

import inspect
from typing import Any, Dict, List, Literal, Optional, Type, Union, get_origin

import pydantic
from pydantic import AliasChoices, BaseModel, Field, model_validator

from gigachat.models._schema_normalize import to_strict_json_schema
from gigachat.models.base import APIResponse
from gigachat.models.chat import Function, FunctionCall


class ChatV2FileDescriptor(BaseModel):
    """File reference used in v2 content parts."""

    id: str = Field(description="File identifier.")
    target: Optional[str] = Field(default=None, description="Generated file target.")
    mime: Optional[str] = Field(default=None, description="MIME type.")


class ChatV2FunctionResult(BaseModel):
    """Result of a client-side function execution."""

    name: str = Field(description="Function name.")
    result: Union[Dict[str, Any], str] = Field(description="Function result payload.")


class ChatV2ToolExecution(BaseModel):
    """Information about a platform tool execution."""

    name: str = Field(description="Tool name.")
    status: Optional[str] = Field(default=None, description="Execution status.")
    seconds_left: Optional[int] = Field(default=None, description="Estimated seconds left for streaming runs.")
    censored: Optional[bool] = Field(default=None, description="Whether the tool output was censored.")


class ChatV2LogProbToken(BaseModel):
    """Token log-probability information."""

    token: str = Field(description="Token text.")
    token_id: Optional[int] = Field(default=None, description="Token identifier.")
    logprob: float = Field(description="Token log probability.")


class ChatV2MessageLogProb(BaseModel):
    """Log probabilities for one generated token position."""

    chosen: ChatV2LogProbToken = Field(description="Chosen token.")
    top: List[ChatV2LogProbToken] = Field(description="Top candidate tokens.")


class ChatV2ContentPart(BaseModel):
    """One structured content part inside a v2 message."""

    inline_data: Optional[Dict[str, Any]] = Field(default=None, description="Additional inline data.")
    text: Optional[str] = Field(default=None, description="Text content.")
    files: Optional[List[ChatV2FileDescriptor]] = Field(default=None, description="Attached or generated files.")
    function_result: Optional[ChatV2FunctionResult] = Field(default=None, description="Client function result.")
    function_call: Optional[FunctionCall] = Field(default=None, description="Requested function call.")
    tool_execution: Optional[ChatV2ToolExecution] = Field(default=None, description="Platform tool execution info.")
    logprobs: Optional[List[ChatV2MessageLogProb]] = Field(default=None, description="Token log probabilities.")

    @model_validator(mode="before")
    @classmethod
    def _coerce_files(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        values = dict(values)
        files = values.get("files")
        if isinstance(files, str):
            values["files"] = [{"id": files}]
        elif isinstance(files, list):
            values["files"] = [{"id": item} if isinstance(item, str) else item for item in files]

        return values

    @model_validator(mode="after")
    def _validate_payload(self) -> ChatV2ContentPart:
        payload_fields = (
            self.inline_data,
            self.text,
            self.files,
            self.function_result,
            self.function_call,
            self.tool_execution,
            self.logprobs,
        )
        if not any(field is not None for field in payload_fields):
            raise ValueError("ChatV2ContentPart requires at least one payload field")
        return self


class ChatV2Message(BaseModel):
    """Request/response message for v2 chat completions."""

    message_id: Optional[str] = Field(default=None, description="Message identifier.")
    role: str = Field(description="Message role.")
    tools_state_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("tools_state_id", "tool_state_id"),
        description="Tool state identifier.",
    )
    content: List[ChatV2ContentPart] = Field(description="Structured message content.")

    @model_validator(mode="before")
    @classmethod
    def _coerce_content(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        values = dict(values)
        content = values.get("content")
        if isinstance(content, str):
            values["content"] = [{"text": content}]
        elif isinstance(content, dict):
            values["content"] = [content]

        return values


class ChatV2MessageChunk(BaseModel):
    """Streaming delta message for v2 chat completions."""

    message_id: Optional[str] = Field(default=None, description="Message identifier.")
    role: Optional[str] = Field(default=None, description="Message role.")
    tools_state_id: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("tools_state_id", "tool_state_id"),
        description="Tool state identifier.",
    )
    content: Optional[List[ChatV2ContentPart]] = Field(default=None, description="Structured message content delta.")

    @model_validator(mode="before")
    @classmethod
    def _coerce_content(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        values = dict(values)
        content = values.get("content")
        if isinstance(content, str):
            values["content"] = [{"text": content}]
        elif isinstance(content, dict):
            values["content"] = [content]

        return values


class ChatV2Reasoning(BaseModel):
    """Reasoning configuration."""

    effort: Literal["low", "medium", "high"] = Field(description="Reasoning effort.")


class ChatV2ResponseFormat(BaseModel):
    """Response format configuration for v2 chat completions."""

    type: Literal["text", "json_schema"] = Field(description="Response format type.")
    schema_: Optional[Dict[str, Any]] = Field(default=None, alias="schema", description="JSON Schema definition.")
    strict: Optional[bool] = Field(default=None, description="Strict schema adherence.")

    @model_validator(mode="before")
    @classmethod
    def _validate_and_convert_schema(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        values = dict(values)
        schema = values.get("schema")
        if schema is None:
            return values

        if inspect.isclass(schema) and issubclass(schema, pydantic.BaseModel):
            values["schema"] = to_strict_json_schema(schema)
            return values

        if isinstance(schema, pydantic.TypeAdapter):
            values["schema"] = to_strict_json_schema(schema)
            return values

        if get_origin(schema) is not None:
            values["schema"] = to_strict_json_schema(pydantic.TypeAdapter(schema))
            return values

        if isinstance(schema, dict):
            return values

        raise ValueError(
            "'schema' must be a dict, a pydantic.BaseModel subclass, a supported typing annotation, "
            f"or a pydantic.TypeAdapter; got {type(schema).__name__}"
        )

    @model_validator(mode="after")
    def _require_schema_for_json_schema(self) -> ChatV2ResponseFormat:
        if self.type == "json_schema" and self.schema_ is None:
            raise ValueError("response_format.schema is required when response_format.type='json_schema'")
        return self


ChatV2ResponseFormatInput = Union[ChatV2ResponseFormat, Dict[str, Any], Type[pydantic.BaseModel], Any]


class ChatV2ModelOptions(BaseModel):
    """Model execution options."""

    preset: Optional[str] = Field(default=None, description="Preset name.")
    temperature: Optional[float] = Field(default=None, description="Sampling temperature.")
    top_p: Optional[float] = Field(default=None, description="Nucleus sampling parameter.")
    max_tokens: Optional[int] = Field(default=None, description="Maximum number of generated tokens.")
    repetition_penalty: Optional[float] = Field(default=None, description="Repetition penalty.")
    update_interval: Optional[float] = Field(default=None, description="Streaming update interval.")
    unnormalized_history: Optional[bool] = Field(default=None, description="Disable history normalization.")
    top_logprobs: Optional[int] = Field(default=None, description="Top log-prob count.", ge=1, le=5)
    reasoning: Optional[ChatV2Reasoning] = Field(default=None, description="Reasoning settings.")
    response_format: Optional[ChatV2ResponseFormat] = Field(default=None, description="Response format settings.")


class ChatV2FilterRequestContent(BaseModel):
    """Request filtering configuration."""

    neuro: Optional[bool] = Field(default=None, description="Neuro-model censorship check.")
    blacklist: Optional[bool] = Field(default=None, description="Blacklist regex check.")
    whitelist: Optional[bool] = Field(default=None, description="Whitelist response shortcut.")


class ChatV2FilterResponseContent(BaseModel):
    """Response filtering configuration."""

    blacklist: Optional[bool] = Field(default=None, description="Blacklist regex check.")


class ChatV2FilterConfig(BaseModel):
    """Filter configuration."""

    request_content: Optional[ChatV2FilterRequestContent] = Field(default=None, description="Request filtering.")
    response_content: Optional[ChatV2FilterResponseContent] = Field(default=None, description="Response filtering.")


class ChatV2Storage(BaseModel):
    """Stateful storage configuration."""

    limit: Optional[int] = Field(default=None, description="Maximum number of history messages sent to the model.")
    thread_id: Optional[str] = Field(default=None, description="Thread identifier.")
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Thread metadata.")


class ChatV2RankerOptions(BaseModel):
    """Tool/function ranking settings."""

    enabled: Optional[bool] = Field(default=None, description="Enable ranking.")
    top_n: Optional[int] = Field(default=None, description="Number of ranked items to pass to the model.")
    embeddings_model: Optional[str] = Field(default=None, description="Embeddings model alias for ranking.")


class ChatV2UserInfo(BaseModel):
    """User metadata passed to the model."""

    timezone: Optional[str] = Field(default=None, description="IANA timezone.")


class ChatV2ToolConfig(BaseModel):
    """Tool invocation policy."""

    mode: Literal["auto", "none", "forced"] = Field(description="Tool invocation mode.")
    tool_name: Optional[str] = Field(default=None, description="Forced internal tool name.")
    function_name: Optional[str] = Field(default=None, description="Forced client function name.")

    @model_validator(mode="after")
    def _validate_forced_mode(self) -> ChatV2ToolConfig:
        if self.mode == "forced":
            forced_targets = [self.tool_name is not None, self.function_name is not None]
            if sum(forced_targets) != 1:
                raise ValueError("tool_config.mode='forced' requires exactly one of tool_name or function_name")
        return self


class ChatV2WebSearchTool(BaseModel):
    """Web search tool configuration."""

    type: Optional[str] = Field(default=None, description="Search type.")
    indexes: Optional[List[str]] = Field(default=None, description="Search indexes.")
    flags: Optional[List[str]] = Field(default=None, description="Search flags.")


class ChatV2FunctionsTool(BaseModel):
    """Client functions tool configuration."""

    specifications: Optional[List[Function]] = Field(default=None, description="Client function specifications.")


class ChatV2Tool(BaseModel):
    """One tool entry inside the tools list."""

    code_interpreter: Optional[Dict[str, Any]] = Field(default=None, description="Code interpreter tool config.")
    image_generate: Optional[Dict[str, Any]] = Field(default=None, description="Image generation tool config.")
    web_search: Optional[ChatV2WebSearchTool] = Field(default=None, description="Web search tool config.")
    url_content_extraction: Optional[Dict[str, Any]] = Field(
        default=None, description="URL content extraction tool config."
    )
    model_3d_generate: Optional[Dict[str, Any]] = Field(default=None, description="3D model generation tool config.")
    functions: Optional[ChatV2FunctionsTool] = Field(default=None, description="Client functions tool config.")

    @classmethod
    def from_name(cls, name: str) -> ChatV2Tool:
        """Create a built-in tool from its shorthand name."""

        tool_factories = {
            "code_interpreter": cls.code_interpreter_tool,
            "image_generate": cls.image_generate_tool,
            "web_search": cls.web_search_tool,
            "url_content_extraction": cls.url_content_extraction_tool,
            "model_3d_generate": cls.model_3d_generate_tool,
            "functions": cls.functions_tool,
        }
        try:
            return tool_factories[name]()
        except KeyError as exc:
            allowed = ", ".join(sorted(tool_factories))
            raise ValueError(f"Unknown tool shorthand {name!r}. Expected one of: {allowed}") from exc

    @classmethod
    def code_interpreter_tool(cls) -> ChatV2Tool:
        """Create a code interpreter tool with default configuration."""

        return cls(code_interpreter={})

    @classmethod
    def image_generate_tool(cls) -> ChatV2Tool:
        """Create an image generation tool with default configuration."""

        return cls(image_generate={})

    @classmethod
    def web_search_tool(
        cls,
        *,
        type: Optional[str] = None,
        indexes: Optional[List[str]] = None,
        flags: Optional[List[str]] = None,
    ) -> ChatV2Tool:
        """Create a web search tool with optional configuration."""

        return cls(web_search=ChatV2WebSearchTool(type=type, indexes=indexes, flags=flags))

    @classmethod
    def url_content_extraction_tool(cls) -> ChatV2Tool:
        """Create a URL content extraction tool with default configuration."""

        return cls(url_content_extraction={})

    @classmethod
    def model_3d_generate_tool(cls) -> ChatV2Tool:
        """Create a 3D model generation tool with default configuration."""

        return cls(model_3d_generate={})

    @classmethod
    def functions_tool(cls, specifications: Optional[List[Function]] = None) -> ChatV2Tool:
        """Create a client functions tool with optional specifications."""

        return cls(functions=ChatV2FunctionsTool(specifications=specifications))

    @model_validator(mode="after")
    def _validate_single_tool_kind(self) -> ChatV2Tool:
        kinds = (
            self.code_interpreter,
            self.image_generate,
            self.web_search,
            self.url_content_extraction,
            self.model_3d_generate,
            self.functions,
        )
        if sum(kind is not None for kind in kinds) != 1:
            raise ValueError("ChatV2Tool requires exactly one tool kind")
        return self


class ChatV2InputTokensDetails(BaseModel):
    """Detailed token usage for input."""

    cached_tokens: Optional[int] = Field(default=None, description="Number of cached input tokens.")


class ChatV2Usage(BaseModel):
    """Usage statistics for v2 chat completions."""

    input_tokens: int = Field(description="Number of input tokens.")
    input_tokens_details: Optional[ChatV2InputTokensDetails] = Field(
        default=None, description="Detailed input token information."
    )
    output_tokens: int = Field(description="Number of output tokens.")
    total_tokens: int = Field(description="Total number of tokens.")


class ChatV2AdditionalData(BaseModel):
    """Additional response metadata."""

    execution_steps: Optional[List[Dict[str, Any]]] = Field(default=None, description="Execution steps.")


class ChatV2(BaseModel):
    """Request model for v2/chat/completions."""

    @model_validator(mode="before")
    @classmethod
    def _coerce_input_shorthands(cls, values: Any) -> Any:
        if not isinstance(values, dict):
            return values

        values = dict(values)

        tools = values.get("tools")
        if isinstance(tools, list):
            coerced_tools = []
            for tool in tools:
                if isinstance(tool, str):
                    coerced_tools.append(ChatV2Tool.from_name(tool).model_dump(exclude_none=True))
                else:
                    coerced_tools.append(tool)
            values["tools"] = coerced_tools

        model_options = values.get("model_options")
        if not isinstance(model_options, dict):
            return values

        response_format = model_options.get("response_format")
        if response_format is None:
            return values

        if (
            (inspect.isclass(response_format) and issubclass(response_format, pydantic.BaseModel))
            or isinstance(response_format, pydantic.TypeAdapter)
            or get_origin(response_format) is not None
        ):
            values["model_options"] = dict(model_options)
            values["model_options"]["response_format"] = {"type": "json_schema", "schema": response_format}
            return values

        return values

    model: Optional[str] = Field(default=None, description="Model identifier.")
    assistant_id: Optional[str] = Field(default=None, description="Assistant identifier.")
    messages: List[ChatV2Message] = Field(description="Chat messages.")
    model_options: Optional[ChatV2ModelOptions] = Field(default=None, description="Model configuration.")
    stream: Optional[bool] = Field(default=None, description="Enable SSE streaming.")
    disable_filter: Optional[bool] = Field(default=None, description="Disable filtering.")
    filter_config: Optional[ChatV2FilterConfig] = Field(default=None, description="Filter configuration.")
    flags: Optional[List[str]] = Field(default=None, description="Feature flags.")
    storage: Optional[Union[ChatV2Storage, bool]] = Field(default=None, description="Stateful storage settings.")
    ranker_options: Optional[ChatV2RankerOptions] = Field(default=None, description="Tool ranking configuration.")
    user_info: Optional[ChatV2UserInfo] = Field(default=None, description="User info metadata.")
    tool_config: Optional[ChatV2ToolConfig] = Field(default=None, description="Tool invocation policy.")
    tools: Optional[List[ChatV2Tool]] = Field(default=None, description="Available tools.")
    additional_fields: Optional[Dict[str, Any]] = Field(default=None, description="Additional raw request fields.")

    @model_validator(mode="after")
    def _validate_request(self) -> ChatV2:
        storage_thread_id = self.storage.thread_id if isinstance(self.storage, ChatV2Storage) else None

        if self.assistant_id is not None and self.model is not None:
            raise ValueError("assistant_id and model are mutually exclusive")

        if self.assistant_id is not None and storage_thread_id is not None:
            raise ValueError("assistant_id cannot be used together with storage.thread_id")

        return self


class ChatCompletionV2(APIResponse):
    """Response model for non-streaming v2 chat completions."""

    model: str = Field(description="Model name.")
    thread_id: Optional[str] = Field(default=None, description="Thread identifier.")
    created_at: int = Field(description="Creation timestamp.")
    messages: List[ChatV2Message] = Field(description="Response messages.")
    finish_reason: Optional[str] = Field(default=None, description="Why generation finished.")
    usage: Optional[ChatV2Usage] = Field(default=None, description="Usage statistics.")
    additional_data: Optional[ChatV2AdditionalData] = Field(default=None, description="Additional metadata.")


class ChatCompletionV2Chunk(APIResponse):
    """Response model for streaming v2 chat completions."""

    event: Optional[str] = Field(default=None, description="SSE event name.")
    model: str = Field(description="Model name.")
    thread_id: Optional[str] = Field(default=None, description="Thread identifier.")
    created_at: int = Field(description="Creation timestamp.")
    messages: Optional[List[ChatV2MessageChunk]] = Field(default=None, description="Streaming message deltas.")
    finish_reason: Optional[str] = Field(default=None, description="Why generation finished.")
    usage: Optional[ChatV2Usage] = Field(default=None, description="Usage statistics.")
    additional_data: Optional[ChatV2AdditionalData] = Field(default=None, description="Additional metadata.")

    @model_validator(mode="after")
    def _validate_stream_payload(self) -> ChatCompletionV2Chunk:
        if self.messages is None and self.finish_reason is None and self.usage is None and self.additional_data is None:
            raise ValueError("ChatCompletionV2Chunk requires messages or completion metadata")
        return self
