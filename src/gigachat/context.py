"""Context variables for distributed tracing and request identification.

These variables are injected into HTTP headers via :func:`gigachat.api.utils.build_headers`
and allow passing tracing/auth context without threading it through every call.

Mapping to HTTP headers
-----------------------

================================  ====================
Context Variable                  HTTP Header
================================  ====================
``authorization_cvar``            ``Authorization``
``client_id_cvar``                ``X-Client-ID``
``request_id_cvar``               ``X-Request-ID``
``session_id_cvar``               ``X-Session-ID``
``service_id_cvar``               ``X-Service-ID``
``operation_id_cvar``             ``X-Operation-ID``
``trace_id_cvar``                 ``X-Trace-ID``
``agent_id_cvar``                 ``X-Agent-ID``
================================  ====================

Tracing semantics
-----------------

- **trace_id** — identifies an entire business transaction (correlation ID).
  Stays the same across all calls within one logical operation.
- **request_id** — identifies a single incoming client request.
  May equal trace_id when there is one request per transaction.
- **operation_id** — identifies an individual outgoing call (span ID).
  Should be regenerated for every call to an external system.
- **session_id** — ties multiple requests to a single user session.

Example::

    from gigachat.context import trace_id_cvar, request_id_cvar, operation_id_cvar

    # Set once per incoming request
    trace_id_cvar.set("tx-001")
    request_id_cvar.set("req-abc")

    # Set a new span for each outgoing call
    operation_id_cvar.set("span-1")
    response_1 = gigachat.chat(...)

    operation_id_cvar.set("span-2")
    response_2 = gigachat.chat(...)
"""

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
"""JWE token for authorization. Sent as the ``Authorization`` header, overriding the default token."""

client_id_cvar: ContextVar[Optional[str]] = ContextVar("client_id_cvar", default=None)
"""Unique client identifier. Sent as ``X-Client-ID``."""

request_id_cvar: ContextVar[Optional[str]] = ContextVar("request_id_cvar", default=None)
"""Unique incoming request identifier. Sent as ``X-Request-ID``."""

session_id_cvar: ContextVar[Optional[str]] = ContextVar("session_id_cvar", default=None)
"""User session identifier. Sent as ``X-Session-ID``."""

service_id_cvar: ContextVar[Optional[str]] = ContextVar("service_id_cvar", default=None)
"""Calling service identifier. Sent as ``X-Service-ID``."""

operation_id_cvar: ContextVar[Optional[str]] = ContextVar("operation_id_cvar", default=None)
"""Individual operation (span) identifier for tracing. Sent as ``X-Operation-ID``."""

trace_id_cvar: ContextVar[Optional[str]] = ContextVar("trace_id_cvar", default=None)
"""End-to-end trace identifier (correlation ID) for the entire business transaction. Sent as ``X-Trace-ID``."""

agent_id_cvar: ContextVar[Optional[str]] = ContextVar("agent_id_cvar", default=None)
"""Agent identifier. Sent as ``X-Agent-ID``."""

custom_headers_cvar: ContextVar[Optional[Dict[str, str]]] = ContextVar("custom_headers_cvar", default=None)
"""Additional HTTP headers to be added to every request."""

chat_url_cvar: ContextVar[str] = ContextVar("chat_url_cvar", default="/chat/completions")
"""Custom URL path for chat completions endpoint."""
