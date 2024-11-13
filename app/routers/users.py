import logging
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.models.user import User  # CourseSection
from app.services.service_factory import ServiceFactory

logger = logging.getLogger("uvicorn")
router = APIRouter()

class LoginRequest(BaseModel):
    auth_code: str

@router.post("/login", tags=["users"], status_code=status.HTTP_201_CREATED)
async def login(request: LoginRequest):
    """Uses Spotify Auth Code to Login User

    Gets login service and sends authorization code to Spotify service
    The service returns a user model, and this should save it to the database
    """

    logger.info(f"Incoming Request - Method: POST, Path: /login, Body: {request.dict()}")
    auth_code = request.auth_code
    user_service = ServiceFactory.get_service("User")

    try:

        # Get details from Spotify integration service
        user = user_service.login(auth_code)
        logger.debug(f"User info received: {user}")
        if not user:
            logger.error(f"Login failed for auth_code: {auth_code}")
            raise HTTPException(status_code=400, detail="Spotify Login Failed")

        logger.info(f"Response - Method: POST, Path: /login, Status: 200, Body: {user.dict()}")
        return user

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}", tags=["users"])
async def get_user(user_id: str):
    """Gets a User's Public Information"""

    logger.info(f"Incoming Request - Method: GET, Path: /users/{user_id}")
    user_service = ServiceFactory.get_service("User")

    try:
        # Get details from Spotify integration service
        user = user_service.get_user(user_id)
        logger.debug(f"User info: {user}")
        if not user:
            logger.error(f"Failed to get user info for {user_id}")
            raise HTTPException(status_code=400, detail="User does not use Subwoofer")

        logger.info(f"Response - Method: GET, Path: /users/{user_id}, Status: 200, Body: {user.dict()}")
        return user

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/playlists", tags=["users"])
async def get_user_playlists(user_id: str):
    """Gets a User's Playlists

    TODO: Optional authentication to get private playlists

    Checks information from Spotify and updates our database behind
    the scenes with the latest information.
    """

    logger.info(f"Incoming Request - Method: GET, Path: /users/{user_id}/playlists")
    user_service = ServiceFactory.get_service("User")

    try:
        # Get details from Spotify integration service
        playlists = user_service.get_user_playlists(user_id)
        logger.debug(f"User playlists: {playlists}")
        if not playlists:
            logger.error(f"Failed to get playlists for user {user_id}")
            raise HTTPException(status_code=400, detail="User does not have any playlists")

        logger.info(f"Response - Method: GET, Path: /users/{user_id}/playlists, Status: 200, Body: {playlists}")
        return playlists

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
