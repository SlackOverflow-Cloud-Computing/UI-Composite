from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.models.user import User  # CourseSection
from app.services.service_factory import ServiceFactory

router = APIRouter()

class LoginRequest(BaseModel):
    auth_code: str

@router.post("/login", tags=["users"])
async def login(request: LoginRequest):
    """Uses Spotify Auth Code to Login User

    Gets login service and sends authorization code to Spotify service
    The service returns a user model, and this should save it to the database
    """

    auth_code = request.auth_code
    login = ServiceFactory.get_service("Login")

    try:

        # Get details from Spotify integration service
        user = login.get_user_info(auth_code)
        print(f"Got info: {user}")
        if not user:
            print(f"Error for request: {request}")
            raise HTTPException(status_code=400, detail="Spotify Login Failed")

        return user

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
