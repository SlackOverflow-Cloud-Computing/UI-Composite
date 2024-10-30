from __future__ import annotations

from typing import Optional

from pydantic import BaseModel
from datetime import datetime


class Playlist(BaseModel):

    # Spotify based information
    id: str                                 # Spotify ID

    # TODO: Add more fields here
