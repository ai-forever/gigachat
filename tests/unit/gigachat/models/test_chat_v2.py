from typing import Literal

import pydantic
import pytest
from pydantic import BaseModel, ValidationError

from gigachat.models.chat_v2 import (
    ChatCompletionV2,
    ChatV2,
    ChatV2ContentPart,
    ChatV2Tool,
)
from tests.utils import get_json


def test_chat_v2_accepts_arbitrary_roles() -> None:
    chat = ChatV2(
        model="GigaChat-2-Max",
        messages=[{"role": "reasoning", "content": "hidden chain of thought"}],
    )

    assert chat.messages[0].role == "reasoning"
    assert chat.messages[0].content[0].text == "hidden chain of thought"


def test_chat_v2_content_part_requires_payload() -> None:
    with pytest.raises(ValidationError):
        ChatV2ContentPart()


def test_chat_v2_tool_requires_exactly_one_kind() -> None:
    with pytest.raises(ValidationError):
        ChatV2Tool(code_interpreter={}, image_generate={})


def test_chat_v2_tool_from_name_accepts_builtin_shorthand() -> None:
    tool = ChatV2Tool.from_name("web_search")

    assert tool.model_dump(exclude_none=True) == {"web_search": {}}


def test_chat_v2_tool_from_name_rejects_unknown_shorthand() -> None:
    with pytest.raises(ValueError, match="Unknown tool shorthand"):
        ChatV2Tool.from_name("unknown_tool")


def test_chat_v2_tool_web_search_factory_serializes_to_empty_config() -> None:
    tool = ChatV2Tool.web_search_tool()

    assert tool.model_dump(exclude_none=True) == {"web_search": {}}


def test_chat_v2_tool_web_search_factory_accepts_config() -> None:
    tool = ChatV2Tool.web_search_tool(type="search", indexes=["news"], flags=["fresh"])

    assert tool.model_dump(exclude_none=True) == {
        "web_search": {"type": "search", "indexes": ["news"], "flags": ["fresh"]}
    }


def test_chat_v2_tool_builtin_factories_dump_expected_payloads() -> None:
    assert ChatV2Tool.code_interpreter_tool().model_dump(exclude_none=True) == {"code_interpreter": {}}
    assert ChatV2Tool.image_generate_tool().model_dump(exclude_none=True) == {"image_generate": {}}
    assert ChatV2Tool.url_content_extraction_tool().model_dump(exclude_none=True) == {
        "url_content_extraction": {}
    }
    assert ChatV2Tool.model_3d_generate_tool().model_dump(exclude_none=True) == {"model_3d_generate": {}}
    assert ChatV2Tool.functions_tool().model_dump(exclude_none=True) == {"functions": {}}


def test_chat_v2_accepts_tool_string_shorthand() -> None:
    chat = ChatV2(
        model="GigaChat-2-Max",
        messages=[{"role": "user", "content": "hi"}],
        tools=["web_search", "image_generate"],
    )

    assert [tool.model_dump(exclude_none=True) for tool in chat.tools or []] == [
        {"web_search": {}},
        {"image_generate": {}},
    ]


def test_chat_v2_tool_config_forced_requires_exactly_one_target() -> None:
    with pytest.raises(ValidationError):
        ChatV2(
            model="GigaChat-2-Max",
            messages=[{"role": "user", "content": "hi"}],
            tool_config={"mode": "forced"},
        )

    with pytest.raises(ValidationError):
        ChatV2(
            model="GigaChat-2-Max",
            messages=[{"role": "user", "content": "hi"}],
            tool_config={"mode": "forced", "tool_name": "image_generate", "function_name": "weather-get"},
        )


def test_chat_v2_response_format_bare_basemodel() -> None:
    class Answer(BaseModel):
        answer: str

    chat = ChatV2(
        model="GigaChat-2-Max",
        messages=[{"role": "user", "content": "hi"}],
        model_options={"response_format": Answer},
    )

    dumped = chat.model_dump(exclude_none=True, by_alias=True)
    assert dumped["model_options"]["response_format"]["type"] == "json_schema"
    assert dumped["model_options"]["response_format"]["schema"]["type"] == "object"


def test_chat_v2_response_format_bare_type_adapter() -> None:
    adapter = pydantic.TypeAdapter(list[Literal["yes", "no"]])

    chat = ChatV2(
        model="GigaChat-2-Max",
        messages=[{"role": "user", "content": "hi"}],
        model_options={"response_format": adapter},
    )

    dumped = chat.model_dump(exclude_none=True, by_alias=True)
    assert dumped["model_options"]["response_format"]["type"] == "json_schema"
    assert dumped["model_options"]["response_format"]["schema"]["type"] == "array"


def test_chat_v2_json_schema_requires_schema() -> None:
    with pytest.raises(ValidationError):
        ChatV2(
            model="GigaChat-2-Max",
            messages=[{"role": "user", "content": "hi"}],
            model_options={"response_format": {"type": "json_schema"}},
        )


def test_chat_v2_assistant_and_model_are_mutually_exclusive() -> None:
    with pytest.raises(ValidationError):
        ChatV2(
            model="GigaChat-2-Max",
            assistant_id="assistant-1",
            messages=[{"role": "user", "content": "hi"}],
        )


def test_chat_v2_assistant_and_storage_thread_are_mutually_exclusive() -> None:
    with pytest.raises(ValidationError):
        ChatV2(
            assistant_id="assistant-1",
            storage={"thread_id": "thread-1"},
            messages=[{"role": "user", "content": "hi"}],
        )


def test_chat_v2_storage_bool_passthrough() -> None:
    chat = ChatV2(model="GigaChat-2-Max", messages=[{"role": "user", "content": "hi"}], storage=True)

    assert chat.storage is True
    assert chat.model_dump(exclude_none=True)["storage"] is True


def test_chat_completion_v2_message_logprobs() -> None:
    completion = ChatCompletionV2.model_validate(get_json("chat_completion_v2.json"))

    assert completion.messages[0].content[5].logprobs is not None
    assert completion.messages[0].content[5].logprobs[0].chosen.token == "Вот"
    assert completion.usage is not None
    assert completion.usage.input_tokens_details is not None
    assert completion.usage.input_tokens_details.cached_tokens == 2
