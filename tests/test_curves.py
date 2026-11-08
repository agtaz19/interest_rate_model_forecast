"""Tests for the par-to-zero bootstrap and the model-ready panels."""

import numpy as np
import pandas as pd
import pytest

from irmf.curves import (
    bey_to_cc,
    bootstrap_discount_grid,
    cc_to_bey,
    par_from_discount_grid,
    reprice_errors_bp,
    zero_curve,
    zero_curve_panel,
)
from irmf.data import TENOR_YEARS, TENORS, clean_par_panel, load_par_yields, month_end

STANDARD = ["3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]


@pytest.fixture(scope="module")
def par_dec():
    return clean_par_panel(load_par_yields())


# ---- Conversions ---------------------------------------------------------

def test_bey_cc_round_trip():
    y = np.array([-0.001, 0.0, 0.0123, 0.05, 0.09])
    assert np.allclose(cc_to_bey(bey_to_cc(y)), y, atol=1e-15)


def test_bey_to_cc_known_value():
    assert bey_to_cc(0.05) == pytest.approx(2 * np.log(1.025))


# ---- Bootstrap on synthetic curves ---------------------------------------

def test_flat_par_curve_gives_flat_zero_curve():
    par = pd.Series(0.05, index=STANDARD)
    z = zero_curve(par)
    assert np.allclose(z.to_numpy(), 2 * np.log(1.025), atol=1e-12)


def test_flat_curve_discount_factors_exact():
    par = pd.Series(0.04, index=STANDARD)
    disc = bootstrap_discount_grid(par)
    expected = 1.02 ** (-np.arange(1, len(disc) + 1))
    assert np.allclose(disc.to_numpy(), expected, atol=1e-14)
    assert disc.index[-1] == 30.0


def test_nelson_siegel_round_trip():
    """Zero curve -> par yields at every grid point -> bootstrap recovers it."""
    grid = np.arange(0.5, 30.01, 0.5)
    lam = 0.6
    b1, b2, b3 = 0.05, -0.02, 0.01
    x = lam * grid
    z_true = b1 + b2 * (1 - np.exp(-x)) / x + b3 * ((1 - np.exp(-x)) / x - np.exp(-x))
    disc = pd.Series(np.exp(-z_true * grid), index=grid)

    # Feed the bootstrap only the standard tenors; interpolation error is the
    # only source of difference, so allow a few basis points at in-between points.
    tenors_long = [k for k in STANDARD if TENOR_YEARS[k] > 1]
    par_long = par_from_discount_grid(disc, [TENOR_YEARS[k] for k in tenors_long])
    par = pd.Series(
        {"6M": cc_to_bey(z_true[0]), "1Y": cc_to_bey(z_true[1]),
         **{k: par_long.iloc[i] for i, k in enumerate(tenors_long)}}
    )
    z_hat = zero_curve(par)
    for k in tenors_long:
        z_at = z_true[np.isclose(grid, TENOR_YEARS[k])][0]
        assert abs(z_hat[k] - z_at) * 1e4 < 1.0, k


def test_missing_30y_truncates_grid():
    par = pd.Series(0.03, index=STANDARD)
    par["30Y"] = np.nan
    disc = bootstrap_discount_grid(par)
    assert disc.index[-1] == 20.0
    assert np.isnan(zero_curve(par).get("30Y", np.nan))


def test_requires_6m_and_1y():
    par = pd.Series(0.03, index=["2Y", "5Y", "10Y"])
    with pytest.raises(ValueError):
        bootstrap_discount_grid(par)


# ---- Real data -----------------------------------------------------------

def test_clean_panel_drops_empty_row_and_scales(par_dec):
    assert len(par_dec) == 8506
    assert pd.Timestamp("2010-10-11") not in par_dec.index
    assert par_dec.loc["1990-01-02", "10Y"] == pytest.approx(0.0794)


def test_reprices_par_curve_within_tenth_bp(par_dec):
    sample = par_dec.iloc[::50]  # every 50th day across 1990-2023
    errs = reprice_errors_bp(sample)
    assert errs.abs().max().max() < 0.1


def test_zero_curve_panel_shape_and_sanity(par_dec):
    sample = par_dec.loc["2023-12-01":"2023-12-29"]
    zeros = zero_curve_panel(sample)
    assert list(zeros.columns) == TENORS
    assert zeros.index.equals(sample.index)
    # Short tenors: direct BEY -> CC conversion.
    assert np.allclose(zeros["3M"], bey_to_cc(sample["3M"]))
    # Zero yields stay close to par yields (within 50 bp) on a normal curve.
    assert (zeros["10Y"] - sample["10Y"]).abs().max() < 0.005


def test_month_end_selects_last_trading_day(par_dec):
    me = month_end(par_dec)
    assert me.index[-1] == pd.Timestamp("2023-12-29")
    assert pd.Timestamp("2023-11-30") in me.index
    assert len(me) == 34 * 12
    assert me.index.to_period("M").is_unique
