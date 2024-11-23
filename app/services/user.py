import requests
import logging
from typing import List, Optional
import time

from pydantic import ValidationError, parse_obj_as
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError

from app.models.user import User
from app.models.playlist import Playlist

from requests import Response, RequestException

UPDATE_FREQUENCY = 300  # seconds -> 5 minutes


class UserService:

    def __init__(self, spotify_adapter_url: str, user_url: str, playlist_url: str):
        self.spotify_url = spotify_adapter_url  # URL of the Spotify integration service
        self.user_url = user_url
        self.playlist_url = playlist_url
        self.last_updated = {}


    def login(self, auth_code: str) -> Optional[User]:
        payload = {'auth_code': auth_code}

        try:
            # Exchange the auth code for user info from the Spotify integration service
            response = self._make_request('POST', f"{self.spotify_url}/login", json=payload)
            data = response.json()

            # Update the user in the User service
            updated_response = self._make_request('PUT', f"{self.user_url}/update_user", json=data)
            user = User.parse_obj(updated_response.json())
            return user

        except RequestException as e:
            logging.error(f"Login failed for auth_code {auth_code}: {e}")
            return None

    def get_user(self, user_id: str) -> Optional[User]:
        try:
            # Retrieve user info from the User service
            response = self._make_request('GET', f"{self.user_url}/users/{user_id}")
            user = User.parse_obj(response.json())
            return user

        except RequestException as e:
            logging.error(f"Failed to get user {user_id}: {e}")
            return None


    def get_user_playlists(self, user_id: str) -> Optional[List[Playlist]]:
        if self._should_update(user_id):
            playlists = self._update_playlists_from_spotify(user_id)
        else:
            playlists = self._get_playlists_from_service(user_id)
        return playlists

    def _should_update(self, user_id: str) -> bool:
        last_time = self.last_updated.get(user_id, 0)
        return (time.time() - last_time) >= self.UPDATE_FREQUENCY

    def _get_playlists_from_service(self, user_id: str) -> Optional[List[Playlist]]:
        try:
            response = self._make_request('GET', f"{self.playlist_url}/playlists/{user_id}")
            playlists = parse_obj_as(List[Playlist], response.json())
            return playlists
        except RequestException as e:
            logging.error(f"Failed to get cached playlists for {user_id}: {e}")
            return None

    def _update_playlists_from_spotify(self, user_id: str) -> Optional[List[Playlist]]:
        try:
            logging.info(f"Updating playlists from Spotify for user {user_id}")
            response = self._make_request('GET', f"{self.spotify_url}/users/{user_id}/playlists")
            spotify_playlists = response.json()

            # Update the playlist service with new data
            self._make_request('POST', f"{self.playlist_url}/update_playlists", json=spotify_playlists)

            playlists = parse_obj_as(List[Playlist], spotify_playlists)
            self.last_updated[user_id] = time.time()
            return playlists
        except RequestException as e:
            logging.error(f"Failed to update playlists from Spotify for {user_id}: {e}")
            return None

    def _make_request(self, method: str, url: str, **kwargs) -> Response:
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except RequestException as e:
            logging.error(f"HTTP {method} request to {url} failed: {e}")
            raise
