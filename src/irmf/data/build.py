"""Build the clean data panel from the raw files.

Usage::

    python -m irmf.data.build

Writes to ``data/processed/``:
- ``par_yields.csv``: daily par yields, one column per tenor (percent).
- ``overnight_long.csv``: overnight rates with percentiles, volume, target range.
- ``overnight_rates.csv``: overnight rates, one column per rate type (percent).

- ``zero_curve.csv``: continuously compounded zero yields (decimals), daily.
- ``zero_curve_monthly.csv``: the same, last available day of each month.

Writes to ``results/tables/``:
- ``data_coverage.csv``: coverage report for every series.
- ``bootstrap_reprice_check.csv``: par repricing error (bp) by tenor.
"""

from __future__ import annotations

import pandas as pd

from irmf.curves import reprice_errors_bp, zero_curve_panel
from irmf.data.loaders import load_overnight_rates, load_par_yields, overnight_wide
from irmf.data.panel import clean_par_panel, month_end
from irmf.data.quality import coverage_report
from irmf.paths import PROCESSED_DIR, TABLES_DIR


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    par = load_par_yields()
    on_long = load_overnight_rates()
    on_wide = overnight_wide(on_long)

    par.to_csv(PROCESSED_DIR / "par_yields.csv", date_format="%Y-%m-%d")
    on_long.to_csv(PROCESSED_DIR / "overnight_long.csv", index=False, date_format="%Y-%m-%d")
    on_wide.to_csv(PROCESSED_DIR / "overnight_rates.csv", date_format="%Y-%m-%d")

    coverage = pd.concat(
        {"par_yield": coverage_report(par), "overnight": coverage_report(on_wide)},
        names=["dataset", "series"],
    )
    coverage.to_csv(TABLES_DIR / "data_coverage.csv", date_format="%Y-%m-%d")

    par_dec = clean_par_panel(par)
    zeros = zero_curve_panel(par_dec)
    zeros.to_csv(PROCESSED_DIR / "zero_curve.csv", date_format="%Y-%m-%d")
    month_end(zeros).to_csv(PROCESSED_DIR / "zero_curve_monthly.csv", date_format="%Y-%m-%d")

    errs = reprice_errors_bp(par_dec)
    check = pd.DataFrame({
        "n_dates": errs.notna().sum(),
        "max_abs_error_bp": errs.abs().max(),
        "mean_abs_error_bp": errs.abs().mean(),
    })
    check.index.name = "tenor"
    check.to_csv(TABLES_DIR / "bootstrap_reprice_check.csv", float_format="%.2e")

    overlap_start = max(par.index[0], on_wide.index[0]).date()
    overlap_end = min(par.index[-1], on_wide.index[-1]).date()
    print(f"Par yields:     {len(par):>5} days, {par.index[0].date()} to {par.index[-1].date()}")
    print(f"Overnight:      {len(on_wide):>5} days, {on_wide.index[0].date()} to {on_wide.index[-1].date()}")
    print(f"Overlap:        {overlap_start} to {overlap_end}")
    print()
    with pd.option_context("display.width", 120):
        print(coverage.to_string())
        print()
        print(f"Zero curve:     {len(zeros):>5} days, {len(month_end(zeros))} month-ends")
        print("Bootstrap repricing error (bp):")
        print(check.to_string(float_format=lambda x: f"{x:.2e}"))


if __name__ == "__main__":
    main()
