# Slay the Spire 2 — Data Summary

A GUI tool that processes your Slay the Spire 2 run history and generates CSV reports on run statistics and card pick rates.

## Usage

### Download

Grab the latest release for your platform from the [Releases](../../releases) page:
- **Windows**: `SpireDataSummary.exe`
- **Linux**: `SpireDataSummary`

No Python installation required.

### Running

1. Launch the executable.
2. **Data Directory** — Select your SlayTheSpire2 data folder. It will auto-detect the default location:
   - Linux: `~/.local/share/SlayTheSpire2`
   - Windows: `%APPDATA%/SlayTheSpire2`
3. **Steam ID** — Enter your Steam ID, or leave blank to auto-detect (uses the first ID found in the data directory).
4. **Output Directory** — Choose where to save the CSV files.
5. Click **Run Processing**.

Two files will be generated:
- `run_history.csv` — Per-run stats: character, ascension, damage taken, bosses fought, etc.
- `card_choices.csv` — Card offering and pick rates across all runs.

### Uploading to Google Sheets

For an easier way to view the files and some preliminary analytics, use the following steps:

 - Open [this google sheet](https://docs.google.com/spreadsheets/d/1eAFP3YOF5N8CT2cKSrRMdJBH7yY9KqU2JWtMKaD-org/edit?gid=154445968#gid=154445968)
 - File >> Make a Copy
 - On your copied sheet:
   - On the "run_history" sheet:
     - File >> Import >> Upload
     - Select the "run_history.csv" file that was generated
     - Use the following settings:
       - Import location: "Replace current sheet"
       - Separator type: "Detect automatically" (or "Comma")
       - Ensure "Convert text to numbers, dates and formulas" is selected
   - On the "card_choices" sheet:
     - File >> Import >> Upload
     - Select the "card_choices.csv" file that was generated
     - Use the following settings:
       - Import location: "Replace current sheet"
       - Separator type: "Detect automatically" (or "Comma")
       - Ensure "Convert text to numbers, dates and formulas" is selected 
   - On the "analytics" sheet:
     - This should update automatically once you have uploaded the other two .csv files

## Running from source

### Clone the repo

```bash
git clone git@github.com:philhteoma/spire_data_summariser.git
cd spire_data_summariser
```

### (Optional) Set up .venv

Linux:
```bash
python -m venv .venv
source .venv/bin/activate
```

Windows Powershell:
```bash
python -m venv .venv
.venv\scripts\activate.ps1
```

### Install requirements

```bash
pip install -r requirements.txt
python gui.py
```

## Building

### Prerequisites

- Python 3.10+
- pip

### Local build

```bash
pip install -r requirements.txt
pip install pyinstaller
pyinstaller spire_gui.spec
```

The executable will be in `dist/SpireDataSummary`.

## AI Disclaimer

Generative AI was used for the following purposes in this project:
 - Generating the GUI and build system
 - Generating the github workflow build.yml to allow for releases
 - Explaining the above two concepts and their implementation to a novice in these matters
 - Generating the base README.md
