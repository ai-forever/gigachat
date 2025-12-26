from contextvars import ContextVar
from typing import Dict, Optional

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
]

authorization_cvar: ContextVar[Optional[str]] = ContextVar("authorization_cvar", default=None)
"""Authorization information using JWE."""
client_id_cvar: ContextVar[Optional[str]] = ContextVar("client_id_cvar", default=None)
"""Unique client ID."""
request_id_cvar: ContextVar[Optional[str]] = ContextVar("request_id_cvar", default=None)
"""Unique request ID."""
session_id_cvar: ContextVar[Optional[str]] = ContextVar("session_id_cvar", default=None)
"""Unique session ID."""
service_id_cvar: ContextVar[Optional[str]] = ContextVar("service_id_cvar", default=None)
"""Unique service ID."""
operation_id_cvar: ContextVar[Optional[str]] = ContextVar("operation_id_cvar", default=None)
"""Unique operation ID."""
trace_id_cvar: ContextVar[Optional[str]] = ContextVar("trace_id_cvar", default=None)
"""Unique process instance ID (main operation)."""
agent_id_cvar: ContextVar[Optional[str]] = ContextVar("agent_id_cvar", default=None)
"""Unique agent ID."""
custom_headers_cvar: ContextVar[Optional[Dict[str, str]]] = ContextVar("custom_headers_cvar", default=None)
"""Additional HTTP headers to be added to the request."""
chat_url_cvar: ContextVar[str] = ContextVar("chat_url_cvar", default="/chat/completions")
"""Custom URL for chat/completions if a different chat URL is required."""
