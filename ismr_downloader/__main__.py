import os
import logging
import argparse
from dotenv import load_dotenv

from ismr_downloader.client import create_session
from ismr_downloader.auth import AuthManager
from ismr_downloader.downloader import Downloader

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

    # Authentication
    parser.add_argument("--email", help="Email for authentication")
    parser.add_argument("--password", help="Password for authentication")
    parser.add_argument(
        "-f", "--force-auth", action="store_true", help="Force authentication"
    )
    parser.add_argument(
        "--token-file",
        help="Path to token cache file (default: .token.json or $ISMR_TOKEN_FILE)",
    )

    # Input dataset parameters
    parser.add_argument("--stations", help="Comma-separated list of stations")
    parser.add_argument("--start", help="Start datetime (ISO format)")
    parser.add_argument("--end", help="End datetime (ISO format)")
    parser.add_argument(
        "--data-type",
        choices=list(DATA_ENDPOINTS.keys()),
        help="Data type to download (ismr, sbf, rinex, ismr1min)",
    )

    # Downloader configuration
    parser.add_argument(
        "--overwrite", action="store_true", help="Overwrite existing files"
    )
    parser.add_argument("--max-workers", type=int, help="Number of parallel downloads")
    parser.add_argument("--max-days", type=int, help="Max days per chunk")
    parser.add_argument("--max-req", type=int, help="Max requests per minute")
    parser.add_argument("--logs-dir", default=None, help="Directory for logs")
    parser.add_argument(
        "--output-dir",
        help="Directory where downloaded files will be stored "
        "(default: 'downloads' or $ISMR_OUTPUT_DIR)",
    )

    # SSL
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS certificate verification (not recommended in production)",
    )

    # Environment file
    parser.add_argument(
        "-e", "--env", default=".env", help="Path to .env file (default: .env)"
    )

    args = parser.parse_args()

    load_dotenv(args.env)

    # Authentication values
    email = args.email or os.getenv("ISMR_EMAIL")
    password = args.password or os.getenv("ISMR_PASSWORD")

    # Stations (CLI > env)
    stations_env = os.getenv("ISMR_STATIONS", "")
    stations_cli = args.stations
    stations = stations_cli.split(",") if stations_cli else stations_env.split(",")
    stations = [s.strip() for s in stations if s.strip()]

    # Dates (CLI > env)
    start_date = args.start or os.getenv("ISMR_START")
    end_date = args.end or os.getenv("ISMR_END")

    # Data type (CLI > env > default)
    data_type = (args.data_type or os.getenv("DATA_TYPE", "ismr")).lower()

    if data_type not in DATA_ENDPOINTS:
        raise ValueError(
            f"Invalid data type: {data_type}. Options: {', '.join(DATA_ENDPOINTS.keys())}"
        )

    # Output dir (CLI > env > default)
    output_dir = args.output_dir or os.getenv("ISMR_OUTPUT_DIR", "downloads")

    # Token file (CLI > env > default)
    token_file = args.token_file or os.getenv("ISMR_TOKEN_FILE", ".token.json")

    # Basic validation
    if not email or not password:
        raise SystemExit("Email and password must be provided (via CLI or .env).")
    if not stations:
        raise SystemExit("At least one station must be provided (via CLI or .env).")
    if not start_date or not end_date:
        raise SystemExit("Start and end dates must be provided (via CLI or .env).")

    # Create session/auth
    verify_ssl = not args.insecure
    session = create_session(verify_ssl=verify_ssl)
    auth = AuthManager(session, LOGIN_URL, email, password, token_file=token_file)
    auth.authenticate(force=args.force_auth)

    # Downloader configuration (CLI overrides defaults)
    downloader_kwargs = {}
    if args.overwrite:
        downloader_kwargs["overwrite"] = True
    if args.max_workers:
        downloader_kwargs["max_workers"] = args.max_workers
    if args.max_days:
        downloader_kwargs["max_days"] = args.max_days
    if args.max_req:
        downloader_kwargs["max_requests_per_minute"] = args.max_req
    if args.logs_dir:
        downloader_kwargs["logs_dir"] = args.logs_dir

    download_url = f"{API_BASE}/{DATA_ENDPOINTS[data_type]}"

    downloader = Downloader(session, auth, download_url, **downloader_kwargs)

    try:
        downloader.download(stations, start_date, end_date, save_dir=output_dir)
    except SystemExit as e:
        logging.critical(str(e))


if __name__ == "__main__":
    main()
