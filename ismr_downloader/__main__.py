import os
import logging
from .client import create_session
from .auth import AuthManager
from .downloader import Downloader
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

API_BASE = "https://api-ismrquerytool.fct.unesp.br/api/v1"
LOGIN_URL = f"{API_BASE}/user/token"
DOWNLOAD_URL = f"{API_BASE}/data/download/ismr"


def main():
    load_dotenv()
    email = os.getenv("ISMR_EMAIL")
    password = os.getenv("ISMR_PASSWORD")
    stations = os.getenv("ISMR_STATIONS", "").split(",")
    start_date = os.getenv("ISMR_START")
    end_date = os.getenv("ISMR_END")

    if not all([email, password, stations, start_date, end_date]):
        raise ValueError("Missing required environment variables in .env file")

    stations = [s.strip() for s in stations if s.strip()]

    session = create_session()
    auth = AuthManager(session, LOGIN_URL, email, password)

    # Authenticate only once at the start
    auth.authenticate()

    downloader = Downloader(session, auth, DOWNLOAD_URL)
    downloader.download(stations, start_date, end_date)


if __name__ == "__main__":
    main()