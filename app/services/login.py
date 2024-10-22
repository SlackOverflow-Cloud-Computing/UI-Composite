import requests
from pydantic import ValidationError
import logging

from app.models.user import User


class LoginService:

    def __init__(self, spotify_adapter_url: str, user_url: str):
        self.spotify_url = spotify_adapter_url  # URL of the Spotify integration service
        self.user_url = user_url

    def get_user_info(self, auth_code):
        payload = {'auth_code': auth_code}
        user = None

        # Send a POST request to the Spotify integration service to exchange the auth code for user info
        try:
            response = requests.post(f"{self.spotify_url}/login", json=payload)

            # Check if the request was successful
            if response.status_code != 200:
                return None

            # Pass user and token response to the User service
            data = response.json()
            current_data = requests.post(f"{self.user_url}/update_user", json=data)

            # Try to parse the response into a User model
            user = User.parse_obj(current_data.json())
            return user

        except requests.RequestException as e:
            logging.error(f"Request failed: {str(e)}")
            raise e
