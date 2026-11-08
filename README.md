# Interest Rate Model Forecast Comparison

![Status](https://img.shields.io/badge/status-prototype-yellow) ![License](https://img.shields.io/badge/license-MIT-blue)

## Project Description

This project measures how well standard interest rate models forecast future U.S. rates. Using daily Treasury par yields (1990 to 2023) and New York Fed overnight reference rates (2016 to 2026), it runs a walk-forward comparison of short-rate, yield-curve factor, and regime-switching models against simple benchmarks. Each model is scored on the forecast level, the forecast change ($\Delta y$), and the quality of its forecast distribution, across tenors, horizons, and rate regimes.

## Table of Contents

- [Project Description](#project-description)
- [Objectives](#objectives)
- [Status & Roadmap](#status--roadmap)
- [Methodology & Workflow](#methodology--workflow)
- [Results & Visuals](#results--visuals)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Authors & Acknowledgements](#authors--acknowledgements)
- [References](#references)
- [License](#license)

## Objectives

1. Determine which models beat the random walk out of sample when forecasting yields at tenors from overnight to 30 years and horizons from 1 day to 12 months.
2. Quantify forecast error in basis points and the accuracy of predicted rate changes, including direction.
3. Evaluate whether each model's forecast distribution is calibrated (interval coverage, PIT, CRPS), not only its point forecast.
4. Identify how model rankings change across rate regimes: pre-2008, the zero lower bound, and the 2022 to 2023 hiking cycle, plus the 2024 to 2026 easing period for the overnight rate.

## Status & Roadmap

**Current Version:** v0.1.0
**Stage:** Prototype
**Last Updated:** November 2026

### Roadmap

- **Phase 1, Data & Curves:** Load and clean both datasets, bootstrap par yields to zero-coupon yields, and publish a data coverage report.
- **Phase 2, Benchmarks & Harness:** Build the walk-forward forecasting harness and the random walk, historical mean, AR(1), and forward-implied benchmarks.
- **Phase 3, Short-Rate Models:** Estimate Vasicek, CIR, and CKLS by maximum likelihood and generate point and density forecasts.
- **Phase 4, Factor & Regime Models:** Implement Diebold-Li dynamic Nelson-Siegel, PCA-VAR, VAR/VECM on yields, and a two-state Markov regime-switching model.
- **Phase 5, Evaluation & Write-up:** Produce the forecast accuracy tables, statistical tests, regime breakdowns, and the final report.

**Future work:**

- Extend the par yield curve from 2024 through 2026 using Treasury's published daily files. This aligns the curve with the overnight data and adds the 2024 to 2026 easing period as an out-of-sample test for the curve models.
- Add arbitrage-free Nelson-Siegel (Kalman filter) and Gaussian affine term structure models (Joslin-Singleton-Zhu).
- Add regularized and tree-based machine learning models.

## Methodology & Workflow

### Data

| Dataset | Source | Coverage | Notes |
|---|---|---|---|
| Daily par yield curve (CMT), `par-yield-curve-rates-1990-2023.csv` | U.S. Treasury | 1990-01-02 to 2023-12-29 (8,507 days) | 1-month from 2001-07-31, 2-month from 2018-10-16, 4-month from 2022-10-19, 20-year from 1993-10-01; 30-year absent from 2002-02-19 to early 2006. |
| Overnight reference rates, `overnight_rates.xlsx` | Federal Reserve Bank of New York | 2016-03-01 to 2026-04-23 | EFFR and OBFR from 2016-03-01; SOFR, TGCR, BGCR from 2018-04-02. Long format, one row per date and rate type. Includes percentiles, volume, and target range. |

The two files overlap from 2016-03-01 to 2023-12-29. Joint analyses of the curve and the overnight rate are limited to that window.

Data handling rules:

- The core curve panel uses the 3-month through 10-year tenors, which are complete for the full sample. The 1-month, 20-year, and 30-year tenors are evaluated on their available sub-samples.
- Par yields are bootstrapped to continuously compounded zero yields before any short-rate or factor model is fitted. Par yields are treated as semiannual bond-equivalent yields, converted by $z = 2\ln(1 + y_{\text{BEY}}/2)$. Tenors of 1 year or less are treated as zero-coupon; longer tenors are interpolated onto a semiannual grid with a monotone cubic spline and bootstrapped from the par bond condition $1 = \tfrac{c}{2}\sum_{i} D(t_i) + D(T)$.
- Forecasts at horizons of 1 month and longer use the last available trading day of each month.
- Details of data gaps, holidays, and bootstrap checks are in [docs/Data_notes.md](docs/Data_notes.md).
- The 3-month yield is the short-rate proxy for 1990 to 2023; EFFR and TGCR are used for 2016 to 2026. SOFR is reported but not used as the primary short rate because of month-end and quarter-end spikes (for example, September 2019).
- Every forecast uses only information available at the prior close.

### Models

| Group | Model | Specification |
|---|---|---|
| Benchmark | Random walk | $\hat{y}_{t+h} = y_t$ |
| Benchmark | Historical mean, AR(1) | Fitted per tenor on the estimation window |
| Benchmark | Forward-implied | Forecast equals the forward rate implied by today's curve (expectations hypothesis) |
| Short-rate | Vasicek | $dr_t = \kappa(\theta - r_t)\,dt + \sigma\,dW_t$ |
| Short-rate | CIR | $dr_t = \kappa(\theta - r_t)\,dt + \sigma\sqrt{r_t}\,dW_t$ |
| Short-rate | CKLS | $dr_t = (\alpha + \beta r_t)\,dt + \sigma r_t^{\gamma}\,dW_t$ |
| Curve factor | Diebold-Li dynamic Nelson-Siegel | $y_t(\tau) = \beta_{1t} + \beta_{2t}\frac{1-e^{-\lambda\tau}}{\lambda\tau} + \beta_{3t}\left(\frac{1-e^{-\lambda\tau}}{\lambda\tau} - e^{-\lambda\tau}\right)$, factors follow AR(1)/VAR(1) |
| Curve factor | PCA-VAR | Level, slope, and curvature principal components with a VAR on the scores |
| Econometric | VAR / VECM | Fitted directly to the yield panel |
| Econometric | Markov regime-switching | Two-state AR with regime-dependent mean and volatility |

Short-rate models are estimated under the real-world measure $\mathbb{P}$ by maximum likelihood, using their closed-form or approximate transition densities. Hull-White and HJM are excluded as forecasters: they are calibrated under $\mathbb{Q}$ to fit today's curve exactly, so their forecast reduces to the forward-implied benchmark.

### Evaluation

Forecasts are produced for tenors $\tau \in \{\text{ON}, 3\text{m}, 6\text{m}, 1\text{y}, 2\text{y}, 5\text{y}, 10\text{y}, 30\text{y}\}$ and horizons $h \in \{1\text{d}, 1\text{w}, 1\text{m}, 3\text{m}, 6\text{m}, 12\text{m}\}$. The forecast error and the predicted change are

$$e_{t+h}(\tau) = y_{t+h}(\tau) - \hat{y}_{t+h|t}(\tau), \qquad \Delta\hat{y}_{t+h|t}(\tau) = \hat{y}_{t+h|t}(\tau) - y_t(\tau).$$

| Dimension | Metric |
|---|---|
| Point accuracy | RMSE and MAE in basis points |
| Relative to random walk | $R^2_{OOS} = 1 - \dfrac{\sum e^2_{\text{model}}}{\sum e^2_{\text{RW}}}$ |
| Direction of change | Hit rate on $\operatorname{sign}(\Delta y)$; Pesaran-Timmermann test |
| Pairwise significance | Diebold-Mariano test with Newey-West standard errors for overlapping horizons |
| Set of best models | Model Confidence Set |
| Distribution quality | 90% interval coverage, PIT histograms, CRPS, log score |
| Regime stability | All metrics split by pre-2008, 2009 to 2015, 2016 to 2019, 2020 to 2021, 2022 to 2023; overnight models also 2024 to 2026 |

### Workflow

1. Build the clean daily panel of par yields and overnight rates, then bootstrap to zero yields.
2. Choose the estimation scheme: expanding window and 10-year rolling window, re-estimated monthly. Horizons of 1 month and longer use end-of-month observations; 1-day and 1-week horizons use daily data.
3. At each forecast origin, fit every model on the estimation window only and record point and density forecasts for each tenor and horizon.
4. Hold out the final period of each dataset as the untouched test set: 2019 to 2023 for the curve models and 2023-01 to 2026-04 for the overnight models. Use earlier data for model selection.
5. Compute the evaluation metrics, tests, and regime breakdowns, and write tables and figures to `results/`.

## Results & Visuals

Results are pending; the project is at the data and harness stage. Planned outputs:

- **Table 1:** RMSE (bp) and $R^2_{OOS}$ by model, tenor, and horizon.
- **Table 2:** Diebold-Mariano statistics against the random walk and Model Confidence Set membership.
- **Table 3:** Directional hit rates on $\Delta y$ and interval coverage by regime.
- **Figure 1:** Rolling RMSE through time for each model at the 2-year and 10-year tenors.
- **Figure 2:** PIT histograms for the short-rate and regime-switching models.

## Repository Structure

```plaintext
interest_rate_model_forecast/
│
├── data/
│   ├── raw/            : par-yield-curve-rates-1990-2023.csv, overnight_rates.xlsx (untouched)
│   └── processed/      : Clean daily panel, zero curves, monthly samples
│
├── notebooks/          : Exploration and result walkthroughs
│
├── src/irmf/
│   ├── data/           : Loaders and quality checks
│   ├── curves/         : Par-to-zero bootstrap, Nelson-Siegel fitting
│   ├── models/         : Benchmarks, short-rate, factor, VAR, regime-switching
│   ├── evaluation/     : Walk-forward harness, metrics, statistical tests
│   └── plots/          : Figure generation
│
├── tests/              : pytest unit tests
├── results/
│   ├── tables/
│   └── figures/
├── docs/               : Methodology notes and report drafts
├── pyproject.toml
├── README.md
└── LICENSE
```

## Getting Started

Requires Python 3.11 or later. The package entry points below are planned for Phases 1 and 2.

```bash
# Clone the repo
git clone https://github.com/agtaz19/interest_rate_model_forecast.git
cd interest_rate_model_forecast

# Create an environment and install dependencies
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Build the clean panel from the files in data/raw/
python -m irmf.data.build

# Run the walk-forward comparison
python -m irmf.evaluation.run

# Run tests
pytest
```

## Authors & Acknowledgements

### Authors

- **Alexandre Tilly**: Sole author. Research design, data engineering, model implementation, evaluation, and write-up. FQE semester project, 2026.

## References

1. Ang, A., & Bekaert, G. (2002). _Regime switches in interest rates_. Journal of Business & Economic Statistics, 20(2).
2. Campbell, J. Y., & Thompson, S. B. (2008). _Predicting excess stock returns out of sample: Can anything beat the historical average?_ Review of Financial Studies, 21(4).
3. Chan, K. C., Karolyi, G. A., Longstaff, F. A., & Sanders, A. B. (1992). _An empirical comparison of alternative models of the short-term interest rate_. Journal of Finance, 47(3).
4. Cox, J. C., Ingersoll, J. E., & Ross, S. A. (1985). _A theory of the term structure of interest rates_. Econometrica, 53(2).
5. Diebold, F. X., & Li, C. (2006). _Forecasting the term structure of government bond yields_. Journal of Econometrics, 130(2).
6. Diebold, F. X., & Mariano, R. S. (1995). _Comparing predictive accuracy_. Journal of Business & Economic Statistics, 13(3).
7. Duffee, G. R. (2002). _Term premia and interest rate forecasts in affine models_. Journal of Finance, 57(1).
8. Fama, E. F., & Bliss, R. R. (1987). _The information in long-maturity forward rates_. American Economic Review, 77(4).
9. Gneiting, T., & Raftery, A. E. (2007). _Strictly proper scoring rules, prediction, and estimation_. Journal of the American Statistical Association, 102(477).
10. Gürkaynak, R. S., Sack, B., & Wright, J. H. (2007). _The U.S. Treasury yield curve: 1961 to the present_. Journal of Monetary Economics, 54(8).
11. Hamilton, J. D. (1989). _A new approach to the economic analysis of nonstationary time series and the business cycle_. Econometrica, 57(2).
12. Hansen, P. R., Lunde, A., & Nason, J. M. (2011). _The model confidence set_. Econometrica, 79(2).
13. Litterman, R., & Scheinkman, J. (1991). _Common factors affecting bond returns_. Journal of Fixed Income, 1(1).
14. Nelson, C. R., & Siegel, A. F. (1987). _Parsimonious modeling of yield curves_. Journal of Business, 60(4).
15. Pesaran, M. H., & Timmermann, A. (1992). _A simple nonparametric test of predictive performance_. Journal of Business & Economic Statistics, 10(4).
16. Svensson, L. E. O. (1994). _Estimating and interpreting forward interest rates: Sweden 1992-1994_. NBER Working Paper 4871.
17. Vasicek, O. (1977). _An equilibrium characterization of the term structure_. Journal of Financial Economics, 5(2).

**Data sources**

- U.S. Department of the Treasury. _Daily Treasury Par Yield Curve Rates_. home.treasury.gov.
- Federal Reserve Bank of New York. _Reference Rates: EFFR, OBFR, SOFR, TGCR, BGCR_. newyorkfed.org.

## License

This project is licensed under the **MIT License**.
See the [LICENSE](LICENSE) file for details.
