"""Tests for the raw-data loaders and the coverage report.

The expected counts and dates below are the ones stated in the README.
"""

import numpy as np
import pandas as pd
import pytest

from irmf.data import (
    OVERNIGHT_RATE_TYPES,
    TENOR_YEARS,
    TENORS,
    coverage_report,
    load_overnight_rates,
    load_par_yields,
    overnight_wide,
)


@pytest.fixture(scope="module")
def par():
    return load_par_yields()


@pytest.fixture(scope="module")
def on_long():
    return load_overnight_rates()


# ---- Par yields ----------------------------------------------------------

def test_par_shape_and_range(par):
    assert len(par) == 8507
    assert list(par.columns) == TENORS
    assert par.index[0] == pd.Timestamp("1990-01-02")
    assert par.index[-1] == pd.Timestamp("2023-12-29")
    assert par.index.is_monotonic_increasing and par.index.is_unique


@pytest.mark.parametrize(
    "tenor, first",
    [("1M", "2001-07-31"), ("2M", "2018-10-16"), ("4M", "2022-10-19"),
     ("20Y", "1993-10-01"), ("3M", "1990-01-02"), ("10Y", "1990-01-02")],
)
def test_par_tenor_start_dates(par, tenor, first):
    assert par[tenor].first_valid_index() == pd.Timestamp(first)


def test_par_30y_suspension_gap(par):
    s = par.loc["2002-03-01":"2005-12-31", "30Y"]
    assert s.isna().all()


def test_par_values_in_plausible_range(par):
    vals = par.to_numpy()
    vals = vals[~np.isnan(vals)]
    assert vals.min() >= -0.5 and vals.max() <= 10.0


def test_core_panel_nearly_complete(par):
    core = par.loc[:, "3M":"10Y"].drop(columns=["4M"])
    assert core.isna().sum().max() <= 4


def test_tenor_years_cover_all_tenors():
    assert set(TENOR_YEARS) == set(TENORS)
    years = [TENOR_YEARS[t] for t in TENORS]
    assert years == sorted(years)


# ---- Overnight rates -----------------------------------------------------

@pytest.mark.parametrize(
    "rate_type, first, n",
    [("EFFR", "2016-03-01", 2549), ("OBFR", "2016-03-01", 2549),
     ("SOFR", "2018-04-02", 2013), ("TGCR", "2018-04-02", 2013),
     ("BGCR", "2018-04-02", 2013)],
)
def test_overnight_counts(on_long, rate_type, first, n):
    sub = on_long[on_long["rate_type"] == rate_type]
    assert len(sub) == n
    assert sub["date"].min() == pd.Timestamp(first)
    assert sub["date"].max() == pd.Timestamp("2026-04-23")


def test_overnight_long_sorted_unique(on_long):
    assert on_long["date"].is_monotonic_increasing
    assert not on_long.duplicated(["date", "rate_type"]).any()


def test_target_range_only_on_effr(on_long):
    effr = on_long["rate_type"] == "EFFR"
    assert on_long.loc[effr, "target_low"].notna().all()
    assert on_long.loc[~effr, "target_low"].isna().all()
    assert (on_long.loc[effr, "target_high"] > on_long.loc[effr, "target_low"]).all()


def test_overnight_wide(on_long):
    wide = overnight_wide(on_long)
    assert list(wide.columns) == OVERNIGHT_RATE_TYPES
    assert len(wide) == 2549
    assert wide.loc["2026-04-23", "EFFR"] == pytest.approx(3.64)
    assert wide.loc[:"2018-03-29", "SOFR"].isna().all()


# ---- Coverage report -----------------------------------------------------

def test_coverage_report_toy():
    idx = pd.to_datetime(["2020-01-01", "2020-01-02", "2020-01-03", "2020-01-10", "2020-01-11"])
    df = pd.DataFrame({"a": [np.nan, 1.0, np.nan, 2.0, 3.0], "b": [np.nan] * 5}, index=idx)
    rep = coverage_report(df)
    a = rep.loc["a"]
    assert a["first"] == pd.Timestamp("2020-01-02")
    assert a["last"] == pd.Timestamp("2020-01-11")
    assert a["n_obs"] == 3
    assert a["n_missing_inside"] == 1
    assert a["max_gap_days"] == 8
    assert a["max_gap_start"] == pd.Timestamp("2020-01-02")
    assert rep.loc["b", "n_obs"] == 0
