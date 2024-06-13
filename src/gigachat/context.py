from contextvars import ContextVar
from typing import Optional

authorization_cvar: ContextVar[Optional[str]] = ContextVar("authorization_cvar", default=None)
"""Информация об авторизации с помощью JWE"""
client_id_cvar: ContextVar[Optional[str]] = ContextVar("client_id_cvar", default=None)
"""Уникальный ID клиента"""
request_id_cvar: ContextVar[Optional[str]] = ContextVar("request_id_cvar", default=None)
"""Уникальный ID запроса"""
session_id_cvar: ContextVar[Optional[str]] = ContextVar("session_id_cvar", default=None)
"""Уникальный ID сессии"""
service_id_cvar: ContextVar[Optional[str]] = ContextVar("service_id_cvar", default=None)
operation_id_cvar: ContextVar[Optional[str]] = ContextVar("operation_id_cvar", default=None)
