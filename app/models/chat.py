from __future__ import annotations

from pydantic import BaseModel
from typing import Optional, List


# https://fastapi.tiangolo.com/tutorial/body/
class Message(BaseModel):
    query: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Fast paced country music."
            }
        }