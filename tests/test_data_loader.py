"""
Unit tests for src/data_loader.py.

Run with: pytest tests/test_data_loader.py -v
(from the repo root, so `from src.data_loader import ...` resolves)
"""

import pandas as pd
import pytest

from src.data_loader import (
    DataLoadError,
    load_unified_data,
    load_forecast_data,
    get_observations,
    get_events,
    get_impact_links,
    get_targets,
    get_indicator_timeseries,
    get_latest_value,
    compute_trend_delta,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

UNIFIED_COLUMNS = [
    "record_id", "record_type", "pillar", "indicator", "indicator_code",
    "value_numeric", "observation_date", "fiscal_year", "gender", "location",
]


@pytest.fixture
def valid_unified_csv(tmp_path):
    df = pd.DataFrame([
        {"record_id": "REC_1", "record_type": "observation", "pillar": "ACCESS",
         "indicator": "Account Ownership Rate", "indicator_code": "ACC_OWNERSHIP",
         "value_numeric": 46.0, "observation_date": "2021-12-31", "fiscal_year": 2021,
         "gender": "all", "location": "national"},
        {"record_id": "REC_2", "record_type": "observation", "pillar": "ACCESS",
         "indicator": "Account Ownership Rate", "indicator_code": "ACC_OWNERSHIP",
         "value_numeric": 51.0, "observation_date": "2023-12-31", "fiscal_year": 2023,
         "gender": "all", "location": "national"},
        {"record_id": "REC_3", "record_type": "event", "pillar": "ACCESS",
         "indicator": "Mobile Money Launch", "indicator_code": "EVT_MM",
         "value_numeric": None, "observation_date": "2022-06-01", "fiscal_year": 2022,
         "gender": "all", "location": "national"},
        {"record_id": "REC_4", "record_type": "impact_link", "pillar": "ACCESS",
         "indicator": "Account Ownership Rate", "indicator_code": "ACC_OWNERSHIP",
         "value_numeric": None, "observation_date": None, "fiscal_year": 2022,
         "gender": "all", "location": "national"},
        {"record_id": "REC_5", "record_type": "target", "pillar": "ACCESS",
         "indicator": "Account Ownership Rate", "indicator_code": "ACC_OWNERSHIP",
         "value_numeric": 70.0, "observation_date": "2025-12-31", "fiscal_year": 2025,
         "gender": "all", "location": "national"},
    ])
    path = tmp_path / "unified.csv"
    df.to_csv(path, index=False)
    return str(path)


@pytest.fixture
def valid_forecast_csv(tmp_path):
    # MultiIndex columns: (indicator, scenario), indexed by year.
    years = [2024, 2025, 2026]
    columns = pd.MultiIndex.from_tuples([
        ("ACC_OWNERSHIP", "optimistic"),
        ("ACC_OWNERSHIP", "base"),
        ("ACC_OWNERSHIP", "pessimistic"),
    ])
    data = [[55.0, 53.0, 51.0], [60.0, 56.0, 52.0], [65.0, 59.0, 53.0]]
    df = pd.DataFrame(data, index=years, columns=columns)
    path = tmp_path / "forecast_results.csv"
    df.to_csv(path)
    return str(path)


# ---------------------------------------------------------------------------
# load_unified_data
# ---------------------------------------------------------------------------

def test_load_unified_data_missing_file_raises(tmp_path):
    with pytest.raises(DataLoadError):
        load_unified_data(str(tmp_path / "does_not_exist.csv"))


def test_load_unified_data_missing_columns_raises(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"record_id": ["REC_1"], "record_type": ["observation"]}).to_csv(path, index=False)
    with pytest.raises(DataLoadError):
        load_unified_data(str(path))


def test_load_unified_data_bad_record_type_raises(tmp_path):
    path = tmp_path / "bad_type.csv"
    df = pd.DataFrame([{
        "record_id": "REC_1", "record_type": "not_a_real_type", "pillar": "ACCESS",
        "indicator": "X", "indicator_code": "X", "value_numeric": 1.0,
        "observation_date": "2021-01-01", "fiscal_year": 2021,
    }])
    df.to_csv(path, index=False)
    with pytest.raises(DataLoadError):
        load_unified_data(str(path))


def test_load_unified_data_valid_file_parses_dates(valid_unified_csv):
    df = load_unified_data(valid_unified_csv)
    assert len(df) == 5
    assert pd.api.types.is_datetime64_any_dtype(df["observation_date"])


# ---------------------------------------------------------------------------
# load_forecast_data
# ---------------------------------------------------------------------------

def test_load_forecast_data_missing_file_raises(tmp_path):
    with pytest.raises(DataLoadError):
        load_forecast_data(str(tmp_path / "no_forecast.csv"))


def test_load_forecast_data_reshapes_to_long_format(valid_forecast_csv):
    long_df = load_forecast_data(valid_forecast_csv)
    assert list(long_df.columns) == ["year", "indicator", "scenario", "value"]
    assert set(long_df["scenario"].unique()) == {"optimistic", "base", "pessimistic"}
    assert len(long_df) == 3 * 3  # 3 years x 3 scenarios

    row = long_df[
        (long_df["year"] == 2025) & (long_df["scenario"] == "base")
    ].iloc[0]
    assert row["value"] == 56.0


# ---------------------------------------------------------------------------
# record_type filters
# ---------------------------------------------------------------------------

def test_get_observations_events_impact_links_targets(valid_unified_csv):
    df = load_unified_data(valid_unified_csv)
    assert len(get_observations(df)) == 2
    assert len(get_events(df)) == 1
    assert len(get_impact_links(df)) == 1
    assert len(get_targets(df)) == 1


# ---------------------------------------------------------------------------
# indicator time series / deltas
# ---------------------------------------------------------------------------

def test_get_indicator_timeseries_filters_and_sorts(valid_unified_csv):
    df = load_unified_data(valid_unified_csv)
    series = get_indicator_timeseries(df, "ACC_OWNERSHIP", gender="all", location="national")
    assert len(series) == 2
    assert series.iloc[0]["value_numeric"] == 46.0
    assert series.iloc[1]["value_numeric"] == 51.0


def test_get_latest_value_returns_none_when_no_data(valid_unified_csv):
    df = load_unified_data(valid_unified_csv)
    assert get_latest_value(df, "NOT_A_REAL_CODE") is None


def test_compute_trend_delta_with_two_or_more_observations(valid_unified_csv):
    df = load_unified_data(valid_unified_csv)
    latest, previous, delta = compute_trend_delta(df, "ACC_OWNERSHIP", gender="all", location="national")
    assert latest == 51.0
    assert previous == 46.0
    assert delta == pytest.approx(5.0)


def test_compute_trend_delta_with_fewer_than_two_observations_returns_none(valid_unified_csv):
    df = load_unified_data(valid_unified_csv)
    result = compute_trend_delta(df, "EVT_MM", gender="all", location="national")
    assert result == (None, None, None)
