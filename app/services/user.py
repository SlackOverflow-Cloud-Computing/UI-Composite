import requests
import logging
from typing import List, Optional
import time

from pydantic import ValidationError, parse_obj_as
import jwt

from app.models.user import User
from app.models.playlist import Playlist
from app.models.spotify_token import SpotifyToken

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
            response = self._make_request('POST', f"{self.spotify_url}/login", token="", json=payload)
            data = response.json()

            # Update the user in the User service
            updated_response = self._make_request('PUT', f"{self.user_url}/update_user", token="", json=data)
            user = User.parse_obj(updated_response.json())
            return user

        except requests.RequestException as e:
            logging.error(f"Login failed for auth_code {auth_code}: {e}")
            return None

    def get_user_id(self, token: str) -> Optional[str]:
        try:
            # Decode the JWT to get the user ID
            payload = jwt.decode(token, algorithms=['HS256'])
            return payload.get('user_id')

        except jwt.ExpiredSignatureError:
            logging.error(f"JWT expired: {jwt}")
            return None

        except jwt.InvalidTokenError:
            logging.error(f"Invalid JWT: {jwt}")

    def get_user(self, token: str) -> Optional[User]:
        user_id = self.get_user_id(token)
        if not user_id:
            return None

        try:
            # Retrieve user info from the User service
            response = self._make_request('GET', f"{self.user_url}/users/{user_id}", token)
            user = User.parse_obj(response.json())
            return user

        except requests.RequestException as e:
            logging.error(f"Failed to get user {user_id}: {e}")
            return None


    def get_user_playlists(self, token: str) -> Optional[List[Playlist]]:
        user_id = self.get_user_id(token)
        if not user_id:
            return None

        if self._should_update(user_id):
            playlists = self._update_playlists_from_spotify(user_id, token)
        else:
            playlists = self._get_playlists_from_service(user_id, token)
        return playlists

    def _should_update(self, user_id: str) -> bool:
        last_time = self.last_updated.get(user_id, 0)
        return (time.time() - last_time) >= UPDATE_FREQUENCY

    def _get_playlists_from_service(self, user_id: str, token: str) -> Optional[List[Playlist]]:
        try:
            response = self._make_request('GET', f"{self.playlist_url}/playlists/{user_id}", token)
            playlists = parse_obj_as(List[Playlist], response.json())
            return playlists
        except requests.RequestException as e:
            logging.error(f"Failed to get cached playlists for {user_id}: {e}")
            return None

    def _update_playlists_from_spotify(self, user_id: str, token: str) -> Optional[List[Playlist]]:
        try:
            logging.info(f"Updating playlists from Spotify for user {user_id}")

            # Get the user's spotify token from user service
            response = self._make_request('GET', f"{self.user_url}/users/spotify_token", token)
            spotify_token = SpotifyToken.parse_obj(response.json())

            # Get the user's playlists from the playlist service
            payload = {"spotify_token": spotify_token}
            response = self._make_request('GET', f"{self.spotify_url}/users/{user_id}/playlists", token, json=payload)
            spotify_playlists = response.json()

            # Update the playlist service with new data
            self._make_request('POST', f"{self.playlist_url}/update_playlists", token, json=spotify_playlists)

            playlists = parse_obj_as(List[Playlist], spotify_playlists)
            self.last_updated[user_id] = time.time()
            return playlists
        except requests.RequestException as e:
            logging.error(f"Failed to update playlists from Spotify for {user_id}: {e}")
            return None

    def _make_request(self, method: str, url: str, token:str, **kwargs) -> requests.Response:
        try:
            # Add the JWT to the request headers
            if token:
                headers = kwargs.get('headers', {})
                headers['Authorization'] = f"Bearer {token}"
                kwargs['headers'] = headers

            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logging.error(f"HTTP {method} request to {url} failed: {e}")
            raise
