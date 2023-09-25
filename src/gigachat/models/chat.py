from typing import List, Optional

from gigachat.models.messages import Messages
from gigachat.pydantic_v1 import BaseModel

LATEST_MODEL = "GigaChat:latest"


class Chat(BaseModel):
    model: str = LATEST_MODEL
    messages: List[Messages]
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    n: Optional[int] = None
    stream: Optional[bool] = None
    max_tokens: Optional[int] = None
    repetition_penalty: Optional[float] = None
    update_interval: Optional[float] = None
    profanity_check: Optional[bool] = None
