from __future__ import annotations

from pydantic import BaseModel
from typing import Optional, List
from app.models.song import Traits, Song


# https://fastapi.tiangolo.com/tutorial/body/
class Message(BaseModel):
    query: str
    role: Optional[str] = None
    chat_id: Optional[str] = None
    agent_name: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "query": "Fast paced country music."
            }
        }


class ChatData(BaseModel):
    chat_id: Optional[str] = None
    role: Optional[str] = None
    content: Optional[str] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    agent_id: Optional[str] = None
    agent_name: Optional[str] = None


class ChatResponse(BaseModel):
    content: str
    traits: Optional[Traits]


class WebChat(BaseModel):
    content: str
    songs: Optional[List[Song]]
