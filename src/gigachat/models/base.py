from typing import Dict, Optional

from pydantic import BaseModel, Field


class XHeadersMixin(BaseModel):
    """Mixin adding X-Headers to API responses."""

    x_headers: Optional[Dict[str, Optional[str]]] = Field(default=None, description="Service headers")


class APIResponse(XHeadersMixin):
    """Base class for all API response models."""

    pass
