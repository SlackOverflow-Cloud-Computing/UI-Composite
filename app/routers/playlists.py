import logging
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional

from app.models.playlist import Playlist
from app.services.service_factory import ServiceFactory

logger = logging.getLogger("uvicorn")
router = APIRouter()


@router.get("playlists/{playlist_id}", tags=["playlists"], status_code=status.HTTP_200_OK)
async def get_playlist(playlist_id: str, include_tracks: Optional[bool] = Query(False)):
    """ Get playlist details from Spotify and merge with our own data

    TODO: Should we check in with the spotify service to get the latest playlist details
    for every request?
    """

    logger.info(f"Incoming Request - Method: POST, Path: /playlists/{playlist_id}")
    playlist_service = ServiceFactory.get_service("Playlist")
    if not include_tracks:
        include_tracks = False

    try:
        # Get details from Spotify integration service
        playlist = playlist_service.get_playlist(playlist_id, include_tracks) # Does nothing yet
        logger.debug(f"Playlist info received: {playlist}")
        if not playlist:
            logger.error(f"Failed to get playlist info for {playlist_id}")
            raise HTTPException(status_code=400, detail="Spotify Login Failed")

        logger.info(f"Response - Method: POST, Path: /login, Status: 200, Body: {playlist.dict()}")
        return playlist

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/update_playlist", tags=["playlists"], status_code=status.HTTP_202_ACCEPTED)
async def update_playlist(request: Playlist):
    """ Update a playlist with new data

    Asynchronously update the playlist with the new data. This will be done in the background
    and the response will be returned immediately.
    TODO: is PUT really best for integrating with the UI?
    """

    logger.info(f"Incoming Request - Method: PUT, Path: /update_playlist")
    playlist_service = ServiceFactory.get_service("Playlist")

    # TODO: Check for authorization to update the playlist

    try:
        playlist_service.update_playlist(request)
        logger.info(f"Response - Method: PUT, Path: /update_playlist, Status: 202, Body: {request.dict()}")
        return {"message": "Playlist updated successfully", "playlist": request.dict()}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
