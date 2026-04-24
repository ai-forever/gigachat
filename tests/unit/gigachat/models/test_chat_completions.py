from typing import List

from pydantic import BaseModel

from gigachat.models import ChatCompletionRequest, ChatCompletionResponse, ChatMessage
from gigachat.models.chat_completions import ChatCompletionChunk, ChatResponseFormat


class WeatherAnswer(BaseModel):
    answer: str
    citations: List[str]


def test_chat_completion_request_round_trip() -> None:
    payload = {
        "assistant_id": "assistant-1",
        "messages": [
            {
                "role": "system",
                "content": "Верни JSON-ответ",
            },
            {
                "role": "user",
                "content": [
                    {"text": "Погода в Москве на три дня"},
                    {"files": [{"id": "0e4d9e4e-9270-465f-b637-d029872ca6e3"}]},
                ],
            },
            {
                "role": "tool",
                "content": [
                    {
                        "function_result": {
                            "name": "gismeteo-get_n_day_weather_forecast",
                            "result": {"status": "success"},
                        }
                    }
                ],
                "tools_state_id": "tools-state-1",
            },
        ],
        "model_options": {
            "preset": "preprocess",
            "temperature": 1.8,
            "top_p": 0.8,
            "max_tokens": 4000,
            "repetition_penalty": 1.0,
            "update_interval": 1,
            "unnormalized_history": False,
            "top_logprobs": 3,
            "reasoning": {"effort": "medium"},
            "response_format": {"type": "json_schema", "schema": WeatherAnswer, "strict": False},
        },
        "filter_config": {
            "request_content": {"neuro": True, "blacklist": True, "whitelist": False},
            "response_content": {"blacklist": True},
        },
        "storage": {
            "thread_id": "thread-1",
            "metadata": {"tenant": "test"},
        },
        "ranker_options": {
            "enabled": True,
            "top_n": 3,
            "embeddings_model": "Embeddings",
        },
        "tool_config": {"mode": "forced", "function_name": "gismeteo-get_n_day_weather_forecast"},
        "tools": [
            {
                "web_search": {
                    "type": "actual_info_web_search",
                    "indexes": ["news"],
                    "flags": ["safe_search"],
                }
            },
            {
                "functions": {
                    "specifications": [
                        {
                            "title": "gismeteo-get_n_day_weather_forecast",
                            "description": "Погода на N дней",
                            "properties": {
                                "location": {"type": "string"},
                                "num_days": {"type": "integer"},
                            },
                            "few_shot_examples": [
                                {
                                    "request": "Погода в Москве на три дня",
                                    "params": {"location": "Moscow", "num_days": 3},
                                }
                            ],
                        }
                    ]
                }
            },
        ],
        "user_info": {"timezone": "Europe/Moscow"},
        "stream": False,
        "disable_filter": False,
        "flags": ["web_search"],
    }

    request = ChatCompletionRequest.model_validate(payload)
    dumped = request.model_dump(exclude_none=True, by_alias=True)

    assert request.messages[0].content is not None
    assert request.messages[0].content[0].text == "Верни JSON-ответ"
    assert request.model_options is not None
    assert isinstance(request.response_format, ChatResponseFormat)
    assert request.response_format.schema_ is not None
    assert request.tools is not None
    assert request.tools[1].functions is not None
    assert request.tools[1].functions.specifications is not None
    assert request.tools[1].functions.specifications[0].name == "gismeteo-get_n_day_weather_forecast"
    assert request.tools[1].functions.specifications[0].parameters["type"] == "object"
    assert dumped["messages"][0]["content"] == [{"text": "Верни JSON-ответ"}]
    assert dumped["model_options"]["response_format"]["schema"]["properties"]["answer"]["title"] == "Answer"
    assert dumped["tools"][1]["functions"]["specifications"][0]["name"] == "gismeteo-get_n_day_weather_forecast"


