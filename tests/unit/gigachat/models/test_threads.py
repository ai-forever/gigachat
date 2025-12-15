from gigachat.models.chat import MessagesRole
from gigachat.models.threads import (
    Thread,
    ThreadCompletion,
    ThreadCompletionChunk,
    ThreadMessage,
    ThreadMessages,
    ThreadMessagesResponse,
    ThreadRunOptions,
    ThreadRunResponse,
    ThreadRunResult,
    Threads,
    ThreadStatus,
)


def test_thread_creation() -> None:
    data = {
        "id": "thread-1",
        "model": "GigaChat",
        "created_at": 1,
        "updated_at": 2,
        "run_lock": False,
        "status": "ready",
    }
    thread = Thread.model_validate(data)
    assert thread.id_ == "thread-1"
    assert thread.status == ThreadStatus.READY


def test_threads_creation() -> None:
    data = {
        "threads": [
            {
                "id": "thread-1",
                "model": "GigaChat",
                "created_at": 1,
                "updated_at": 2,
                "run_lock": False,
                "status": "ready",
            }
        ]
    }
    threads = Threads.model_validate(data)
    assert len(threads.threads) == 1
    assert threads.threads[0].id_ == "thread-1"


def test_thread_message_creation() -> None:
    data = {
        "message_id": "msg-1",
        "role": "user",
        "content": "hello",
        "created_at": 123,
        "attachments": [],
    }
    msg = ThreadMessage.model_validate(data)
    assert msg.message_id == "msg-1"
    assert msg.role == MessagesRole.USER


def test_thread_messages_creation() -> None:
    data = {
        "thread_id": "thread-1",
        "messages": [
            {
                "message_id": "msg-1",
                "role": "user",
                "content": "hello",
                "created_at": 123,
            }
        ],
    }
    msgs = ThreadMessages.model_validate(data)
    assert msgs.thread_id == "thread-1"
    assert len(msgs.messages) == 1


def test_thread_messages_response_creation() -> None:
    data = {
        "thread_id": "thread-1",
        "messages": [{"created_at": 123, "message_id": "msg-1"}],
    }
    resp = ThreadMessagesResponse.model_validate(data)
    assert resp.thread_id == "thread-1"
    assert len(resp.messages) == 1


def test_thread_run_options_creation() -> None:
    opts = ThreadRunOptions(temperature=0.5, max_tokens=100)
    assert opts.temperature == 0.5
    assert opts.max_tokens == 100


def test_thread_run_response_creation() -> None:
    data = {
        "status": "in_progress",
        "thread_id": "thread-1",
        "created_at": 123,
    }
    resp = ThreadRunResponse.model_validate(data)
    assert resp.status == ThreadStatus.IN_PROGRESS
    assert resp.thread_id == "thread-1"


def test_thread_run_result_creation() -> None:
    data = {
        "status": "ready",
        "thread_id": "thread-1",
        "updated_at": 456,
        "model": "GigaChat",
        "messages": [],
    }
    res = ThreadRunResult.model_validate(data)
    assert res.status == ThreadStatus.READY
    assert res.model == "GigaChat"


def test_thread_completion_creation() -> None:
    data = {
        "object": "thread.completion",
        "model": "GigaChat",
        "thread_id": "thread-1",
        "message_id": "msg-2",
        "created": 123,
        "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
        "message": {"role": "assistant", "content": "hi"},
        "finish_reason": "stop",
    }
    comp = ThreadCompletion.model_validate(data)
    assert comp.thread_id == "thread-1"
    assert comp.message.content == "hi"


def test_thread_completion_chunk_creation() -> None:
    data = {
        "object": "thread.completion.chunk",
        "model": "GigaChat",
        "thread_id": "thread-1",
        "message_id": "msg-2",
        "created": 123,
        "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
        "choices": [{"delta": {"content": "h"}, "index": 0}],
    }
    chunk = ThreadCompletionChunk.model_validate(data)
    assert chunk.thread_id == "thread-1"
    assert chunk.choices[0].delta.content == "h"
