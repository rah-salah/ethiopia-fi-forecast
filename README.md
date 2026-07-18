# Ethiopia Financial Inclusion Forecasting

Forecasting system for Ethiopia's digital financial transformation, built for **Selam Analytics**. Predicts Access (Account Ownership) and Usage (Digital Payment Adoption) trends for 2025-2027, using a curated, source-documented dataset of survey observations, market events, and estimated event impacts.

## Setup

```bash
pip install -r requirements.txt
```

Then explore the data via the notebook:

```bash
jupyter notebook notebooks/task1_2_exploration_eda.ipynb
```

## Data Sources

- **`data/raw/ethiopia_fi_unified_data.csv`**  -  the core dataset: survey observations (e.g. Global Findex account ownership), market events (e.g. Telebirr launch), estimated event impacts, and policy targets. Originally converted from `ethiopia_fi_unified_data.xlsx` (see `src/convert_raw_data.py`), then extended with 5 additional sourced records (see `data_enrichment_log.md`).
- **`data/raw/reference_codes.csv`**  -  lookup table defining the controlled vocabulary used throughout the unified dataset (valid `record_type`, `pillar`, `indicator_direction`, `value_type` values, etc.).
- Primary external sources include the World Bank Global Findex Database (2014/2017/2021/2024 editions), the National Bank of Ethiopia, individual mobile money operators (Ethio Telecom/Telebirr, Safaricom/M-Pesa), and peer-reviewed research citing Findex microdata. Every record traces back to a `source_name`/`source_url` pair.

## Unified Schema

All data lives in a single flat table (`ethiopia_fi_unified_data.csv`), with each row's meaning determined by its `record_type`:

| record_type | Meaning | `pillar` set? |
|---|---|---|
| `observation` | An actual measured value from a source (e.g. "49% account ownership, Nov 2024, Global Findex") | Yes |
| `event` | A policy launch, market event, or milestone (e.g. "Telebirr Launch, May 2021") | No  -  an event itself isn't tied to one pillar |
| `impact_link` | An analyst-estimated relationship connecting an `event` to the `indicator` it plausibly affected, via `parent_id` | No |
| `target` | An official policy target or goal (e.g. NBE's 2030 gender-parity target) | Yes |

**How `impact_link` connects events to indicators:** each `impact_link` row's `parent_id` points back to the `record_id` of the `event` that caused it, and its `related_indicator` field names the `indicator_code` it affects (e.g. `ACC_OWNERSHIP`). Fields like `impact_direction`, `impact_magnitude`, `impact_estimate`, and `lag_months` quantify the analyst's estimate of that effect, with `evidence_basis` and `comparable_country` documenting how the estimate was derived. This is explained and demonstrated with a worked example in `notebooks/task1_2_exploration_eda.ipynb`.

Key `pillar` values used for observations/targets: `ACCESS`, `USAGE`, `GENDER`, `AFFORDABILITY`. Full controlled vocabulary is in `data/raw/reference_codes.csv`.

## Data Enrichment

New data points added beyond the original dataset are documented in **`data_enrichment_log.md`**, including source URLs, original source text, confidence ratings, and justification for why each addition is useful.

## Project Structure

```
ethiopia-fi-forecast/
|-- data/
|   |-- raw/            # unified dataset, reference codes, original Excel sources
|   `-- processed/      # generated figures and any derived/cleaned data
|-- notebooks/          # exploration, EDA, and modeling notebooks
|-- src/                # reusable Python modules (data conversion, etc.)
|-- dashboard/          # Streamlit dashboard app (Task 5)
|-- models/             # saved forecasting models (Task 4)
|-- reports/figures/    # exported charts for the final report
`-- tests/              # unit tests
```

Work is organized into task branches (`task-1` data & enrichment, `task-2` EDA, `task-3` event impact modeling, `task-4` forecasting, `task-5` dashboard), each merged into `main` via pull request.
