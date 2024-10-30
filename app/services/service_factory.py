from framework.services.service_factory import BaseServiceFactory
from app.services.login import LoginService
from app.services.playlist import PlaylistService
import dotenv, os

dotenv.load_dotenv()
spotify_url = os.getenv('SPOTIFY_URL')
user_url = os.getenv('USER_URL')
playlist_url = "XXXX" # os.getenv('PLAYLIST_URL')

class ServiceFactory(BaseServiceFactory):

    def __init__(self):
        super().__init__()

    @classmethod
    def get_service(cls, service_name):

        match service_name:
            case "Login":
                result = LoginService(spotify_adapter_url=spotify_url, user_url=user_url)

            case "Playlist":
                result = PlaylistService(spotify_adapter_url=spotify_url, playlist_url=playlist_url)

            case _:
                result = None

        return result
