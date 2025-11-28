from typing import Dict, Optional

from gigachat.pydantic_v1 import BaseModel, Field


class WithXHeaders(BaseModel):
    """Base model for responses containing X-Headers."""

    x_headers: Optional[Dict[str, Optional[str]]] = Field(default=None)
    """Service headers (x-request-id, x-session-id, x-client-id)."""
