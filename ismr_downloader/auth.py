import logging
from datetime import datetime
import requests

class AuthManager:
    def __init__(self, session: requests.Session, login_url: str, email: str, password: str):
        self.session = session
        self.login_url = login_url
        self.email = email
        self.password = password
        self.token_info = {"access_token": None, "expires_at": None}

    def is_token_valid(self) -> bool:
        if not self.token_info["access_token"]:
            return False
        if not self.token_info["expires_at"]:
            return True  # API does not always return expires_at
        expires_at = datetime.fromisoformat(self.token_info["expires_at"].replace("Z", "+00:00"))
        return expires_at > datetime.now()

    def authenticate(self, force: bool = False) -> None:
        if not force and self.is_token_valid():
            return

        logging.info("Requesting new token")
        res = self.session.post(
            self.login_url,
            json={"email": self.email, "password": self.password},
            timeout=20,
        )
        res.raise_for_status()
        data = res.json()

        token = data.get("token") or data.get("access_token")
        expires_at = data.get("expires_at")

        if not token:
            raise ValueError(f"Unexpected login response: {data}")

        self.token_info.update({"access_token": token, "expires_at": expires_at})
        self.session.headers.update(
            {
                "accept": "application/json",
                "Authorization": f"Bearer {token}",
            }
        )