import sys
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """Resolve path to bundled resource, handling PyInstaller's temp directory."""
    if hasattr(sys, '_MEIPASS'):
        return Path(sys._MEIPASS) / relative_path
    return Path(__file__).parent.parent / relative_path
