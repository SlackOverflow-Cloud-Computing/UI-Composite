from dotenv import load_dotenv
import os

from framework.services.service_factory import BaseServiceFactory
from app.services.login import LoginService


SPOTIFY_URL = "http://127.0.0.1:8080"
USER_URL = "http://127.0.0.1:8088"

# Load environment variables from .env file
load_dotenv()

class ServiceFactory(BaseServiceFactory):

    def __init__(self):
        super().__init__()

    @classmethod
    def get_service(cls, service_name):

        match service_name:
            case "Login":
                result = LoginService(spotify_adapter_url=SPOTIFY_URL, user_url=USER_URL)

            case _:
                result = None

        return result
