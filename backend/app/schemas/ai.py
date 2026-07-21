from pydantic import BaseModel
from typing import Optional, Literal


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class AIQueryRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []
    provider: str = ""
    model: str = ""


class AIAction(BaseModel):
    action_type: Literal["update_task", "adjust_dates", "generate_doc", "none"]
    params: dict = {}
    summary: str = ""


class AIStreamEvent(BaseModel):
    type: Literal["text", "action", "error", "done"]
    content: str = ""
    action: Optional[AIAction] = None
