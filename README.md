# ISMR Downloader

A Python tool for downloading ISMR (Ionospheric Scintillation Monitoring Receiver) data from the ISMR Query Tool API.  
It handles automatic token management, rate limiting, logging, and progress bars.

---

# Requirements

- [Python](https://www.python.org/downloads/) version **3.10** or above  
- [pip](https://pip.pypa.io/en/stable/installation/)  
- [virtualenv](https://virtualenv.pypa.io/en/latest/) (recommended)

⚠ Recommended to use [conventional commits](https://www.conventionalcommits.org/) ([summary](https://gist.github.com/qoomon/5dfcdf8eec66a051ecd85625518cfd13))

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

# Logs

- All run logs will be saved under the `logs/` folder with a timestamp:  
  - `run_YYYYMMDD_HHMMSS.log` → detailed logs  
  - `downloaded_files_YYYYMMDD_HHMMSS.txt` → list of downloaded files

---

# Notes

- Default download folder is `downloads/`.  
- Maximum allowed request interval is **2 months** (handled automatically).  
- Progress bars are displayed during file downloads.  
