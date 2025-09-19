import json
import logging
from datetime import datetime, timedelta, timezone
import requests
from pathlib import Path
from threading import Lock


class AuthManager:
    _lock = Lock()

    def __init__(
        self,
        session: requests.Session,
        login_url: str,
        email: str,
        password: str,
        token_file: str = ".token.json",
    ):
        self.session = session
        self.login_url = login_url
        self.email = email
        self.password = password
        self.token_file = Path(token_file)
        self.token: str | None = None
        self.expires_at: datetime | None = None

    def _load_token(self) -> bool:
        if not self.token_file.exists():
            return False
        try:
            with open(self.token_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            self.token = data["access_token"]
            self.expires_at = datetime.fromisoformat(data["expires_at"])

            if self.is_token_valid():
                logging.info(
                    "Using cached token from file (expires at %s)",
                    self.expires_at.isoformat(),
                )
                return True
            else:
                logging.warning("Cached token expired")
                return False
        except Exception as e:
            logging.warning("Failed to load token from file: %s", e)
            return False

    def _save_token(self):
        if self.token and self.expires_at:
            data = {
                "access_token": self.token,
                "expires_at": self.expires_at.astimezone(timezone.utc).isoformat(),
            }
            with open(self.token_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    def is_token_valid(self) -> bool:
        if not self.token or not self.expires_at:
            return False
        return datetime.now(timezone.utc) < self.expires_at

    def authenticate(self, force: bool = False):
        """
        Authenticate user, refresh token if needed.
        Threads are synchronized with a lock to avoid multiple renewals.
        """
        with self._lock:
            if not force and self._load_token():
                return

            logging.info("Requesting new token from API")
            res = self.session.post(
                self.login_url,
                json={"email": self.email, "password": self.password},
                timeout=20,
            )
            res.raise_for_status()
            data = res.json()

            self.token = data.get("access_token")
            if not self.token:
                raise ValueError(f"Invalid token response: {data}")

            expires_at_str = data.get("expires_at")
            if expires_at_str:
                self.expires_at = datetime.fromisoformat(expires_at_str).astimezone(
                    timezone.utc
                )
            else:
                self.expires_at = datetime.now(timezone.utc) + timedelta(hours=3)

            self._save_token()
            logging.info(
                "New token acquired (expires at %s)", self.expires_at.isoformat()
            )
