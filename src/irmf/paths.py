"""Project directory layout.

The project root is the directory that contains ``pyproject.toml``. Set the
``IRMF_ROOT`` environment variable to override it (for example, when running
from an installed copy outside the repository).
"""

from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    env = os.environ.get("IRMF_ROOT")
    if env:
        return Path(env).resolve()
    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists():
            return parent
    raise FileNotFoundError("Could not locate project root; set IRMF_ROOT.")


ROOT = project_root()
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"
TABLES_DIR = ROOT / "results" / "tables"
FIGURES_DIR = ROOT / "results" / "figures"

PAR_YIELDS_FILE = RAW_DIR / "par-yield-curve-rates-1990-2023.csv"
OVERNIGHT_FILE = RAW_DIR / "overnight_rates.xlsx"
