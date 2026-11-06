"""Data coverage and quality checks."""

from __future__ import annotations

import pandas as pd


def coverage_report(df: pd.DataFrame) -> pd.DataFrame:
    """Per-column coverage of a date-indexed frame.

    Columns of the result:
    - ``first``, ``last``: first and last dates with a value.
    - ``n_obs``: number of non-missing values.
    - ``n_missing_inside``: rows between ``first`` and ``last`` with no value
      (gaps inside the series, as opposed to before it starts).
    - ``max_gap_days``: longest calendar-day gap between consecutive values.
    - ``max_gap_start``: date of the last value before that gap.
    """
    rows = {}
    for col in df.columns:
        s = df[col].dropna()
        if s.empty:
            rows[col] = dict(first=pd.NaT, last=pd.NaT, n_obs=0, n_missing_inside=0,
                             max_gap_days=0, max_gap_start=pd.NaT)
            continue
        inside = df.loc[s.index[0]: s.index[-1], col]
        gaps = s.index.to_series().diff().dt.days
        rows[col] = dict(
            first=s.index[0],
            last=s.index[-1],
            n_obs=int(s.size),
            n_missing_inside=int(inside.isna().sum()),
            max_gap_days=int(gaps.max()) if s.size > 1 else 0,
            max_gap_start=gaps.shift(-1).idxmax() if s.size > 1 else pd.NaT,
        )
    out = pd.DataFrame.from_dict(rows, orient="index")
    out.index.name = "series"
    return out
