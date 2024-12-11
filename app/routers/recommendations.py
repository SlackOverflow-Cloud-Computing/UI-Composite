import logging
import uuid
from typing import Optional, List, Union
from fastapi import APIRouter, HTTPException, Request, status, Query, Depends
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel

from app.models.chat import Message, ChatData, WebChat
from app.models.song import Song, Traits
from app.services.service_factory import ServiceFactory

logger = logging.getLogger("uvicorn")
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class RecommendationRequest(BaseModel):
    message: str
    userId: str


@router.post("/chats", tags=["chats"], status_code=status.HTTP_200_OK)
async def general_chat(request: Request) -> WebChat:
    """Process the general chat and give the recommendation when needed"""
    data = await request.json()
    user_id = data.get("user_id")
    chat_id = data.get("chat_id")
    query = data.get("query")
    token = data.get("token")

    if chat_id is None:
        chat_id = str(uuid.uuid4())

    logger.info(f"Incoming Request - Method: POST, Path: /chats")
    chat_service = ServiceFactory.get_service("Chat")
    chat_data = ChatData(
        content=query,
        role="human",
        agent_name="Chat",
        chat_id=chat_id,
        user_id=user_id
    )
 
    if not chat_service.validate_token(token, id=user_id, scope=("/chats", "POST")):
        raise HTTPException(status_code=401, detail="Invalid Token")

    try:
        # Get natural language response and optionally traits
        chat_service.update_chat_database(chat_data)
        agent_response = chat_service.general_chat(query=query, user_id=user_id, chat_id=chat_id)
        if agent_response:
            chat_message = agent_response.content
            chat_data = ChatData(
                content=chat_message,
                role="ai",
                agent_name="Chat",
                chat_id=chat_id,
                user_id=user_id
            )
            chat_service.update_chat_database(chat_data)
            if agent_response.traits:
                # traits = chat_service.extract_song_traits(agent_response.traits)
                traits = agent_response.traits
                logger.debug(f"Got song traits: {traits}")
                recommendation_service = ServiceFactory.get_service("Recommendation")
                user_service = ServiceFactory.get_service("User")
                song_service = ServiceFactory.get_service("Song")
                spotify_token = user_service.get_spotify_token(user_id, token)
                songs = recommendation_service.get_recommendations(token, spotify_token, traits)
                logger.debug(f"Got song recommendations: {songs}")  
                logger.debug(f"Adding new songs to db: {traits}")
                song_service.add_songs(token, songs)
                logger.debug(f"Added new songs to db: {traits}")
                response_data = WebChat(
                    content=chat_message,
                    songs=songs
                )
            else:
                response_data = WebChat(
                    content=chat_message,
                    songs=None
                )
            return response_data
        else:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Couldn't get chat response")
    except Exception as e:
        if isinstance(e, HTTPException):  # Return any error specified in the chat service
            raise e
        else:  # Otherwise default to generic server error
            raise HTTPException(status_code=500, detail=str(e))


@router.post(
    "/recommendations",
    tags=["recommendations"],
    response_model=List[Song],
    status_code=status.HTTP_200_OK
)
async def query_to_recommendations(
    req: RecommendationRequest,
    user_id: str,
    token: str = Depends(oauth2_scheme),
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

    logger.info(f"Incoming Request - Method: GET, Path: /recommendations")
    chat_service = ServiceFactory.get_service("Chat")
    recommendation_service = ServiceFactory.get_service("Recommendation")
    # query = Message(query=query)
    chat_data = ChatData(
        content=query,
        role="human",
        agent_name="Recommendation",
    )

    try:
        chat_service.update_chat_database(chat_data)  # Store to database
        result = chat_service.extract_song_traits(query)
        logger.debug(f"Got song traits: {result}")

        user_service = ServiceFactory.get_service("User")
        spotify_token = user_service.get_spotify_token(user_id, token)
        result = recommendation_service.get_recommendations(token, spotify_token, result)
        logger.debug(f"Got song recommendations: {result}")
        return result
    except Exception as e:

        if isinstance(e, HTTPException):  # Return any error specified in the chat service
            raise e
        else:  # Otherwise default to generic server error
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/playlist", tags=["recommendations"], response_model=List[Song], status_code=status.HTTP_200_OK)
async def playlist_to_recommendations(
    user_id: str,
    song_ids: Union[List[str], None] = Query(default=None),
    token: str = Depends(oauth2_scheme)
) -> List[Song]:
    """Given a list of song ids, return recommended songs"""

    logger.info(f"Incoming Request - Method: GET, Path: /recommendations/playlist")

    recommendation_service = ServiceFactory.get_service("Recommendation")
    traits = Traits(seed_tracks=song_ids)

    try:
        user_service = ServiceFactory.get_service("User")
        spotify_token = user_service.get_spotify_token(user_id, token)
        result = recommendation_service.get_recommendations(token, spotify_token, result)
        logger.debug(f"Got song recommendations: {result}")
        return result
    except Exception as e:
        if isinstance(e, HTTPException):  # Return any error specified in the chat service
            raise e
        else:  # Otherwise default to generic server error
            raise HTTPException(status_code=500, detail=str(e))


@router.get("/user_preference", tags=["preference"], status_code=status.HTTP_200_OK)
async def get_user_preference(user_id: str, chat_id: Optional[str] = None) -> str:
    """Return user preference analysis from user's chat history"""

    logger.info(f"Incoming Request - Method: GET, Path: /user_preference")
    chat_service = ServiceFactory.get_service("Chat")

    try:
        result = chat_service.analyze_preference(user_id=user_id, chat_id=chat_id)
        chat_data = ChatData(
            content=result,
            role="ai",
            agent_name="Preference"
        )
        chat_service.update_chat_database(chat_data)  # Store to database
        return result
    except Exception as e:
        if isinstance(e, HTTPException):  # Return any error specified in the chat service
            raise e
        else:  # Otherwise default to generic server error
            raise HTTPException(status_code=500, detail=str(e))
