import os
from typing import Optional, List
import requests
from http.client import responses
import logging

import jwt
from pydantic import ValidationError
from requests import Response, RequestException
from fastapi import HTTPException, Query
import dotenv

from app.models.song import Song

dotenv.load_dotenv()
JWT_SECRET = os.getenv('JWT_SECRET')
ALGORITHM = "HS256"

class SongService:
    def __init__(self, song_url: str):
        self.song_url = song_url

    def validate_token(self, token: str, scope: tuple[str, str]) -> bool:
        """Validate a JWT token.

        Also checks if the token has the required scope for the endpoint.
        Scope is of the form ("/endpoint", "METHOD").
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
            if scope and scope[1] not in payload.get("scopes").get(scope[0]):
                return False
            return True

        except jwt.exceptions.InvalidTokenError:
            return False

    def add_songs(self, token: str, song: List[Song], cid: str):
        try:
            response = self._make_request(token, "POST", f"{self.song_url}/songs", cid, json=[s.model_dump() for s in song])
            return response.json()
        except RequestException as e:
            logging.error(f"Failed to put song {song}: {e} - [{cid}]")
            # raise nested exception instead of generic 500
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))

    def _make_request(self, token: str, method: str, url: str, cid: str, **kwargs) -> Response:
        try:
            # Add the JWT to the request headers
            headers = kwargs.get('headers', {})
            headers['Authorization'] = f"Bearer {token}"
            headers['X-Correlation-ID'] = cid
            kwargs['headers'] = headers

            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response

        except RequestException as e:
            logging.error(f"HTTP {method} request to {url} failed: {e} - [{cid}]")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
