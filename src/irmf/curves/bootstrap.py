r"""Par-to-zero bootstrap for the Treasury par yield curve.

Conventions (see README, Methodology):

* Input par yields are decimals, quoted on a semiannual bond-equivalent basis
  (BEY).
* Output zero yields are continuously compounded decimals:
  :math:`z = 2 \ln(1 + y_{BEY}/2)`.
* Tenors of 1 year or less are bill yields and are treated as zero-coupon.
* Above 1 year, the par curve is interpolated onto a semiannual grid with a
  monotone cubic (PCHIP) spline, and discount factors are bootstrapped from
  the semiannual-coupon par condition

  .. math::  1 = \frac{c_n}{2}\sum_{i=1}^{n} D(t_i) + D(t_n),
             \qquad t_i = i/2.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.interpolate import PchipInterpolator

from irmf.data.loaders import TENOR_YEARS

GRID_STEP = 0.5  # semiannual coupon dates, in years
ZERO_COUPON_MAX = 1.0  # tenors at or below this are treated as zero-coupon


def bey_to_cc(y: np.ndarray | float) -> np.ndarray | float:
    """Semiannual bond-equivalent yield to continuous compounding."""
    return 2.0 * np.log1p(np.asarray(y) / 2.0)


def cc_to_bey(z: np.ndarray | float) -> np.ndarray | float:
    """Continuous compounding to semiannual bond-equivalent yield."""
    return 2.0 * np.expm1(np.asarray(z) / 2.0)


def bootstrap_discount_grid(par: pd.Series) -> pd.Series:
    """Bootstrap discount factors on the semiannual grid for one date.

    Parameters
    ----------
    par
        Par yields (decimals) for one date, indexed by tenor label
        (``"3M"``, ``"2Y"``, ...). NaN tenors are ignored.

    Returns
    -------
    pd.Series
        Discount factors indexed by grid time in years (0.5, 1.0, ...,
        longest available tenor).
    """
    par = par.dropna()
    t_knots = np.array([TENOR_YEARS[k] for k in par.index])
    c_knots = par.to_numpy(dtype=float)
    order = np.argsort(t_knots)
    t_knots, c_knots = t_knots[order], c_knots[order]

    if not np.any(np.isclose(t_knots, 0.5)) or not np.any(np.isclose(t_knots, 1.0)):
        raise ValueError("6M and 1Y par yields are required to start the bootstrap")

    t_max = t_knots[-1]
    grid = np.arange(GRID_STEP, t_max + 1e-9, GRID_STEP)
    disc = np.empty_like(grid)

    # Grid points at or below 1 year come straight from bill (zero-coupon) yields.
    short = grid <= ZERO_COUPON_MAX + 1e-9
    for i in np.flatnonzero(short):
        z = bey_to_cc(c_knots[np.isclose(t_knots, grid[i])][0])
        disc[i] = np.exp(-z * grid[i])

    # Longer grid points: interpolate par yields, then bootstrap sequentially.
    mask = t_knots >= GRID_STEP - 1e-9
    spline = PchipInterpolator(t_knots[mask], c_knots[mask], extrapolate=False)
    annuity = disc[short].sum()
    for i in np.flatnonzero(~short):
        half_c = spline(grid[i]) / 2.0
        disc[i] = (1.0 - half_c * annuity) / (1.0 + half_c)
        annuity += disc[i]

    return pd.Series(disc, index=pd.Index(grid, name="t"), name=par.name)


def zero_curve(par: pd.Series) -> pd.Series:
    """Continuously compounded zero yields at the input tenors for one date.

    Tenors at or below 1 year are converted directly from BEY; longer tenors
    are read from the bootstrapped semiannual grid.
    """
    par = par.dropna()
    out = {}
    disc = None
    for tenor, y in par.items():
        t = TENOR_YEARS[tenor]
        if t <= ZERO_COUPON_MAX + 1e-9:
            out[tenor] = float(bey_to_cc(y))
        else:
            if disc is None:
                disc = bootstrap_discount_grid(par)
            d = disc.iloc[int(round(t / GRID_STEP)) - 1]
            out[tenor] = float(-np.log(d) / t)
    return pd.Series(out, name=par.name)


def zero_curve_panel(par: pd.DataFrame) -> pd.DataFrame:
    """Apply :func:`zero_curve` to every date of a par yield panel (decimals)."""
    rows = {date: zero_curve(row) for date, row in par.iterrows()}
    out = pd.DataFrame.from_dict(rows, orient="index").reindex(columns=par.columns)
    out.index.name = par.index.name
    return out


def par_from_discount_grid(disc: pd.Series, tenors: list[float]) -> pd.Series:
    r"""Semiannual-coupon par yields implied by a discount grid.

    :math:`c(T) = 2\,(1 - D(T)) / \sum_{t_i \le T} D(t_i)`. Used to verify
    that the bootstrap reprices the input par curve.
    """
    cum = disc.cumsum()
    out = {}
    for T in tenors:
        n = int(round(T / GRID_STEP))
        out[T] = 2.0 * (1.0 - disc.iloc[n - 1]) / cum.iloc[n - 1]
    return pd.Series(out)


def reprice_errors_bp(par: pd.DataFrame) -> pd.DataFrame:
    """Repricing error (bp) at input tenors above 1 year, for every date.

    Error = par yield implied by the bootstrapped curve minus the input par
    yield. Tenors at or below 1 year are excluded because they are treated as
    zero-coupon by construction.
    """
    long_tenors = [k for k in par.columns if TENOR_YEARS[k] > ZERO_COUPON_MAX]
    rows = {}
    for date, row in par.iterrows():
        row = row.dropna()
        disc = bootstrap_discount_grid(row)
        avail = [k for k in long_tenors if k in row.index]
        implied = par_from_discount_grid(disc, [TENOR_YEARS[k] for k in avail])
        rows[date] = {k: (implied.iloc[j] - row[k]) * 1e4 for j, k in enumerate(avail)}
    out = pd.DataFrame.from_dict(rows, orient="index").reindex(columns=long_tenors)
    out.index.name = par.index.name
    return out
