import logging
from fastapi import APIRouter, HTTPException, status, Query
from typing import List


from app.models.chat import Message
from app.models.song import Song, Traits
from app.services.service_factory import ServiceFactory

logger = logging.getLogger("uvicorn")
router = APIRouter()


@router.get("/recommendations", tags=["recommendations"], response_model=List[Song], status_code=status.HTTP_200_OK)
async def query_to_recommendations(query: str) -> List[Song]:
    """Given a user query, return recommended songs"""
    
    logger.info(f"Incoming Request - Method: POST, Path: /recommendations")
    chat_service = ServiceFactory.get_service("Chat")
    recommendation_service = ServiceFactory.get_service("Recommendation")
    query = Message(query=query)
    
    try:
        result = chat_service.extract_song_traits(query)
        logger.debug(f"Got song traits: {result}")
        result = recommendation_service.get_recommendations(result)
        logger.debug(f"Got song recommendations: {result}")
        return result
    except Exception as e:
        if isinstance(e, HTTPException): # Return any error specified in the chat service
            raise e
        else: # Otherwise default to generic server error
            raise HTTPException(status_code=500, detail=str(e))

@router.get("/playlist_recommendations", tags=["recommendations"], response_model=List[Song], status_code=status.HTTP_200_OK)
async def query_to_recommendations(song_ids: List[str] | None = Query()) -> List[Song]:
    """Given a list of song ids, return recommended songs"""
    
    logger.info(f"Incoming Request - Method: POST, Path: /playlist_recommendations")
    recommendation_service = ServiceFactory.get_service("Recommendation")
    traits = Traits(seed_tracks=song_ids)
    
    try:
        result = recommendation_service.get_recommendations(traits)
        logger.debug(f"Got song recommendations: {result}")
        return result
    except Exception as e:
        if isinstance(e, HTTPException): # Return any error specified in the chat service
            raise e
        else: # Otherwise default to generic server error
            raise HTTPException(status_code=500, detail=str(e))