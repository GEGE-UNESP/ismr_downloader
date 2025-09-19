import time
import logging
import csv
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
        max_days: int = 15,
        overwrite: bool = False,
    ):
        self.session = session
        self.auth = auth
        self.download_url = download_url
        self.max_requests_per_minute = max_requests_per_minute
        self.request_interval = 60.0 / max_requests_per_minute
        self.max_error_tolerance = max_error_tolerance
        self.max_workers = max_workers
        self.error_count = 0
        self.max_days = max_days
        self.too_many_requests_count = 0
        self.overwrite = overwrite

        # Prepare logs directory
        Path(logs_dir).mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.run_log_file = Path(logs_dir) / f"run_{timestamp}.log"
        self.files_log_file = Path(logs_dir) / f"downloaded_files_{timestamp}.txt"
        self.no_data_file = Path(logs_dir) / f"no_data_{timestamp}.csv"

        # Init CSV file with header
        with open(self.no_data_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["dataset", "station", "start", "end", "message"])

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(self.run_log_file, mode="a", encoding="utf-8"),
            ],
        )

    def _save_file_log(self, filepath: Path, status: str = "downloaded") -> None:
        with open(self.files_log_file, "a", encoding="utf-8") as f:
            f.write(f"{status.upper()}: {filepath}\n")

    def _save_no_data_csv(
        self, dataset: str, station: str, start: datetime, end: datetime, msg: str
    ) -> None:
        """Save no-data intervals into CSV file."""
        with open(self.no_data_file, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow([dataset, station, start.date(), end.date(), msg])

    def _ensure_token_valid(self):
        """Ensure the token is still valid before making requests."""
        if not self.auth.is_token_valid():
            logging.info("Token expired or missing. Refreshing...")
            self.auth.authenticate(force=True)

    def _download_chunk(
        self, station: str, start: datetime, end: datetime, save_dir: Path
    ) -> Optional[List[Path]]:
        """
        Try downloading a chunk of data.
        - 404 (no data) → log into CSV, no retry.
        - 429 (too many requests) → stop after 2 occurrences.
        - Timeout/network errors → retry up to 3 times.
        - Supports: bundle (zip), temp_urls (multiple files).
        """
        params = {
            "start": start.isoformat(),
            "end": end.isoformat(),
            "station": station,
        }
        dataset = self.download_url.split("/")[-1].upper()

        for attempt in range(1, 4):
            try:
                self._ensure_token_valid()
                response = self.session.get(
                    self.download_url,
                    params=params,
                    headers={"Authorization": f"Bearer {self.auth.token}"},
                    timeout=120,
                )

                if response.status_code == 404:
                    try:
                        msg = response.json().get("message", "No data available")
                    except Exception:
                        msg = "No data available"
                    logging.warning(
                        "[%s] %s %s→%s → %s",
                        dataset,
                        station,
                        start.date(),
                        end.date(),
                        msg,
                    )
                    self._save_no_data_csv(dataset, station, start, end, msg)
                    return None

                if response.status_code == 401:
                    logging.warning("[%s] Unauthorized. Refreshing token...", dataset)
                    self.auth.authenticate(force=True)
                    continue

                if response.status_code == 429:
                    self.too_many_requests_count += 1
                    logging.error(
                        "[%s] Too many requests (%d/2).",
                        dataset,
                        self.too_many_requests_count,
                    )
                    if self.too_many_requests_count >= 2:
                        logging.critical(
                            "[%s] Too many requests twice. Stopping execution.", dataset
                        )
                        raise SystemExit(1)
                    else:
                        self.auth.authenticate(force=True)
                        time.sleep(10)
                        continue
                else:
                    self.too_many_requests_count = 0

                response.raise_for_status()
                data = response.json()
                downloaded_paths: List[Path] = []

                if "bundle" in data and data["bundle"]:
                    bundle = data["bundle"]
                    filepath = self._download_file(
                        dataset,
                        station,
                        start,
                        end,
                        attempt,
                        bundle["url"],
                        bundle["filename"],
                        save_dir,
                    )
                    if filepath:
                        downloaded_paths.append(filepath)

                elif "temp_urls" in data and data["temp_urls"]:
                    for entry in data["temp_urls"]:
                        filename = entry.get("filename", "file.dat")
                        filepath = self._download_file(
                            dataset,
                            station,
                            start,
                            end,
                            attempt,
                            entry["url"],
                            filename,
                            save_dir,
                        )
                        if filepath:
                            downloaded_paths.append(filepath)

                else:
                    msg = "No bundle/temp_urls returned"
                    logging.warning(
                        "[%s] %s %s→%s → %s",
                        dataset,
                        station,
                        start.date(),
                        end.date(),
                        msg,
                    )
                    self._save_no_data_csv(dataset, station, start, end, msg)
                    return None

                return downloaded_paths if downloaded_paths else None

            except requests.Timeout as e:
                logging.error(
                    "[%s] Timeout %s %s→%s [Attempt %d]: %s",
                    dataset,
                    station,
                    start.date(),
                    end.date(),
                    attempt,
                    e,
                )
                time.sleep(5)

            except requests.RequestException as e:
                logging.error(
                    "[%s] Error %s %s→%s [Attempt %d]: %s",
                    dataset,
                    station,
                    start.date(),
                    end.date(),
                    attempt,
                    e,
                )
                time.sleep(5)

            finally:
                time.sleep(self.request_interval)

        return None

    def _download_file(
        self,
        dataset: str,
        station: str,
        start: datetime,
        end: datetime,
        attempt: int,
        url: str,
        filename: str,
        save_dir: Path,
    ) -> Optional[Path]:
        """Helper to download a single file with tqdm progress bar (skip or overwrite)."""
        self._ensure_token_valid()
        filepath = save_dir / filename

        if filepath.exists() and not self.overwrite:
            logging.info("[%s] Skipping existing file: %s", dataset, filepath)
            self._save_file_log(filepath, status="skipped")
            return filepath

        logging.info(
            "[%s] Downloading %s (%s → %s) [Attempt %d]",
            dataset,
            filename,
            start.date(),
            end.date(),
            attempt,
        )

        with self.session.get(
            url,
            headers={"Authorization": f"Bearer {self.auth.token}"},
            stream=True,
            timeout=900,
        ) as res:
            if res.status_code == 401:
                logging.error(
                    "[%s] Unauthorized when fetching %s. Token expired?",
                    dataset,
                    filename,
                )
                self._ensure_token_valid()
                return None

            res.raise_for_status()
            total_size = int(res.headers.get("content-length", 0))
            block_size = 8192
            with open(filepath, "wb") as f, tqdm(
                total=total_size if total_size else None,
                unit="B",
                unit_scale=True,
                desc=f"{dataset}-{filename}",
                ascii=True,
            ) as bar:
                for chunk in res.iter_content(chunk_size=block_size):
                    if chunk:
                        f.write(chunk)
                        bar.update(len(chunk))

        logging.info("[%s] Download completed: %s", dataset, filepath)
        self._save_file_log(filepath, status="downloaded")
        self.error_count = 0
        return filepath

    def _summarize_run(self, downloaded_files: List[Path]) -> None:
        dataset = self.download_url.split("/")[-1].upper()
        total_size = sum(f.stat().st_size for f in downloaded_files if f.exists())

        logging.info("[%s] ========= SUMMARY =========", dataset)
        logging.info("[%s] Files downloaded: %d", dataset, len(downloaded_files))
        logging.info("[%s] Total size: %.2f MB", dataset, total_size / (1024 * 1024))
        logging.info("[%s] Errors during run: %d", dataset, self.error_count)
        logging.info("[%s] No-data file saved in: %s", dataset, self.no_data_file)
        logging.info("[%s] Run log file: %s", dataset, self.run_log_file)
        logging.info("[%s] Files list: %s", dataset, self.files_log_file)
        logging.info("[%s] ===========================", dataset)

    def download(
        self, stations: List[str], start: str, end: str, save_dir: str = "downloads"
    ) -> List[Path]:
        save_dir = Path(save_dir)
        save_dir.mkdir(parents=True, exist_ok=True)

        start_dt = datetime.fromisoformat(start)
        end_dt = datetime.fromisoformat(end)

        results: List[Path] = []
        futures = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            for station in stations:
                for s, e in daterange_chunks(start_dt, end_dt, max_days=self.max_days):
                    futures.append(
                        executor.submit(self._download_chunk, station, s, e, save_dir)
                    )

            for future in as_completed(futures):
                result = future.result()
                if result:
                    if isinstance(result, list):
                        results.extend(result)
                    else:
                        results.append(result)

        self._summarize_run(results)
        return results
