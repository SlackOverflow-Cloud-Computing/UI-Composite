import os
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
import dotenv

dotenv.load_dotenv()
UPDATE_FREQUENCY = 300  # seconds -> 5 minutes
JWT_SECRET = os.getenv("JWT_SECRET")


class UserService:

    def __init__(self, spotify_adapter_url: str, user_url: str, playlist_url: str):
        self.spotify_url = spotify_adapter_url  # URL of the Spotify integration service
        self.user_url = user_url
        self.playlist_url = playlist_url
        self.last_updated = {}

    def login(self, auth_code: str, cid: str) -> Optional[User]:
        payload = {'auth_code': auth_code}

        try:
            # Exchange the auth code for user info from the Spotify integration service
            response = self._make_request('POST', f"{self.spotify_url}/auth/login", token="", cid=cid, json=payload)
            data = response.json()

            # Update the user in the User service
            updated_response = self._make_request('POST', f"{self.user_url}/users", token="", cid=cid, json=data)
            user = User.parse_obj(updated_response.json().get('user'))
            return user

        except requests.RequestException as e:
            logging.error(f"Login failed for auth_code {auth_code}: {e} - [{cid}]")
            return None

        except ValidationError as e:
            logging.error(f"Failed to parse user data: {e} - [{cid}]")
            return None

    def validate_token(self, token: str, scope: tuple[str, str], id: Optional[str]=None) -> bool:
        """Check if a JWT token is valid

        Also checks if the token has the required scope for the endpoint. Optionally
        checks if the token is associated with a specific user ID.
        """
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            if scope[1] not in payload.get('scopes').get(scope[0]):
                return False
            if id and payload.get('sub') != id:
                return False
            return True

        except jwt.InvalidTokenError as e:
            return False

    def get_user_id(self, token: str, cid: str) -> Optional[str]:
        try:
            # Decode the JWT to get the user ID
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
            return payload.get('sub')

        except jwt.InvalidTokenError:
            logging.error(f"Invalid JWT: {token} - [{cid}]")

    def get_user(self, token: str, cid: str) -> Optional[User]:
        user_id = self.get_user_id(token, cid)
        print(f"User Id from token: {user_id}")
        if not user_id:
            return None

        try:
            # Retrieve user info from the User service
            response = self._make_request('GET', f"{self.user_url}/users/{user_id}", token, cid)
            user = User.parse_obj(response.json())
            return user

        except requests.RequestException as e:
            logging.error(f"Failed to get user {user_id}: {e} - [{cid}]")
            return None

        except Exception as e:
            logging.error(f"Failed to get user {user_id}: {e} - [{cid}]")
            return None


    def get_user_playlists(self, token: str, cid: str) -> Optional[List[Playlist]]:

        user_id = self.get_user_id(token, cid)
        if not user_id or not self.validate_token(token, ("/users/{user_id}/playlists", "GET"), user_id):
            return None

        if self._should_update(user_id):
            playlists = self._update_playlists_from_spotify(user_id, token, cid)
        else:
            playlists = self._get_playlists_from_service(user_id, token, cid)
        return playlists

    def create_playlist(self, token: str, user_id: str, name: str, song_ids: List[str], cid: str):

        # Create Playlist in Spotify Adapter
        try:
            spotify_token = self.get_spotify_token(user_id, token, cid)
            payload = {
                "token": spotify_token.model_dump(),
                "name": name,
                "song_ids": song_ids
            }
            response = self._make_request('POST', f"{self.spotify_url}/users/{user_id}/playlists", token, cid, json=payload)

        except Exception as e:
            logging.error(f"Failed to create playlist: {e} - [{cid}]")
            raise e

    def get_spotify_token(self, user_id: str, token: str, cid: str) -> Optional[SpotifyToken]:
        try:
            response = self._make_request('GET', f"{self.user_url}/users/{user_id}/spotify_token", token, cid)
            spotify_token = SpotifyToken.parse_obj(response.json())
            # TODO: shouldn't need to refresh every time
            params = spotify_token.model_dump()
            params["token"] = token
            response = self._make_request('GET', f"{self.spotify_url}/users/{user_id}/refreshed_token", token, cid, params=params)
            spotify_token = SpotifyToken.parse_obj(response.json())
            return spotify_token
        except requests.RequestException as e:
            logging.error(f"Failed to get Spotify token for {user_id}: {e} - [{cid}]")
            return None

    def _should_update(self, user_id: str, cid: str) -> bool:
        last_time = self.last_updated.get(user_id, 0)
        return (time.time() - last_time) >= UPDATE_FREQUENCY

    def _get_playlists_from_service(self, user_id: str, token: str, cid: str) -> Optional[List[Playlist]]:
        try:
            response = self._make_request('GET', f"{self.playlist_url}/users/{user_id}/playlists", token, cid)
            playlists = parse_obj_as(List[Playlist], response.json())
            return playlists
        except requests.RequestException as e:
            logging.error(f"Failed to get cached playlists for {user_id}: {e} - [{cid}]")
            return None

    def _update_playlists_from_spotify(self, user_id: str, token: str, cid: str) -> Optional[List[Playlist]]:
        try:
            logging.info(f"Updating playlists from Spotify for user {user_id} - [{cid}]")

            # Get the user's spotify token from user service
            spotify_token = self.get_spotify_token(user_id, token, cid)

            # Get the user's playlists from the playlist service
            payload = {"spotify_token": spotify_token}
            response = self._make_request('GET', f"{self.spotify_url}/users/{user_id}/playlists", token, cid, json=payload)
            spotify_playlists = response.json()

            # Update the playlist service with new data
            for playlist in spotify_playlists:
                playlist_id = playlist.get('id')
                self._make_request('POST', f"{self.playlist_url}/playlists/{playlist_id}", token, cid, json=spotify_playlists)

            playlists = parse_obj_as(List[Playlist], spotify_playlists)
            self.last_updated[user_id] = time.time()
            return playlists
        except requests.RequestException as e:
            logging.error(f"Failed to update playlists from Spotify for {user_id}: {e} - [{cid}]")
            return None

    def _make_request(self, method: str, url: str, token:str, cid: str, **kwargs) -> requests.Response:
        try:
            # Add the JWT to the request headers
            if token:
                headers = kwargs.get('headers', {})
                headers['Authorization'] = f"Bearer {token}"
                headers['X-Correlation-ID'] = cid
                kwargs['headers'] = headers

            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logging.error(f"HTTP {method} request to {url} failed: {e} - [{cid}]")
            raise
