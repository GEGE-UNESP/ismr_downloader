import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed
import requests
from tqdm import tqdm

from .auth import AuthManager
from .utils import daterange_chunks


class Downloader:
    def __init__(
        self,
        session: requests.Session,
        auth: AuthManager,
        download_url: str,
        max_requests_per_minute: int = 30,
        max_error_tolerance: int = 3,
        max_workers: int = 5,
        logs_dir: str = "logs",
    ):
        self.session = session
        self.auth = auth
        self.download_url = download_url
        self.max_requests_per_minute = max_requests_per_minute
        self.request_interval = 60.0 / max_requests_per_minute
        self.max_error_tolerance = max_error_tolerance
        self.max_workers = max_workers
        self.error_count = 0

        # Prepare logs directory
        Path(logs_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_log_file = Path(logs_dir) / f"run_{timestamp}.log"
        self.files_log_file = Path(logs_dir) / f"downloaded_files_{timestamp}.txt"

        # Configure logging for this run
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.run_log_file, mode="a", encoding="utf-8"),
            ],
        )

    def _save_file_log(self, filepath: Path) -> None:
        """Append downloaded file name to this run's log file."""
        with open(self.files_log_file, "a", encoding="utf-8") as f:
            f.write(str(filepath) + "\n")

    def _download_chunk(
        self, station: str, start: datetime, end: datetime, save_dir: Path
    ) -> Optional[Path]:
        params = {"start": start.isoformat(), "end": end.isoformat(), "station": station}
        try:
            response = self.session.get(self.download_url, params=params, timeout=30)

            if response.status_code == 401:
                logging.warning("Token invalid. Renewing and retrying once...")
                self.auth.authenticate(force=True)
                response = self.session.get(self.download_url, params=params, timeout=30)

            response.raise_for_status()
            data = response.json()
            bundle = data.get("bundle")
            if not bundle:
                logging.error("Unexpected response: %s", data)
                self.error_count += 1
                return None

            download_url = bundle["url"]
            filename = bundle["filename"]
            filepath = save_dir / filename

            logging.info("Downloading %s (%s → %s)", filename, start.date(), end.date())

            with self.session.get(download_url, stream=True, timeout=60) as res:
                res.raise_for_status()
                total_size = int(res.headers.get("content-length", 0))
                block_size = 8192

                with open(filepath, "wb") as f, tqdm(
                    total=total_size,
                    unit="B",
                    unit_scale=True,
                    desc=filename,
                    ascii=True,
                ) as bar:
                    for chunk in res.iter_content(chunk_size=block_size):
                        if chunk:
                            f.write(chunk)
                            bar.update(len(chunk))

            logging.info("Download completed: %s", filepath)
            self._save_file_log(filepath)

            self.error_count = 0
            return filepath

        except requests.RequestException as e:
            logging.error("Error downloading %s %s→%s: %s", station, start, end, e)
            self.error_count += 1
            if self.error_count >= self.max_error_tolerance:
                logging.warning("Too many errors. Forcing token renewal...")
                self.auth.authenticate(force=True)
                self.error_count = 0
            return None
        finally:
            time.sleep(self.request_interval)

    def _summarize_run(self, downloaded_files: List[Path]) -> None:
        """Generate a summary of the run: files, size, errors, logs."""
        total_size = sum(f.stat().st_size for f in downloaded_files if f.exists())
        logging.info("========== SUMMARY ==========")
        logging.info("Files downloaded: %d", len(downloaded_files))
        logging.info("Total size: %.2f MB", total_size / (1024 * 1024))
        logging.info("Errors during run: %d", self.error_count)
        logging.info("Run log file: %s", self.run_log_file)
        logging.info("Files list: %s", self.files_log_file)
        logging.info("=============================")

    def download(
        self, stations: List[str], start: str, end: str, save_dir: str = "downloads"
    ) -> List[Path]:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)

        results = []
        futures = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for station in stations:
                for s, e in daterange_chunks(start_dt, end_dt):
                    futures.append(
                        executor.submit(self._download_chunk, station, s, e, save_dir)
                    )

            for future in as_completed(futures):
                result = future.result()
                if result:
                    results.append(result)

        self._summarize_run(results)
        return results