# Modern Non-Parametrics in Global Health

This project analyzes major global health and clinical trials datasets (IHME, World Bank, WHO, and ClinicalTrials.gov) utilizing advanced statistical methods from recent journals. The current focus is on "Modern Non-parametrics".

## Project Overview

- **Dataset:** IHME GBD 2021, World Bank WDI, WHO GHO, and ClinicalTrials.gov API v2.
- **Methods:** Non-parametric Kernel Regression (Gaussian Kernel) and Linear Regression Baseline.
- **Key Findings:** Identified a 2.15-year mean delta in life expectancy estimates compared to standard linear baselines in 2019 cross-sectional analysis.
- **Provenance:** All data numbers are certified via TruthCert (SHA-256 hashes in `data/manifest.json`).

## Structure

- `data/`: Raw and processed data with manifest.
- `scripts/`: Data ingestion and TruthCert hashing scripts.
- `models/`: Statistical modeling and analysis scripts.
- `dashboard/`: Interactive HTML/JS dashboard for visualizing results.
- `tests/`: Automated test suite for pipeline validation.

## Dashboard

The interactive dashboard is deployed to [GitHub Pages](https://mahmood726-cyber.github.io/modern-stats-global-health/).

## License

Open Access / MIT.
