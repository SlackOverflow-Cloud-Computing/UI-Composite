import logging
from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional, List

from app.models.playlist import Playlist, PlaylistContent, PlaylistInfo
from app.services.service_factory import ServiceFactory

logger = logging.getLogger("uvicorn")
router = APIRouter()


@router.get("/playlists/{user_id}", tags=["playlists"], status_code=status.HTTP_200_OK)
async def get_playlists(user_id: str, include_tracks: Optional[bool] = Query(False)) -> List[PlaylistInfo]:
    """ Get user's playlists from our database; if no data, get from Spotify API"""

    logger.info(f"Incoming Request - Method: GET, Path: /playlists/{user_id}")
    playlist_service = ServiceFactory.get_service("Playlist")
    if not include_tracks:
        include_tracks = False

    try:
        # Get details from playlist database, if no data, get from spotify
        playlists = playlist_service.get_playlists(user_id)
        logger.debug(f"Playlist info received")
        if not playlists:
            # TODO: get from spotify
            # playlists = playlist_service.get_playlist_spotify()
            if not playlists:
                logger.error(f"Failed to get playlist info for user {user_id}")
                raise HTTPException(status_code=400, detail="Spotify Login Failed")

        return playlists

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/playlist/{playlist_id}", tags=["playlists"], status_code=status.HTTP_200_OK)
async def get_playlist(playlist_id: str) -> PlaylistInfo:
    """ Get a playlist by playlist_id, return the playlist info"""

    logger.info(f"Incoming Request - Method: GET, Path: /playlist/{playlist_id}")
    playlist_service = ServiceFactory.get_service("Playlist")

    try:
        # Get details from playlist database, if no data, get from spotify
        playlist = playlist_service.get_playlist(playlist_id)
        logger.debug(f"Playlist info received")
        if not playlist:
            logger.error(f"Failed to get playlist info of  {playlist_id}")
            raise HTTPException(status_code=400, detail=f"Could not get this playlist {playlist_id}")
        return playlist

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/update_playlist", tags=["playlists"], status_code=status.HTTP_202_ACCEPTED)
async def update_playlist(playlist_id: str, playlist_info: PlaylistInfo, playlist_content: PlaylistContent):
    logger.info(f"Incoming Request - Method: POST, Path: /playlist/{playlist_id}")
    playlist_service = ServiceFactory.get_service("Playlist")
    try:
        message = playlist_service.update_playlist(playlist_id, playlist_info, playlist_content)
        logger.debug(f"Playlist info and content received")
        if not message:
            logger.error(f"Failed to update playlist info for {playlist_id}")
            raise HTTPException(status_code=400, detail=f"Could not update playlist info for {playlist_id}")
        return message

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/delete_playlist", tags=["playlists"], status_code=status.HTTP_200_OK)
async def delete_playlist(playlist_id: str):
    logger.info(f"Incoming Request - Method: DELETE, Path: /playlist/{playlist_id}")
    playlist_service = ServiceFactory.get_service("Playlist")

    try:
        message = playlist_service.delete_playlist(playlist_id)
        logger.debug(f"Playlist id received")
        if not message:
            logger.error(f"Failed to delete playlist info for {playlist_id}")
            raise HTTPException(status_code=400, detail=f"Could not delete playlist info for {playlist_id}")
        return message

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete_song", tags=["playlists"], status_code=status.HTTP_200_OK)
async def delete_song(playlist_id: str, track_id: str):
    logger.info(f"Incoming Request - Method: DELETE, Path: /playlist/{playlist_id}")
    playlist_service = ServiceFactory.get_service("Playlist")
    try:
        message = playlist_service.delete_song(playlist_id, track_id)
        logger.debug(f"Playlist id and Track id received")
        if not message:
            logger.error(f"Failed to delete song info for {playlist_id}")
            raise HTTPException(status_code=400, detail=f"Could not delete song info for {playlist_id}")
        return message
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# @router.put("/update_playlist", tags=["playlists"], status_code=status.HTTP_202_ACCEPTED)
# async def update_playlist(request: Playlist):
#     """ Update a playlist with new data
#
#     Asynchronously update the playlist with the new data. This will be done in the background
#     and the response will be returned immediately.
#     TODO: is PUT really best for integrating with the UI?
#     """
#
#     logger.info(f"Incoming Request - Method: PUT, Path: /update_playlist")
#     playlist_service = ServiceFactory.get_service("Playlist")
#
#     # TODO: Check for authorization to update the playlist
#
#     try:
#         playlist_service.update_playlist(request)
#         logger.info(f"Response - Method: PUT, Path: /update_playlist, Status: 202, Body: {request.dict()}")
#         return {"message": "Playlist updated successfully", "playlist": request.dict()}
#
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
