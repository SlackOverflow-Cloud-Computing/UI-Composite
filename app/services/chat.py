import requests
import logging
from typing import List, Optional

import jwt
from requests import Response, RequestException
from fastapi import HTTPException

from app.models.chat import Message, ChatData, ChatResponse
from app.models.song import Traits



class ChatService:

    def __init__(self, chat_url: str, user_url: str):
        self.chat_url = chat_url
        self.user_url = user_url

    def validate_token(self, token: str, scope: tuple[str, str], id: Optional[str]=None) -> bool:
        """Check if a JWT token is valid

        Also checks if the token has the required scope for the endpoint. Optionally
        checks if the token is associated with a specific user ID.
        """
        try:
            payload = jwt.decode(token, algorithms=['HS256'])
            if scope and scope[1] not in payload.get('scopes').get(scope[0]):
                return False
            if id and payload.get('sub') != id:
                return False
            return True

        except jwt.InvalidTokenError:
            return False

    def update_chat_database(self, chat_data: ChatData) -> str:
        try:
            response = self._make_request("POST", f"{self.chat_url}/update_chat", json=chat_data.model_dump())
            return response.text
        except RequestException as e:
            logging.error(f"Failed to get update the message to database: {e}")
            raise HTTPException(status_code=500, detail=str(e))


    def general_chat(self, query: str, user_id: str, chat_id: Optional[str]) -> ChatResponse:
        try:
            response = self._make_request("POST",
                                          f"{self.chat_url}/general_chat",
                                          params={"user_id": user_id, "chat_id": chat_id, "query": query}
                                          )
            response = ChatResponse.parse_obj(response.json())
            return response
        except RequestException as e:
            logging.error(f"Failed to generate chat response")
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
