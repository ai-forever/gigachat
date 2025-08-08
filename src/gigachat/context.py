from contextvars import ContextVar
from typing import Dict, Optional

authorization_cvar: ContextVar[Optional[str]] = ContextVar("authorization_cvar", default=None)
"""Информация об авторизации с помощью JWE"""
client_id_cvar: ContextVar[Optional[str]] = ContextVar("client_id_cvar", default=None)
"""Уникальный ID клиента"""
request_id_cvar: ContextVar[Optional[str]] = ContextVar("request_id_cvar", default=None)
"""Уникальный ID запроса"""
session_id_cvar: ContextVar[Optional[str]] = ContextVar("session_id_cvar", default=None)
"""Уникальный ID сессии"""
service_id_cvar: ContextVar[Optional[str]] = ContextVar("service_id_cvar", default=None)
"""Уникальный ID сервиса"""
operation_id_cvar: ContextVar[Optional[str]] = ContextVar("operation_id_cvar", default=None)
"""Информация об авторизации с помощью JWE"""
trace_id_cvar: ContextVar[Optional[str]] = ContextVar("trace_id_cvar", default=None)
"""Уникальный ID экземпляра процесса (основной операции)"""
agent_id_cvar: ContextVar[Optional[str]] = ContextVar("agent_id_cvar", default=None)
"""Уникальный ID агента"""
custom_headers_cvar: ContextVar[Optional[Dict[str, str]]] = ContextVar("custom_headers_cvar", default=None)
"""Дополнительные HTTP-заголовки, которые будут добавлены к запросу"""
chat_url_cvar: ContextVar[str] = ContextVar("chat_url_cvar", default="/chat/completions")
"""Пользовательский URL для chat/completions, если требуется использовать другой URL для чата"""
