# ISMR Downloader

**ISMR Downloader** is a Python-based command-line tool designed to retrieve GNSS/ISMR (Ionospheric Scintillation Monitoring Receiver) data from the **ISMR Query Tool API**. It provides a modern, reliable, and convenient workflow with:

- Multiple dataset types (ISMR, RINEX, SBF, 1‑minute ISMR)
- Automatic token authentication and caching
- Chunked date‑range handling for long intervals
- Parallel downloads with rate limiting
- Detailed logging and data‑quality tracking
- Full `.env` integration for simple configuration
- Windows `.exe` binary support (no Python required)

This tool is suitable for researchers, engineers, and analysts working with GNSS scintillation data.

---

# Installation

## Install from PyPI (recommended)

```bash
pip install ismr-downloader
```

Verify installation:

```bash
ismr-downloader --help
```

---

# Manual Installation (Step‑by‑Step Guide)

This section is intended for users who prefer running the tool directly from source (for development, customization and more).

# Requirements

- [Python](https://www.python.org/downloads/) **3.10+**
- [pip](https://pip.pypa.io/en/stable/installation/)
- [virtualenv](https://virtualenv.pypa.io/en/latest/) *(recommended)*

---

## 1. Clone the repository

```bash
git clone https://github.com/GEGE-UNESP/ismr_downloader.git
cd ismr_downloader
```

If using SSH:

```bash
git clone git@github.com:GEGE-UNESP/ismr_downloader.git
cd ismr_downloader
```

---

## 2. Create a virtual environment

### Windows (PowerShell)

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should now see `(.venv)` at the start of your terminal prompt.

---

## 3. Create and configure your `.env` file

### Windows

```powershell
type .env.example > .env
```

### Linux / macOS

```bash
cp .env.example .env
```

Now open `.env` and fill in your API credentials and settings:

```env
ISMR_EMAIL=your_email@example.com
ISMR_PASSWORD=your_password

# Supported types: ismr | ismr1min | sbf | rinex
DATA_TYPE=ismr

# Comma-separated list of stations
ISMR_STATIONS=PRU2,MOR3

# When only a date is provided (YYYY-MM-DD),
# the downloader automatically expands it to:
#   start → 00:00:00
#   end   → 23:59:59
ISMR_START=2025-11-17
ISMR_END=2025-11-17
```

---

## 4. Install project dependencies

With the virtual environment activated:

```bash
pip install -r requirements.txt
```

---

## 5. Run the project manually

### Using command‑line arguments

```bash
python -m ismr_downloader --stations MOR3 --start "2025-11-24T00:00:00" --end "2025-11-24T00:30:00" --data-type ismr --insecure
```

### Using a `.env` file

```bash
python -m ismr_downloader --env .env --insecure
```

---

# Quick Example (PyPI version)

```bash
ismr-downloader --email "your_email" --password "your_password" --stations MOR3 --start "2025-11-24T00:00:00" --end "2025-11-24T00:30:00" --data-type ismr --insecure
```

Using `.env`:

```bash
ismr-downloader --env ".env" --insecure
```

---

# Command‑Line Arguments

| Argument | Description |
|----------|-------------|
| `--email EMAIL` | Email for authentication. |
| `--password PASSWORD` | Password for authentication. |
| `-f`, `--force-auth` | Force authentication (ignore cached token). |
| `--token-file PATH` | Token cache file (default: `.token.json`). |
| `--stations STATIONS` | Comma‑separated list of stations. |
| `--start START` | Start datetime (`YYYY-MM-DD` or ISO timestamp). |
| `--end END` | End datetime (`YYYY-MM-DD` or ISO timestamp). |
| `--data-type {ismr,sbf,rinex,ismr1min}` | Dataset type. |
| `--overwrite` | Overwrite existing files. |
| `--max-workers N` | Number of parallel downloads. |
| `--max-days N` | Maximum days per chunk. |
| `--max-req N` | Max requests per minute. |
| `--logs-dir DIR` | Directory for logs. |
| `--output-dir DIR` | Target directory (default: `downloads/`). |
| `--insecure` | Disable SSL verification. |
| `-e`, `--env FILE` | Path to `.env` file (default: `.env`). |

---

# Date & Time Handling (UTC)

- If you provide a **full timestamp**, it is used as-is:
  ```
  2025-11-17T05:30:00
  ```

- If you provide a **date only**:
  ```
  2025-11-17
  ```

It expands to:

| Field | Value |
|-------|-------|
| Start | 2025‑11‑17 **00:00:00** |
| End   | 2025‑11‑17 **23:59:59** |

---

# Chunked Download Strategy

Large date ranges are broken into smaller, safe chunks (via `--max-days`).
Example: a 90‑day range with `max-days=15` → **6 chunks**.

---

# Token Management

- Cached in `.token.json`
- Auto‑refreshed when expired
- Thread‑safe during parallel operations

---

# Error Handling

| Status | Behavior |
|--------|----------|
| **401** | Refresh token and retry |
| **404** | Interval logged to CSV |
| **429** | Rate‑limit backoff |
| **503** | Graceful shutdown |
| **Timeout** | Automatic retry |

Missing‑data intervals are logged to:

```
logs/no_data_YYYYMMDD_HHMMSS.csv
```

---

# Logging

Each run creates a timestamped folder under `logs/`:

- `run_*.log` — detailed execution log
- `downloaded_files_*.txt` — downloaded/skipped files
- `no_data_*.csv` — time intervals with no available data

---

# Windows Binary (.exe)

Download the `.exe` from GitHub Releases and place it next to your `.env` file.

Run:

```bash
ismr_downloader.exe --env .env --insecure
```

No Python installation required.

---
#  Running with Docker

A pre-built Docker image is available on Docker Hub:

```bash
docker pull yingyangtongxue/ismr-downloader:latest
```

This image contains a fully configured environment with Python, all dependencies, and the `ismr-downloader` CLI preinstalled.

---

### 1. Prepare a working directory on the host

Create a folder where downloads and logs will be stored, for example:

```text
D:\ismr_runner\
    downloads\
    logs\
```

You do **not** need to place any `.env` file there unless you want to.

---

### 2. Run the container with environment variables (recommended)

Pass your API credentials as environment variables. This avoids storing passwords inside the container:

```powershell
docker run --rm `
  -v D:\ismr_runner:/app `
  -e ISMR_EMAIL="your_email@example.com" `
  -e ISMR_PASSWORD="your_password" `
  yingyangtongxue/ismr-downloader:latest `
  --stations MOR3 `
  --start "2025-11-24T00:00:00" `
  --end   "2025-11-24T00:30:00" `
  --data-type ismr `
  --insecure
```

On Linux/macOS, the same command would look like:

```bash
docker run --rm -v /path/to/ismr_runner:/app -e ISMR_EMAIL="your_email@example.com" -e ISMR_PASSWORD="your_password" yingyangtongxue/ismr-downloader:latest --stations MOR3 --start "2025-11-24T00:00:00" --end "2025-11-24T00:30:00" --data-type ismr --insecure
```

**Where the files go:**

| Host path                 | Container path | Purpose                |
|---------------------------|----------------|------------------------|
| `…/ismr_runner/downloads` | `/app/downloads` | Downloaded data files |
| `…/ismr_runner/logs`      | `/app/logs`      | Logs and no-data CSVs |

---

### 3. Optional: using a `.env` file outside the repository

If you prefer to keep credentials in a `.env` file, you can mount it directly:

```powershell
docker run --rm `
  -v D:\ismr_secrets\.env:/app/.env `
  -v D:\ismr_runner:/app `
  yingyangtongxue/ismr-downloader:latest `
  --env .env `
  --insecure
```

In this setup:

- `D:\ismr_secrets\.env` stays only on your machine (never committed to Git).
- The container reads `/app/.env` just like the local CLI version.

---

# License

MIT License.

---

# Contributing

We welcome contributions.
⚠ Please follow [Conventional Commits](https://www.conventionalcommits.org/) ([cheatsheet](https://gist.github.com/qoomon/5dfcdf8eec66a051ecd85625518cfd13)).

---

# Support

Issues and feature requests:

https://github.com/GEGE-UNESP/ismr_downloader/issues