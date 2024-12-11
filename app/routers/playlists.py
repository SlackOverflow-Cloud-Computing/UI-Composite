import logging
from fastapi import APIRouter, HTTPException, Query, Request, status, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, List
import uuid

from app.models.playlist import PlaylistContent, PlaylistInfo
from app.services.service_factory import ServiceFactory

logger = logging.getLogger("uvicorn")
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/token")
async def login_for_access_token(
) -> dict:
    """This is just for testing"""

    return {"access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGV4cmFjYXBlIiwiaWF0IjoxNzMzNjg5NjI2LCJzY29wZXMiOnsiL2F1dGgvbG9naW4iOlsiUE9TVCJdLCIvdXNlcnMve3VzZXJfaWR9L3BsYXlsaXN0cyI6WyJHRVQiXSwiL3VzZXJzL3t1c2VyX2lkfSI6WyJHRVQiLCJQVVQiXSwiL3VzZXJzL3t1c2VyX2lkfS9zcG90aWZ5X3Rva2VuIjpbIkdFVCJdLCIvcGxheWxpc3RzL3twbGF5bGlzdF9pZH0iOlsiR0VUIiwiUE9TVCIsIkRFTEVURSJdLCIvcGxheWxpc3RzL3twbGF5bGlzdF9pZH0vdHJhY2tzL3t0cmFja19pZH0iOlsiREVMRVRFIl0sIi9yZWNvbW1lbmRhdGlvbnMiOlsiR0VUIl0sIi9yZWNvbW1lbmRhdGlvbnMvcGxheWxpc3QiOlsiR0VUIl19fQ.SuQq7SVDOazCaJcZE_cUrzLTvDc4nr6xtj8xA1sEplI", "token_type": "bearer"}


@router.get("/users/{user_id}/playlists", tags=["playlists"], status_code=status.HTTP_200_OK)
async def get_playlists(user_id: str, include_tracks: Optional[bool] = Query(False), token: str = Depends(oauth2_scheme)) -> List[PlaylistInfo]:
    """ Get user's playlists from our database; if no data, get from Spotify API"""
    
    cid = str(uuid.uuid4())
    logger.info(f"Incoming Request - Method: GET, Path: /playlists/{user_id} - [{cid}]")
    playlist_service = ServiceFactory.get_service("Playlist")
    if not playlist_service.validate_token(token, scope=("/users/{user_id}/playlists", "GET")):
        raise HTTPException(status_code=401, detail="Invalid Token")

    if not include_tracks:
        include_tracks = False

    try:
        # Get details from playlist database, if no data, get from spotify
        playlists = playlist_service.get_playlists(user_id, token, cid)
        logger.debug(f"Playlist info received - [{cid}]")
        if not playlists:
            # TODO: get from spotify
            # playlists = playlist_service.get_playlist_spotify()
            if not playlists:
                logger.error(f"Failed to get playlist info for user {user_id} - [{cid}]")
                raise HTTPException(status_code=400, detail="Spotify Login Failed")

        return playlists

    except Exception as e:
        # raise nested exception instead of generic 500
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/playlists/{playlist_id}", tags=["playlists"], status_code=status.HTTP_200_OK)
async def get_playlist(playlist_id: str, token: str = Depends(oauth2_scheme)) -> PlaylistInfo:
    """ Get a playlist by playlist_id, return the playlist info"""
    
    cid = str(uuid.uuid4())
    logger.info(f"Incoming Request - Method: GET, Path: /playlist/{playlist_id} - [{cid}]")
    playlist_service = ServiceFactory.get_service("Playlist")
    if not playlist_service.validate_token(token, scope=("/playlist/{playlist_id}", "GET")):
        raise HTTPException(status_code=401, detail="Invalid Token")

    try:
        # Get details from playlist database, if no data, get from spotify
        playlist = playlist_service.get_playlist(playlist_id, token, cid)
        logger.debug(f"Playlist info received - [{cid}]")
        if not playlist:
            logger.error(f"Failed to get playlist info of {playlist_id} - [{cid}]")
            raise HTTPException(status_code=400, detail=f"Could not get this playlist {playlist_id}")
        return playlist

    except Exception as e:
        # raise nested exception instead of generic 500
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/playlists/{playlist_id}", tags=["playlists"], status_code=status.HTTP_202_ACCEPTED)
async def update_playlist(playlist_id: str, request: Request):
    cid = str(uuid.uuid4())
    data = await request.json()
    playlist_info = data.get("playlist_info")
    playlist_content = data.get("playlist_content")
    token = data.get("token")
    logger.info(f"Incoming Request - Method: POST, Path: /playlist/{playlist_id} - [{cid}]")
    playlist_service = ServiceFactory.get_service("Playlist")
    if not playlist_service.validate_token(token, scope=("/playlist/{playlist_id}", "POST")):
        raise HTTPException(status_code=401, detail="Invalid Token")

    try:
        message = playlist_service.update_playlist(playlist_id, playlist_info, playlist_content, token, cid)
        logger.debug(f"Playlist info and content received - [{cid}]")
        if not message:
            logger.error(f"Failed to update playlist info for {playlist_id} - [{cid}]")
            raise HTTPException(status_code=400, detail=f"Could not update playlist info for {playlist_id}")
        return message

    except Exception as e:
        # raise nested exception instead of generic 500
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/playlists/{playlist_id}", tags=["playlists"], status_code=status.HTTP_200_OK)
async def delete_playlist(playlist_id: str, token: str = Depends(oauth2_scheme)):
    cid = str(uuid.uuid4())
    logger.info(f"Incoming Request - Method: DELETE, Path: /playlist/{playlist_id} - [{cid}]")
    playlist_service = ServiceFactory.get_service("Playlist")
    if not playlist_service.validate_token(token, scope=("/playlist/{playlist_id}", "DELETE")):
        raise HTTPException(status_code=401, detail="Invalid Token")

    try:
        message = playlist_service.delete_playlist(playlist_id, token, cid)
        logger.debug(f"Playlist id received - [{cid}]")
        if not message:
            logger.error(f"Failed to delete playlist info for {playlist_id} - [{cid}]")
            raise HTTPException(status_code=400, detail=f"Could not delete playlist info for {playlist_id}")
        return message

    except Exception as e:
        # raise nested exception instead of generic 500
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/playlists/{playlist_id}/tracks/{track_id}", tags=["playlists"], status_code=status.HTTP_200_OK)
async def delete_song(playlist_id: str, track_id: str, token: str = Depends(oauth2_scheme)):
    cid = str(uuid.uuid4())
    logger.info(f"Incoming Request - Method: DELETE, Path: /playlist/{playlist_id} - [{cid}]")
    playlist_service = ServiceFactory.get_service("Playlist")
    if not playlist_service.validate_token(token, scope=("/playlist/{playlist_id}/tracks/{track_id}", "DELETE")):
        raise HTTPException(status_code=401, detail="Invalid Token")

    try:
        message = playlist_service.delete_song(playlist_id, track_id, token, cid)
        logger.debug(f"Playlist id and Track id received - [{cid}]")
        if not message:
            logger.error(f"Failed to delete song info for {playlist_id} - [{cid}]")
            raise HTTPException(status_code=400, detail=f"Could not delete song info for {playlist_id}")
        return message
    except Exception as e:
        # raise nested exception instead of generic 500
        if isinstance(e, HTTPException):
            raise e
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
