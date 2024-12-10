import requests
import logging
from typing import List, Optional

from app.models.song import Song, Traits

from requests import Response, RequestException
from fastapi import HTTPException



class RecommendationService:

    def __init__(self, spotify_adapter_url: str):
        self.spotify_adapter_url = spotify_adapter_url

    def get_recommendations(self, token: str, params: Traits) -> List[Song]:
        try:
            response = self._make_request(token, "GET", f"{self.spotify_adapter_url}/recommendations", params=params.model_dump())
            songs = [Song.parse_obj(song) for song in response.json()]
            return songs
        except RequestException as e:
            logging.error(f"Failed to get song recommendations from traits {params}: {e}")
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
