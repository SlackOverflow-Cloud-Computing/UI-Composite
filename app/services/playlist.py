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

from app.models.playlist import Playlist, PlaylistInfo, PlaylistContent

dotenv.load_dotenv()
JWT_SECRET = os.getenv('JWT_SECRET')
ALGORITHM = "HS256"

class PlaylistService:

    def __init__(self, spotify_adapter_url: str, user_url: str, playlist_url: str):
        self.spotify_url = spotify_adapter_url  # URL of the Spotify integration service
        self.user_url = user_url
        self.playlist_url = playlist_url

    def validate_token(self, token: str, scope: tuple[str, str], cid: str) -> bool:
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

    def get_playlist_spotify(self, playlist_id: str, cid: str, include_tracks: Optional[bool] = Query(False)):
        pass

    def get_playlist(self, playlist_id: str, token: str, cid: str) -> PlaylistInfo:
        try:
            response = self._make_request(token, "GET", f"{self.playlist_url}/playlists/{playlist_id}", cid)
            playlist = PlaylistInfo.parse_obj(response.json())
            return playlist
        except RequestException as e:
            logging.error(f"Failed to get playlist of {playlist_id}: {e} - [{cid}]")
            # raise nested exception instead of generic 500
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))

    def get_playlists(self, user_id: str, token: str, cid: str) -> List[PlaylistInfo]:
        try:
            response = self._make_request(token, "GET", f"{self.playlist_url}/users/{user_id}/playlists", cid)
            playlists = [PlaylistInfo.parse_obj(playlist) for playlist in response.json()]
            return playlists
        except RequestException as e:
            logging.error(f"Failed to get playlists for user {user_id}: {e} - [{cid}]")
            # raise nested exception instead of generic 500
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))

    def update_playlist(self, playlist_id: str, playlist_info: PlaylistInfo, playlist_content: PlaylistContent, token: str, cid: str):
        try:
            response = self._make_request(
                token,
                "POST",
                f"{self.playlist_url}/playlists/{playlist_id}",
                cid,
                json={
                    "playlist_info": playlist_info.model_dump(mode="json"),
                    "playlist_content": playlist_content.model_dump(mode="json"),
                }
            )
            return response.json()

        except RequestException as e:
            logging.error(f"Failed to update playlist for playlist {playlist_id}: {e} - [{cid}]")
            # raise nested exception instead of generic 500
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))

    def delete_playlist(self, playlist_id: str, token: str, cid: str):
        try:
            response = self._make_request(token,
                                          "DELETE",
                                          f"{self.playlist_url}/playlists/{playlist_id}", cid)
            return response.json()
        except RequestException as e:
            logging.error(f"Failed to delete playlist {playlist_id}: {e} - [{cid}]")
            # raise nested exception instead of generic 500
            if isinstance(e, HTTPException):
                raise e
            raise HTTPException(status_code=500, detail=str(e))

    def delete_song(self, playlist_id: str, track_id: str, token: str, cid: str):
        try:
            responses = self._make_request(token,
                                           "DELETE",
                                           f"{self.playlist_url}/playlists/{playlist_id}/tracks/{track_id}", cid)
            return responses.json()
        except RequestException as e:
            logging.error(f"Failed to delete song {track_id} for playlist {playlist_id}: {e} - [{cid}]")
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
