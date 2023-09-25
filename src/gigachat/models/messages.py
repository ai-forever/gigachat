from gigachat.models.messages_role import MessagesRole
from gigachat.pydantic_v1 import BaseModel


class Messages(BaseModel):
    role: MessagesRole
    content: str

    class Config:
        use_enum_values = True