def test_chat_completion_request_moves_legacy_root_options_to_model_options() -> None:
    request = ChatCompletionRequest.model_validate(
        {
            "messages": [{"role": "user", "content": "Верни JSON"}],
            "model_options": {"temperature": 0.2},
            "reasoning": {"effort": "medium"},
            "response_format": {"type": "json_schema", "schema": WeatherAnswer, "strict": True},
        }
    )

    dumped = request.model_dump(exclude_none=True, by_alias=True)

    assert request.reasoning is not None
    assert request.response_format is not None
    assert request.response_format.strict is True
    assert "reasoning" not in dumped
    assert "response_format" not in dumped
    assert dumped["model_options"]["temperature"] == 0.2
    assert dumped["model_options"]["reasoning"]["effort"] == "medium"
    assert dumped["model_options"]["response_format"]["type"] == "json_schema"


def test_chat_completion_request_accepts_regex_response_format() -> None:
    request = ChatCompletionRequest.model_validate(
        {
            "messages": [{"role": "user", "content": "Верни номер заявки"}],
            "model_options": {
                "response_format": {
                    "type": "regex",
                    "regex": "[A-Z]{2}-[0-9]{4}",
                }
            },
        }
    )

    dumped = request.model_dump(exclude_none=True, by_alias=True)

    assert request.response_format is not None
    assert request.response_format.regex == "[A-Z]{2}-[0-9]{4}"
    assert dumped["model_options"]["response_format"] == {
        "type": "regex",
        "regex": "[A-Z]{2}-[0-9]{4}",
    }


def test_chat_completion_request_accepts_storage_bool_future_shape() -> None:
    request = ChatCompletionRequest.model_validate(
        {
            "messages": [{"role": "user", "content": "Сохрани контекст"}],
            "storage": True,
        }
    )

    dumped = request.model_dump(exclude_none=True, by_alias=True)

    assert request.storage is True
    assert dumped["storage"] is True


