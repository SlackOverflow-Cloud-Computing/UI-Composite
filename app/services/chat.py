import requests
import logging
from typing import List, Optional
import os, dotenv

import jwt
from requests import Response, RequestException
from fastapi import HTTPException

from app.models.chat import Message, ChatData, ChatResponse
from app.models.song import Traits

dotenv.load_dotenv()
JWT_SECRET = os.getenv("JWT_SECRET")

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
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            if scope and scope[1] not in payload.get('scopes').get(scope[0]):
                return False
            if id and payload.get('sub') != id:
                return False
            return True

        except jwt.InvalidTokenError:
            return False

    def update_chat_database(self, chat_data: ChatData, cid: str) -> str:
        try:
            logging.info(f"Updating chat database with data: {chat_data.model_dump()} - [{cid}]")
            logging.info(f"Chat URL: {self.chat_url} - [{cid}]")
            response = self._make_request("POST", f"{self.chat_url}/update_chat", cid, json=chat_data.model_dump())
            return response.text
        except RequestException as e:
            logging.error(f"Failed to get update the message to database: {e} - [{cid}]")
            # raise nested exception instead of generic 500
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))


    def general_chat(self, query: str, user_id: str, chat_id: str, cid: str) -> ChatResponse:
        try:
            response = self._make_request("POST",
                                          f"{self.chat_url}/general_chat",
                                          cid,
                                          params={"user_id": user_id, "chat_id": chat_id, "query": query}
                                          )
            response = ChatResponse.parse_obj(response.json())
            return response
        except RequestException as e:
            logging.error(f"Failed to generate chat response - [{cid}]")
            # raise nested exception instead of generic 500
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))


    def extract_song_traits(self, query: Message, cid: str) -> Traits:
        try:
            response = self._make_request("POST", f"{self.chat_url}/extract_traits", cid, json=query.model_dump())
            traits = Traits.parse_obj(response.json())
            return traits
        except RequestException as e:
            logging.error(f"Failed to get song traits from query {query}: {e} - [{cid}]")
            # raise nested exception instead of generic 500
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))

    def analyze_preference(self, user_id: str, chat_id: str, cid: str) -> str:
        try:
            response = self._make_request("POST",
                                          f"{self.chat_url}/analyze_preference", cid,
                                          params={"user_id": user_id, "chat_id": chat_id}
                                          )
            # print(f"agent response: {response}")
            return response.text
        except RequestException as e:
            logging.error(f"Failed to analyze preference for current user - [{cid}]")
            # raise nested exception instead of generic 500
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))

    def _make_request(self, method: str, url: str, cid: str, **kwargs) -> Response:
        try:
            headers = kwargs.get('headers', {})
            headers['X-Correlation-ID'] = cid
            kwargs['headers'] = headers
            
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except RequestException as e:
            logging.error(f"HTTP {method} request to {url} failed: {e} - [{cid}]")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
