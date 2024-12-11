import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.models.user import User
from app.models.spotify_token import SpotifyToken
from app.services.service_factory import ServiceFactory

logger = logging.getLogger("uvicorn")
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class LoginRequest(BaseModel):
    auth_code: str

class CreatePlaylistRequest(BaseModel):
    name: str
    song_ids: List[str]

@router.post("/auth/login", tags=["users"], status_code=status.HTTP_201_CREATED)
async def login(request: LoginRequest):
    """Uses Spotify Auth Code to Login User

    Gets login service and sends authorization code to Spotify service
    The service returns a user's JWT, and this should save it to the database.
    The UI can then use the JWT for future requests.
    """

    logger.info(f"Incoming Request - Method: POST, Path: /login, Body: {request.dict()}")
    auth_code = request.auth_code
    user_service = ServiceFactory.get_service("User")

    try:

        user = user_service.login(auth_code)
        logger.debug(f"User info received: {user}")
        if not user:
            logger.error(f"Login failed for auth_code: {auth_code}")
            raise HTTPException(status_code=400, detail="Spotify Login Failed")

        logger.info(f"Response - Method: POST, Path: /login, Status: 200, Body: {user.dict()}")
        return user.jwt

    except Exception as e:
        # raise nested exception instead of generic 500
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}", tags=["users"])
async def get_user(user_id: str, token: str = Depends(oauth2_scheme)):
    """Gets a User's Public Information"""

    logger.info(f"Incoming Request - Method: GET, Path: /users/me")
    user_service = ServiceFactory.get_service("User")
    if not user_service.validate_token(token=token, id=user_id, scope=("/users/{user_id}", "GET")):
        raise HTTPException(status_code=401, detail="Invalid Token")

    try:
        # Get the user's information in the database
        logger.info(f"Getting user info for user_id: {user_id}")
        user = user_service.get_user(token)
        logger.info(f"User info: {user}")
        if not user:
            logger.error(f"Failed to get user info")
            raise HTTPException(status_code=400, detail="User does not use Subwoofer")

        logger.info(f"Response - Method: GET, Path: /users/me, Status: 200, Body: {user.dict()}")
        return user

    except Exception as e:
        logger.error(f"Failed to get user info: {str(e)}")
        # raise nested exception instead of generic 500
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/playlists", tags=["users"])
async def get_user_playlists(user_id: str, token: str = Depends(oauth2_scheme)):
    """Gets a User's Playlists

    Checks information from Spotify and updates our database behind
    the scenes with the latest information.
    Requires a valid JWT.
    """

    logger.info(f"Incoming Request - Method: GET, Path: /users/{user_id}/playlists")
    user_service = ServiceFactory.get_service("User")

    try:
        # Get details from Spotify integration service
        playlists = user_service.get_user_playlists(token)
        logger.debug(f"User playlists: {playlists}")
        if not playlists:
            logger.error(f"Failed to get playlists for user {user_id}")
            raise HTTPException(status_code=400, detail="User does not have any playlists")

        logger.info(f"Response - Method: GET, Path: /users/{user_id}/playlists, Status: 200, Body: {playlists}")
        return playlists

    except Exception as e:
        # raise nested exception instead of generic 500
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/users/{user_id}/playlists", tags=["users"])
async def create_playlist(user_id: str, request: CreatePlaylistRequest, token: str = Depends(oauth2_scheme)):
    """Create a Playlist for a User

    Creates a playlist in the user's Spotify account.
    Requires a valid JWT.
    """

    logger.info(f"Incoming Request - Method: POST, Path: /users/{user_id}/playlists")
    user_service = ServiceFactory.get_service("User")
    if not user_service.validate_token(token=token, id=user_id, scope=("/users/{user_id}/playlists", "POST")):
        raise HTTPException(status_code=401, detail="Invalid Token")

    try:
        # Create a playlist in Spotify
        user_service.create_playlist(token, user_id, request.name, request.song_ids)
        logger.info(f"Response - Method: POST, Path: /users/{user_id}/playlists, Status: 200, Body: {request}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
