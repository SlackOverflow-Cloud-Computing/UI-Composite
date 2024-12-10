import requests
import logging
from typing import List, Optional

from app.models.song import Song, Traits
from app.models.spotify_token import SpotifyToken

from requests import Response, RequestException
from fastapi import HTTPException



class RecommendationService:

    def __init__(self, spotify_adapter_url: str):
        self.spotify_adapter_url = spotify_adapter_url

    def get_recommendations(self, token: str, spotify_token: SpotifyToken, traits: Traits) -> List[Song]:
        params = traits.model_dump()
        params["token"] = token
        params["spotify_access_token"] = spotify_token.access_token
        try:
            response = self._make_request(token, "GET", f"{self.spotify_adapter_url}/recommendations", params=params)
            songs = [Song.parse_obj(song) for song in response.json()]
            return songs
        except RequestException as e:
            logging.error(f"Failed to get song recommendations from traits {params}: {e}")
            # raise nested exception instead of generic 500
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))

    def _make_request(self, token: str, method: str, url: str, **kwargs) -> Response:
        try:
            # Add the JWT to the request headers
            headers = kwargs.get('headers', {})
            headers['Authorization'] = f"Bearer {token}"
            kwargs['headers'] = headers

            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except RequestException as e:
            logging.error(f"HTTP {method} request to {url} failed: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
