# Data Notes

Findings from the Phase 1 coverage report (`results/tables/data_coverage.csv`, built by `python -m irmf.data.build`). All rates are in percent as published.

## Par yield curve (`par-yield-curve-rates-1990-2023.csv`)

- 8,507 rows from 1990-01-02 to 2023-12-29.
- **2010-10-11 is an empty row** (Columbus Day; every tenor is blank). The loader keeps it so the raw file is reproduced exactly. Drop it when building any model panel.
- **3M is also missing on 2008-12-10, 2008-12-18, and 2008-12-24**, when bill yields were at or near zero. Treat these as missing, not as zero.
- Tenor start dates: 1M 2001-07-31, 2M 2018-10-16, 4M 2022-10-19, 20Y 1993-10-01. 3M through 10Y (excluding 4M) are complete apart from the dates above.
- **30Y suspension:** no values from 2002-02-19 to 2006-02-08 (the gap starts after 2002-02-15).

## Overnight reference rates (`overnight_rates.xlsx`)

- 2,549 EFFR/OBFR days (2016-03-01 to 2026-04-23) and 2,013 SOFR/TGCR/BGCR days (from 2018-04-02).
- **SOFR, TGCR, and BGCR are missing on 11 days when EFFR is published.** These are bond market closures that do not close the fed funds market: Good Fridays (2019 to 2026), 2018-12-05, 2020-07-03, and 2021-12-24. Repo rates are not set on those days. Do not forward-fill them into a daily repo series.
- The target range (`target_low`, `target_high`) is populated on EFFR rows only.

## Overlap

The two files overlap from 2016-03-01 to 2023-12-29. Any analysis that uses both the curve and the overnight rate is limited to that window.
