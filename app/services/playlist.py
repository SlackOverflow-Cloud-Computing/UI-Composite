from http.client import responses

import requests
from typing import Optional, List
from pydantic import ValidationError
import logging
from requests import Response, RequestException
from fastapi import HTTPException, Query

from app.models.playlist import Playlist, PlaylistInfo, PlaylistContent


class PlaylistService:

    def __init__(self, spotify_adapter_url: str, user_url: str, playlist_url: str):
        self.spotify_url = spotify_adapter_url  # URL of the Spotify integration service
        self.user_url = user_url
        self.playlist_url = playlist_url

    def get_playlist_spotify(self, playlist_id: str, include_tracks: Optional[bool] = Query(False)):
        pass

    def get_playlist(self, playlist_id: str) -> PlaylistInfo:
        try:
            response = self._make_request("GET", f"{self.playlist_url}/playlist/{playlist_id}")
            playlist = PlaylistInfo.parse_obj(response.json())
            return playlist
        except RequestException as e:
            logging.error(f"Failed to get playlist of {playlist_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def get_playlists(self, user_id: str) -> List[PlaylistInfo]:
        try:
            response = self._make_request("GET", f"{self.playlist_url}/playlists/{user_id}")
            playlists = [PlaylistInfo.parse_obj(playlist) for playlist in response.json()]
            return playlists
        except RequestException as e:
            logging.error(f"Failed to get playlists for user {user_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def update_playlist(self, playlist_id: str, playlist_info: PlaylistInfo, playlist_content: PlaylistContent):
        try:
            response = self._make_request(
                "POST",
                f"{self.playlist_url}/update/{playlist_id}",
                json={
                    "playlist_info": playlist_info.model_dump(mode="json"),
                    "playlist_content": playlist_content.model_dump(mode="json"),
                }
            )
            return response.json()
        except RequestException as e:
            logging.error(f"Failed to update playlist for playlist {playlist_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def delete_playlist(self, playlist_id: str):
        try:
            response = self._make_request("DELETE",
                                          f"{self.playlist_url}/playlists/{playlist_id}")
            return response.json()
        except RequestException as e:
            logging.error(f"Failed to delete playlist {playlist_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def delete_song(self, playlist_id: str, track_id: str):
        try:
            responses = self._make_request("DELETE",
                                           f"{self.playlist_url}/playlists/{playlist_id}/{track_id}")
            return responses.json()
        except RequestException as e:
            logging.error(f"Failed to delete song {track_id} for playlist {playlist_id}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    def _make_request(self, method: str, url: str, **kwargs) -> Response:
        try:
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except RequestException as e:
            logging.error(f"HTTP {method} request to {url} failed: {e}")
            raise HTTPException(status_code=e.response.status_code, detail=e.response.text)

    # def create_branch(self, branch_id: str):
    #     pass
    #
    # def set_branch(self, branch_id: str):
    #     pass
