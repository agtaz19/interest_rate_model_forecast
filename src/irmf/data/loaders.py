"""Loaders for the raw data files.

Units: all rates are returned in percent, exactly as published. Conversion to
decimals and to continuous compounding happens in ``irmf.curves``.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from irmf.paths import OVERNIGHT_FILE, PAR_YIELDS_FILE

# Treasury column label -> standard tenor label.
_TREASURY_TENORS = {
    "1 mo": "1M",
    "2 mo": "2M",
    "3 mo": "3M",
    "4 mo": "4M",
    "6 mo": "6M",
    "1 yr": "1Y",
    "2 yr": "2Y",
    "3 yr": "3Y",
    "5 yr": "5Y",
    "7 yr": "7Y",
    "10 yr": "10Y",
    "20 yr": "20Y",
    "30 yr": "30Y",
}

TENORS: list[str] = list(_TREASURY_TENORS.values())

# Tenor in years (months / 12).
TENOR_YEARS: dict[str, float] = {
    "1M": 1 / 12,
    "2M": 2 / 12,
    "3M": 3 / 12,
    "4M": 4 / 12,
    "6M": 6 / 12,
    "1Y": 1.0,
    "2Y": 2.0,
    "3Y": 3.0,
    "5Y": 5.0,
    "7Y": 7.0,
    "10Y": 10.0,
    "20Y": 20.0,
    "30Y": 30.0,
}

OVERNIGHT_RATE_TYPES: list[str] = ["EFFR", "OBFR", "SOFR", "TGCR", "BGCR"]

# NY Fed column label -> snake_case name.
_OVERNIGHT_COLUMNS = {
    "Effective Date": "date",
    "Rate Type": "rate_type",
    "Rate (%)": "rate",
    "1st Percentile (%)": "p01",
    "25th Percentile (%)": "p25",
    "75th Percentile (%)": "p75",
    "99th Percentile (%)": "p99",
    "Volume ($Billions)": "volume_bn",
    "Target Rate From (%)": "target_low",
    "Target Rate To (%)": "target_high",
}


def load_par_yields(path: str | Path = PAR_YIELDS_FILE) -> pd.DataFrame:
    """Daily Treasury par yield curve (CMT), in percent.

    Returns a DataFrame indexed by a sorted, unique ``DatetimeIndex`` named
    ``date`` with columns in ``TENORS`` order. Tenors not yet published on a
    date are NaN.
    """
    df = pd.read_csv(path, encoding="utf-8-sig")
    df.columns = [c.strip() for c in df.columns]
    date_col = df.columns[0]
    if date_col.lower() != "date":
        raise ValueError(f"Expected first column 'date', found {date_col!r}")

    df = df.rename(columns={date_col: "date", **_TREASURY_TENORS})
    unknown = set(df.columns) - {"date", *TENORS}
    if unknown:
        raise ValueError(f"Unrecognized tenor columns: {sorted(unknown)}")

    df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y")
    df = df.set_index("date").sort_index()
    if df.index.has_duplicates:
        raise ValueError("Duplicate dates in par yield file")

    return df.reindex(columns=TENORS).astype(float)


def load_overnight_rates(path: str | Path = OVERNIGHT_FILE) -> pd.DataFrame:
    """NY Fed overnight reference rates in long (tidy) format, in percent.

    One row per (date, rate_type), sorted by date then rate type. Columns:
    ``date, rate_type, rate, p01, p25, p75, p99, volume_bn, target_low,
    target_high``. The target range is populated on EFFR rows only.
    """
    raw = pd.read_excel(path, sheet_name="Results")
    missing = set(_OVERNIGHT_COLUMNS) - set(raw.columns)
    if missing:
        raise ValueError(f"Missing columns in overnight file: {sorted(missing)}")

    df = raw[list(_OVERNIGHT_COLUMNS)].rename(columns=_OVERNIGHT_COLUMNS)
    df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y")
    df["rate_type"] = df["rate_type"].astype(str).str.strip()

    unknown = set(df["rate_type"]) - set(OVERNIGHT_RATE_TYPES)
    if unknown:
        raise ValueError(f"Unrecognized rate types: {sorted(unknown)}")
    if df.duplicated(["date", "rate_type"]).any():
        raise ValueError("Duplicate (date, rate_type) rows in overnight file")

    num_cols = [c for c in df.columns if c not in ("date", "rate_type")]
    df[num_cols] = df[num_cols].astype(float)
    return df.sort_values(["date", "rate_type"]).reset_index(drop=True)


def overnight_wide(long: pd.DataFrame, value: str = "rate") -> pd.DataFrame:
    """Pivot the long overnight frame to one column per rate type."""
    wide = long.pivot(index="date", columns="rate_type", values=value)
    wide.columns.name = None
    cols = [c for c in OVERNIGHT_RATE_TYPES if c in wide.columns]
    return wide[cols].sort_index()
