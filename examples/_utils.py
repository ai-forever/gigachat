"""Shared helpers for runnable examples."""

from collections.abc import Iterable
from typing import Any


def message_text(message: Any) -> str:
    """Return combined text from a chat-completions message."""
    content = message.get("content") if isinstance(message, dict) else message.content
    if content is None:
        return ""

    parts: list[str] = []
    for part in content:
        text = part.get("text") if isinstance(part, dict) else part.text
        if text:
            parts.append(text)
    return "".join(parts)


def first_message_text(response: Any) -> str:
    """Return combined text from the first response message."""
    return message_text(response.messages[0])


def print_stream_text(chunks: Iterable[Any]) -> None:
    """Print text fragments from a sync stream."""
    for chunk in chunks:
        if chunk.messages:
            print(message_text(chunk.messages[0]), end="", flush=True)
    print()


def message_file_ids(message: Any) -> list[str]:
    """Return file IDs from generated or referenced content parts."""
    content = message.get("content") if isinstance(message, dict) else message.content
    if content is None:
        return []

    file_ids: list[str] = []
    for part in content:
        files = part.get("files") if isinstance(part, dict) else part.files
        for file_ in files or []:
            file_id = file_.get("id") if isinstance(file_, dict) else file_.id_
            if file_id:
                file_ids.append(file_id)
    return file_ids


def message_sources(message: Any) -> list[tuple[str, str]]:
    """Return unique sources from inline data."""
    content = message.get("content") if isinstance(message, dict) else message.content
    if content is None:
        return []

    seen: set[tuple[str, str]] = set()
    sources: list[tuple[str, str]] = []
    for part in content:
        inline_data = part.get("inline_data") if isinstance(part, dict) else part.inline_data
        inline_sources = None
        if isinstance(inline_data, dict):
            inline_sources = inline_data.get("sources")
        elif inline_data is not None:
            inline_sources = inline_data.sources

        for source in (inline_sources or {}).values():
            title = source.get("title") if isinstance(source, dict) else source.title
            url = source.get("url") if isinstance(source, dict) else source.url
            key = (title or "Untitled source", url or "")
            if key not in seen:
                seen.add(key)
                sources.append(key)

    return sources
