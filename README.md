# ISMR Downloader

A Python tool for downloading GNSS/ISMR (Ionospheric Scintillation Monitoring Receiver) data from the **ISMR Query Tool API**.
It supports multiple data types, automatic token management, rate limiting, logging, progress bars, automatic date normalization, and chunk-based downloads for large time intervals.

---

## Requirements

- [Python](https://www.python.org/downloads/) **3.10+**
- [pip](https://pip.pypa.io/en/stable/installation/)
- [virtualenv](https://virtualenv.pypa.io/en/latest/) *(recommended)*

⚠ We recommend following [Conventional Commits](https://www.conventionalcommits.org/) ([cheatsheet](https://gist.github.com/qoomon/5dfcdf8eec66a051ecd85625518cfd13)) when contributing.

---

# Getting started

- Clone the repository

```bash
git clone git@github.com:GEGE-UNESP/ismr_downloader.git
```

- Create a virtual environment

**Windows (PowerShell)**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

**Linux/Mac**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

- Create a `.env` file

**Windows**
```powershell
type .env.example > .env
```

**Linux/Mac**
```bash
cp .env.example .env
```

Fill in your **API credentials and settings** inside `.env`:

```env
ISMR_EMAIL=your_email@example.com
ISMR_PASSWORD=your_password

# Data type: ismr | ismr1min | sbf | rinex
DATA_TYPE=ismr

ISMR_STATIONS=PRU2,MOR3

# When only a date is provided (YYYY-MM-DD),
# the downloader automatically expands:
#   start → 00:00:00
#   end   → 23:59:59
ISMR_START=2025-11-17
ISMR_END=2025-11-17
```

- Install dependencies

```bash
pip install -r requirements.txt
```

- Run the project

```bash
python -m ismr_downloader
```

---

# From prebuilt binary (Windows)

If you downloaded the `.exe` from the Releases page, just place it in the same folder as your `.env` file and run:

```bash
ismr_downloader.exe -f -e .env
```

- This avoids the need for Python or pip installation.
- Token caching, date normalization, chunking, and logs all work the same as in the Python version.

⚠ Make sure your `.exe` file has the same structure as the example.

---

# Date & Time Handling (UTC)

The downloader includes automatic datetime normalization:

- If you provide a full ISO timestamp:

```
2025-11-17T05:30:00
```

It is used exactly as written.

- If you provide only a date:

```
2025-11-17
```

It is expanded automatically to the full-day range:

| Field | Value assigned |
|-------|----------------|
| Start | 2025-11-17 **00:00:00** |
| End   | 2025-11-17 **23:59:59** |

This ensures correct, full-day coverage without manual timestamps.

---

# Chunked Download Strategy

The downloader automatically splits large date ranges into smaller chunks based on `max_days`:

- Prevents oversized API queries
- Improves reliability for long time spans
- Ensures the server returns complete data

Example:
If `max_days=15` and your range covers 90 days, it will automatically generate 6 chunks.

---

# Token Management

- API tokens are cached in `.token.json`
- Valid tokens are reused between runs
- Expired tokens are refreshed automatically
- Thread safety prevents race conditions during renewal

---

# Error Handling & Retries

The downloader includes robust handling for:

| Status | Action |
|--------|--------|
| **401** | Refresh token and retry |
| **404** | Logs a "no data" entry into a CSV |
| **429** | Automatic backoff with safe stop after repeated failures |
| **503** | Clean shutdown with clear maintenance message |
| **Timeouts** | Retries with delay |

Any interval without data is recorded into:

```
logs/no_data_YYYYMMDD_HHMMSS.csv
```

---

# Logs

All run logs are saved under the `logs/` folder with a timestamp:

- `run_YYYYMMDD_HHMMSS.log` → detailed logs
- `downloaded_files_YYYYMMDD_HHMMSS.txt` → list of downloaded/skipped files
- `no_data_YYYYMMDD_HHMMSS.csv` → intervals where the API returned no data

Progress bars are shown for each file download.

---

# Notes

- Default download folder is `downloads/`.
- The downloader automatically enforces request pacing via a built-in rate limiter.
- The tool supports both `bundle` and `temp_urls` modes from the API.
- The maximum query range is automatically chunked according to `max_days`.
- Progress bars appear for every downloaded file.