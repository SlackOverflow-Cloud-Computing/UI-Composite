import logging
from typing import List

from fastapi import APIRouter, HTTPException, status, Query, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.models.chat import Message
from app.models.song import Song, Traits
from app.services.service_factory import ServiceFactory

logger = logging.getLogger("uvicorn")
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class RecommendationRequest(BaseModel):
    message: str
    userId: str

@router.post(
    "/recommendations",
    tags=["recommendations"],
    response_model=List[Song],
    status_code=status.HTTP_200_OK
)
async def query_to_recommendations(
    req: RecommendationRequest,
    token: str = Depends(oauth2_scheme)
) -> List[Song]:
    """Given a user query, return recommended songs"""
    logger.info("Incoming Request - Method: POST, Path: /recommendations")

    chat_service = ServiceFactory.get_service("Chat")
    recommendation_service = ServiceFactory.get_service("Recommendation")

    query = Message(**{
        "query": req.message,
        "role": "human",
        "agent_name": "Recommendation"
    })

    try:
        chat_service.update_chat_database(query) # Store to database
        result = chat_service.extract_song_traits(query)
        logger.debug(f"Got song traits: {result}")

        result = recommendation_service.get_recommendations(token, result)
        logger.debug(f"Got song recommendations: {result}")
        return result
    except Exception as e:
        if isinstance(e, HTTPException):
            raise e
        else:
            raise HTTPException(status_code=500, detail=str(e))

@router.get("/recommendations/playlist", tags=["recommendations"], response_model=List[Song], status_code=status.HTTP_200_OK)
async def playlist_to_recommendations(song_ids: List[str] | None = Query(), token: str = Depends(oauth2_scheme)) -> List[Song]:
    """Given a list of song ids, return recommended songs"""

    logger.info(f"Incoming Request - Method: POST, Path: /playlist_recommendations")
    recommendation_service = ServiceFactory.get_service("Recommendation")
    traits = Traits(seed_tracks=song_ids)

    try:
        result = recommendation_service.get_recommendations(token, traits)
        logger.debug(f"Got song recommendations: {result}")
        return result
    except Exception as e:
        if isinstance(e, HTTPException): # Return any error specified in the chat service
            raise e
        else: # Otherwise default to generic server error
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/user_preference", tags=["preference"], status_code=status.HTTP_200_OK)
async def get_user_preference() -> str:
    """Return user preference analysis from user's chat history"""

    logger.info(f"Incoming Request - Method: POST, Path: /recommendations")
    chat_service = ServiceFactory.get_service("Chat")

    try:
        # TODO: temporary solution for user_id
        current_user_id = "8fa98871-2e6a-42e1-b602-00050e5a0ac4"
        result = chat_service.analyze_preference(user_id=current_user_id, chat_id=None)
        query = Message(**{
            "query": result,
            "role": "ai",
            "agent_name": "Preference"
        })
        chat_service.update_chat_database(query)  # Store to database
        return result
    except Exception as e:
        if isinstance(e, HTTPException):  # Return any error specified in the chat service
            raise e
        else:  # Otherwise default to generic server error
            raise HTTPException(status_code=500, detail=str(e))
