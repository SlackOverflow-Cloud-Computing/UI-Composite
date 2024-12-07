import requests
import logging
import uuid
from typing import List, Optional

from app.models.chat import Message, ChatData
from app.models.song import Traits

from requests import Response, RequestException
from fastapi import HTTPException


class ChatService:

    def __init__(self, chat_url: str, user_url: str):
        self.chat_url = chat_url
        self.user_url = user_url

    def update_chat_database(self, query: Message) -> str:
        try:
            # TODO: get current user info and send to chat db
            # user_response = self._make_request("GET", f"{self.user_url}/update_chat", json=chat_data.model_dump())
            chat_id = str(uuid.uuid4())  # temporary solution
            chat_data = ChatData(**{
                "chat_id": chat_id,
                "user_id": "",
                "user_name": "",
                "role": query.role,
                "content": query.query,
                "agent_name": query.agent_name
            })
            response = self._make_request("POST", f"{self.chat_url}/update_chat", json=chat_data.model_dump())
            return chat_id
        except RequestException as e:
            logging.error(f"Failed to get update the message to database: {e}")
            raise HTTPException(status_code=500, detail=str(e))


    def extract_song_traits(self, query: Message) -> Traits:
        try:
            response = self._make_request("POST", f"{self.chat_url}/extract_traits", json=query.model_dump())
            traits = Traits.parse_obj(response.json())
            return traits
        except RequestException as e:
            logging.error(f"Failed to get song traits from query {query}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def analyze_preference(self, user_id: str, chat_id: Optional[str]) -> str:
        try:
            response = self._make_request("POST",
                                          f"{self.chat_url}/analyze_preference",
                                          params={"user_id": user_id, "chat_id": chat_id}
                                          )
            # print(f"agent response: {response}")
            return response.text
        except RequestException as e:
            logging.error(f"Failed to analyze preference for current user")
            raise HTTPException(status_code=500, detail=str(e))

    def _make_request(self, method: str, url: str, **kwargs) -> Response:
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except RequestException as e:
            logging.error(f"HTTP {method} request to {url} failed: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
