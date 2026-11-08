# Data Notes

Findings from the Phase 1 coverage report (`results/tables/data_coverage.csv`, built by `python -m irmf.data.build`). All rates are in percent as published.

## Par yield curve (`par-yield-curve-rates-1990-2023.csv`)

- 8,507 rows from 1990-01-02 to 2023-12-29.
- **2010-10-11 is an empty row** (Columbus Day; every tenor is blank). The loader keeps it so the raw file is reproduced exactly. Drop it when building any model panel.
- **3M is also missing on 2008-12-10, 2008-12-18, and 2008-12-24**, when bill yields were at or near zero. Treat these as missing, not as zero.
- Tenor start dates: 1M 2001-07-31, 2M 2018-10-16, 4M 2022-10-19, 20Y 1993-10-01. 3M through 10Y (excluding 4M) are complete apart from the dates above.
- **30Y suspension:** no values from 2002-02-19 to 2006-02-08 (the gap starts after 2002-02-15).

## Zero curve (`irmf.curves`)

Conventions: par yields are semiannual bond-equivalent (BEY); zero yields are continuously compounded decimals, $z = 2\ln(1 + y_{\text{BEY}}/2)$. Tenors of 1 year or less are treated as zero-coupon. Longer tenors are interpolated onto a semiannual grid with a monotone cubic (PCHIP) spline and bootstrapped from the par condition.

- **Repricing check** (`results/tables/bootstrap_reprice_check.csv`): the zero curve reprices every input par yield above 1 year to within $10^{-12}$ bp. This only confirms the code is internally consistent, because the bootstrap fits the input tenors exactly by construction.
- **Accuracy check** (`tests/test_curves.py`): par yields generated from known Nelson-Siegel zero curves are bootstrapped back to the true zero yields within 0.27 bp at the standard tenors. The residual is interpolation error between the standard tenors.
- **Negative long-end forwards:** on 134 of 8,506 days, the 6-month forward rate between 29.5 and 30 years falls below -0.10%. All such cases lie beyond 28 years and occur when the 20Y par yield sits well above the 30Y (24 bp at minimum, 34 bp median) (for example, 2009-01-12: 20Y 3.30%, 30Y 2.99%). This reflects the relative illiquidity of the 20-year bond, not a bootstrap error. Zero yields at the standard tenors are unaffected. Do not use forward rates beyond 20 years in the forward-implied benchmark.

## Overnight reference rates (`overnight_rates.xlsx`)

- 2,549 EFFR/OBFR days (2016-03-01 to 2026-04-23) and 2,013 SOFR/TGCR/BGCR days (from 2018-04-02).
- **SOFR, TGCR, and BGCR are missing on 11 days when EFFR is published.** These are bond market closures that do not close the fed funds market: Good Fridays (2019 to 2026), 2018-12-05, 2020-07-03, and 2021-12-24. Repo rates are not set on those days. Do not forward-fill them into a daily repo series.
- The target range (`target_low`, `target_high`) is populated on EFFR rows only.

## Overlap

The two files overlap from 2016-03-01 to 2023-12-29. Any analysis that uses both the curve and the overnight rate is limited to that window.
