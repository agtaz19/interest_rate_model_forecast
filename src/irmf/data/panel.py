"""Model-ready panels built from the raw loaders."""

from __future__ import annotations

import pandas as pd


def clean_par_panel(par_pct: pd.DataFrame) -> pd.DataFrame:
    """Par yields in decimals with empty rows removed.

    Drops dates where every tenor is missing (for example, 2010-10-11) and
    converts percent to decimals. Individual missing tenors stay NaN.
    """
    return par_pct.dropna(how="all") / 100.0


def month_end(df: pd.DataFrame) -> pd.DataFrame:
    """Last available observation date in each calendar month.

    Selects whole rows (the last date present in the frame for each month),
    so every column in a row comes from the same date.
    """
    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("month_end requires a DatetimeIndex")
    return df.groupby(df.index.to_period("M")).tail(1)