def test_chat_completion_response_parses_primary_contract() -> None:
    payload = {
        "model": "GigaChat-2-Max",
        "created_at": 1760434636,
        "thread_id": "thread-1",
        "message_id": "message-1",
        "messages": [
            {
                "message_id": "message-in-array-1",
                "role": "assistant",
                "tools_state_id": "tools-state-1",
                "content": [
                    {
                        "text": "Вот результат",
                        "inline_data": {
                            "images": [],
                            "widgets": [{"type": "search_result", "payload": {"query": "rates"}}],
                            "sources": {
                                "1": {
                                    "url": "https://example.com/rates",
                                    "title": "Официальные курсы валют",
                                }
                            },
                        },
                    },
                    {
                        "files": [
                            {
                                "id": "generated-file-1",
                                "target": "image",
                                "mime": "image/png",
                            }
                        ]
                    },
                ],
                "function_call": {
                    "name": "gismeteo-get_n_day_weather_forecast",
                    "arguments": {"location": "Moscow", "num_days": 3},
                },
                "tool_execution": {
                    "name": "image_generation",
                    "status": "success",
                    "seconds_left": 0,
                    "censored": False,
                },
                "logprobs": [
                    {
                        "chosen": {"token": "Вот", "token_id": 1, "logprob": -0.1},
                        "top": [
                            {"token": "Вот", "token_id": 1, "logprob": -0.1},
                            {"token": "Тут", "token_id": 2, "logprob": -0.4},
                        ],
                    }
                ],
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "input_tokens": 10,
            "input_tokens_details": {"cached_tokens": 2},
            "output_tokens": 20,
            "total_tokens": 28,
        },
        "additional_data": [{"type": "tool_call", "name": "image_generation"}],
    }

    response = ChatCompletionResponse.model_validate(payload)

    assert response.thread_id == "thread-1"
    assert response.messages[0].message_id == "message-in-array-1"
    assert response.messages[0].content is not None
    assert response.messages[0].content[0].inline_data is not None
    assert response.messages[0].content[0].inline_data.sources is not None
    assert response.messages[0].content[0].inline_data.sources["1"].title == "Официальные курсы валют"
    assert response.messages[0].content[0].inline_data.widgets == [
        {"type": "search_result", "payload": {"query": "rates"}}
    ]
    assert response.messages[0].tool_execution is not None
    assert response.messages[0].tool_execution.status == "success"
    assert response.messages[0].logprobs is not None
    assert response.messages[0].logprobs[0].chosen is not None
    assert response.messages[0].logprobs[0].chosen.token == "Вот"
    assert response.usage is not None
    assert response.usage.input_tokens_details is not None
    assert response.usage.input_tokens_details.cached_tokens == 2
    assert response.additional_data == [{"type": "tool_call", "name": "image_generation"}]


def test_chat_completion_response_parses_content_function_call() -> None:
    response = ChatCompletionResponse.model_validate(
        {
            "model": "GigaChat-2-Reasoning",
            "created_at": 1776970679,
            "messages": [
                {
                    "role": "assistant",
                    "tool_state_id": "tool-state-1",
                    "content": [
                        {
                            "function_call": {
                                "name": "get_weather",
                                "arguments": {"location": "Moscow"},
                            }
                        }
                    ],
                    "finish_reason": "function_call",
                }
            ],
        }
    )

    assert response.messages[0].content is not None
    assert response.messages[0].content[0].function_call is not None
    assert response.messages[0].content[0].function_call.name == "get_weather"
    assert response.messages[0].content[0].function_call.arguments == {"location": "Moscow"}


def test_chat_completion_request_normalizes_string_tools() -> None:
    request = ChatCompletionRequest.model_validate(
        {
            "messages": [{"role": "user", "content": "Найди свежие новости"}],
            "tools": ["code_interpreter", "web_search", "functions"],
        }
    )

    dumped = request.model_dump(exclude_none=True, by_alias=True)

    assert request.tools is not None
    assert request.tools[0].code_interpreter == {}
    assert request.tools[1].web_search is not None
    assert request.tools[1].web_search.model_dump(exclude_none=True, by_alias=True) == {}
    assert request.tools[2].functions is not None
    assert request.tools[2].functions.model_dump(exclude_none=True, by_alias=True) == {}
    assert dumped["tools"] == [
        {"code_interpreter": {}},
        {"web_search": {}},
        {"functions": {}},
    ]


def test_chat_tool_accepts_string_shorthand() -> None:
    request = ChatCompletionRequest.model_validate(
        {
            "messages": [{"role": "user", "content": "Запусти код"}],
            "tools": ["code_interpreter"],
        }
    )

    assert request.tools is not None
    tool = request.tools[0]
    assert tool.code_interpreter == {}


def test_chat_message_normalizes_ambiguous_content() -> None:
    message = ChatMessage.model_validate(
        {
            "role": "assistant",
            "content": [
                "Первый фрагмент",
                {"text": "Второй фрагмент"},
            ],
            "functions_state_id": "legacy-tools-state",
        }
    )

    assert message.tools_state_id == "legacy-tools-state"
    assert message.content is not None
    assert [part.text for part in message.content] == ["Первый фрагмент", "Второй фрагмент"]


def test_chat_completion_chunk_accepts_partial_messages() -> None:
    chunk = ChatCompletionChunk.model_validate(
        {
            "model": "GigaChat-2-Max",
            "created": 1760434637,
            "messages": [
                {
                    "content": "Частичный ответ",
                    "tool_execution": {"name": "image_generation", "status": "running", "seconds_left": 5},
                }
            ],
            "usage": {"output_tokens": 4},
        }
    )

    assert chunk.created_at == 1760434637
    assert chunk.messages is not None
    assert chunk.messages[0].content is not None
    assert chunk.messages[0].content[0].text == "Частичный ответ"
    assert chunk.messages[0].tool_execution is not None
    assert chunk.messages[0].tool_execution.seconds_left == 5
