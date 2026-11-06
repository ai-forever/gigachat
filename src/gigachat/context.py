"""Carry request-local header values and chat endpoint overrides.

Headers merge case-insensitively: HTTP-client defaults, SDK headers, named
ContextVars, custom headers, view headers, then per-call headers. The settings
session ID is a fallback below explicit header sources. External Authorization bypasses SDK token acquisition/refresh.
IDs remain independent opaque values; no distributed trace or span is created.
Reset set() tokens in finally blocks. New asyncio tasks inherit their creator's
context snapshot; arbitrary thread executors need explicit propagation.
"""

from contextvars import ContextVar

__all__ = [
    "authorization_cvar",
    "client_id_cvar",
    "request_id_cvar",
    "session_id_cvar",
    "service_id_cvar",
    "operation_id_cvar",
    "trace_id_cvar",
    "agent_id_cvar",
    "custom_headers_cvar",
    "chat_url_cvar",
    "chat_completions_url_cvar",
]

authorization_cvar: ContextVar[str | None] = ContextVar("authorization_cvar", default=None)
"""Complete external Authorization header value, managed by the caller."""
client_id_cvar: ContextVar[str | None] = ContextVar("client_id_cvar", default=None)
"""Unique client ID."""
request_id_cvar: ContextVar[str | None] = ContextVar("request_id_cvar", default=None)
"""Unique request ID."""
session_id_cvar: ContextVar[str | None] = ContextVar("session_id_cvar", default=None)
"""Unique session ID."""
service_id_cvar: ContextVar[str | None] = ContextVar("service_id_cvar", default=None)
"""Unique service ID."""
operation_id_cvar: ContextVar[str | None] = ContextVar("operation_id_cvar", default=None)
"""Opaque application operation ID; not necessarily a span ID."""
trace_id_cvar: ContextVar[str | None] = ContextVar("trace_id_cvar", default=None)
"""Opaque application trace ID; no tracing system is created."""
agent_id_cvar: ContextVar[str | None] = ContextVar("agent_id_cvar", default=None)
"""Unique agent ID."""
custom_headers_cvar: ContextVar[dict[str, str] | None] = ContextVar("custom_headers_cvar", default=None)
"""Headers overriding named ContextVars, below view and per-call headers."""
chat_url_cvar: ContextVar[str] = ContextVar("chat_url_cvar", default="/chat/completions")
"""Legacy chat endpoint URL override; not an HTTP header."""
chat_completions_url_cvar: ContextVar[str | None] = ContextVar("chat_completions_url_cvar", default=None)
"""Override the primary chat endpoint URL; not an HTTP header.

``None`` means use the SDK default (``/v2/chat/completions`` on the client's origin).
"""
