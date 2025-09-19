import os
import logging
import argparse
from .client import create_session
from .auth import AuthManager
from .downloader import Downloader
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

API_BASE = "https://api-ismrquerytool.fct.unesp.br/api/v1"
LOGIN_URL = f"{API_BASE}/user/token"

DATA_ENDPOINTS = {
    "ismr": "data/download/ismr",
    "sbf": "data/download/sbf",
    "rinex": "data/download/rinex",
    "ismr1min": "products/download/1min-ismr",
}


def main():
    parser = argparse.ArgumentParser(description="ISMR Downloader")
    parser.add_argument(
        "-f",
        "--force-auth",
        action="store_true",
        help="Force authentication and ignore cached token",
    )
    parser.add_argument(
        "-o",
        "--overwrite",
        action="store_true",
        help="Re-download files even if they already exist on disk",
    )
    args = parser.parse_args()

    load_dotenv()
    email = os.getenv("ISMR_EMAIL")
    password = os.getenv("ISMR_PASSWORD")
    stations = os.getenv("ISMR_STATIONS", "").split(",")
    start_date = os.getenv("ISMR_START")
    end_date = os.getenv("ISMR_END")
    data_type = os.getenv("DATA_TYPE", "ismr").lower()

    if data_type not in DATA_ENDPOINTS:
        raise ValueError(
            f"Invalid data type: {data_type}. "
            f"Options: {', '.join(DATA_ENDPOINTS.keys())}"
        )

    if not all([email, password, stations, start_date, end_date]):
        raise ValueError("Missing required environment variables in .env file")

    stations = [s.strip() for s in stations if s.strip()]

    session = create_session()
    auth = AuthManager(session, LOGIN_URL, email, password)

    # Authenticate (with --force-auth option)
    auth.authenticate(force=args.force_auth)

    download_url = f"{API_BASE}/{DATA_ENDPOINTS[data_type]}"
    downloader = Downloader(session, auth, download_url, overwrite=args.overwrite)

    try:
        downloader.download(stations, start_date, end_date)
    except SystemExit:
        logging.critical(
            "Downloader stopped due to repeated 429 Too Many Requests. "
            "Please wait and retry later."
        )


if __name__ == "__main__":
    main()
