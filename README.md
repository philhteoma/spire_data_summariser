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
   - Windows: `%APPDATA%/../LocalLow/MegaCrit/SlayTheSpire2`
3. **Steam ID** — Enter your Steam ID, or leave blank to auto-detect (uses the first ID found in the data directory).
4. **Output Directory** — Choose where to save the CSV files.
5. Click **Run Processing**.

Two files will be generated:
- `run_history.csv` — Per-run stats: character, ascension, damage taken, bosses fought, etc.
- `card_choices.csv` — Card offering and pick rates across all runs.

### Running from source

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

### CI/CD

The GitHub Actions workflow (`.github/workflows/build.yml`) builds for both Windows and Linux automatically. It triggers on:
- Pushing a tag matching `v*` (e.g. `v1.0.0`)
- Manual dispatch from the Actions tab

To create a release:

```bash
git tag v1.0.0
git push origin v1.0.0
```

Built executables are attached to the GitHub release automatically.
