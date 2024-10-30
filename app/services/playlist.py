import requests
from pydantic import ValidationError
import logging

from app.models.playlist import Playlist


class PlaylistService:

    def __init__(self, spotify_adapter_url: str, user_url: str):
        self.spotify_url = spotify_adapter_url  # URL of the Spotify integration service
        self.user_url = user_url

    def get_playlist(self, playlist_id: str, include_tracks: bool):
        pass

    def update_playlist(self, playlist: Playlist):
        pass
