import requests
import logging
from typing import List, Optional

from app.models.chat import Message
from app.models.song import Traits

from requests import Response, RequestException
from fastapi import HTTPException




class ChatService:

    def __init__(self, chat_url: str):
        self.chat_url = chat_url

    def extract_song_traits(self, query: Message) -> Traits:
        try:
            response = self._make_request("POST", f"{self.chat_url}/extract_traits", json=query.model_dump())
            traits = Traits.parse_obj(response.json())
            return traits
        except RequestException as e:
            logging.error(f"Failed to get song traits from query {query}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    def _make_request(self, method: str, url: str, **kwargs) -> Response:
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except RequestException as e:
            logging.error(f"HTTP {method} request to {url} failed: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)