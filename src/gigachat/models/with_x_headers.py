from typing import Dict, Optional

from gigachat.pydantic_v1 import BaseModel, Field


class WithXHeaders(BaseModel):
    x_headers: Optional[Dict[str, Optional[str]]] = Field(default=None)
    """Служебная информация о запросе (x-request-id, x-session-id, x-client-id)"""
