from gigachat.pydantic_v1 import BaseModel


class Token(BaseModel):
    tok: str
    exp: int
