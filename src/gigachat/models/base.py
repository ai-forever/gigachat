from pydantic import BaseModel, Field


class XHeadersMixin(BaseModel):
    """Mixin adding X-Headers to API responses."""

    x_headers: dict[str, str | None] | None = Field(default=None, description="Service headers")

    @property
    def request_id(self) -> str | None:
        return self.x_headers.get("x-request-id") if self.x_headers else None


class APIResponse(XHeadersMixin):
    """Base class for all API response models."""

    pass
