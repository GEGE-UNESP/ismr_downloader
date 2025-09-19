# ISMR Downloader

A Python tool for downloading GNSS/ISMR (Ionospheric Scintillation Monitoring Receiver) data from the **ISMR Query Tool API**.
It supports multiple data types, automatic token management, rate limiting, logging, and progress bars.

---

## Requirements

- [Python](https://www.python.org/downloads/) **3.10+**
- [pip](https://pip.pypa.io/en/stable/installation/)
- [virtualenv](https://virtualenv.pypa.io/en/latest/) *(recommended)*

⚠ We recommend following [Conventional Commits](https://www.conventionalcommits.org/)
([cheatsheet](https://gist.github.com/qoomon/5dfcdf8eec66a051ecd85625518cfd13)) for contributions.

---

# Getting started

- Clone the repository
```bash
git clone git@github.com:GEGE-UNESP/ismr_downloader.git
```

- Create a virtual environment

*Windows (PowerShell)*
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

*Linux/Mac*
```bash
python3 -m venv .venv
source .venv/bin/activate
```

- Create a `.env` file

*Windows*
```powershell
type .env.example > .env
```

*Linux/Mac*
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
ISMR_START=2015-01-01
ISMR_END=2015-07-30
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
⚠ Make sure your `.exe` file has the same structure as the example.

# Logs

- All run logs will be saved under the `logs/` folder with a timestamp:
  - `run_YYYYMMDD_HHMMSS.log` → detailed logs
  - `downloaded_files_YYYYMMDD_HHMMSS.txt` → list of downloaded files

---

# Notes

- Default download folder is `downloads/`.
- Maximum allowed request interval is **2 months** (handled automatically).
- Progress bars are displayed during file downloads.