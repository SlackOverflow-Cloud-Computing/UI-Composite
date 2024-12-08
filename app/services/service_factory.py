from framework.services.service_factory import BaseServiceFactory
from app.services.user import UserService
from app.services.playlist import PlaylistService
from app.services.chat import ChatService
from app.services.recommendation import RecommandationService
import dotenv, os

dotenv.load_dotenv()
spotify_url = os.getenv('SPOTIFY_URL')
user_url = os.getenv('USER_URL')

chat_url = os.getenv('CHAT_URL')
playlist_url = os.getenv('PLAYLIST_URL')

class ServiceFactory(BaseServiceFactory):

    def __init__(self):
        super().__init__()

    @classmethod
    def get_service(cls, service_name):

        if service_name == "User":
            result = UserService(spotify_adapter_url=spotify_url, user_url=user_url, playlist_url=playlist_url)
        elif service_name == "Playlist":
            result = PlaylistService(spotify_adapter_url=spotify_url, user_url=user_url, playlist_url=playlist_url)
        elif service_name == "Chat":
            result = ChatService(chat_url=chat_url, user_url=user_url)
        elif service_name == "Recommendation":
            result = RecommandationService(spotify_adapter_url=spotify_url)
        else:
            result = None

        return result
