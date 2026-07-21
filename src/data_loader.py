"""
Data loading and shaping utilities for the Ethiopia Financial Inclusion
dashboard (Task 5).

Kept separate from dashboard/app.py so it can be unit-tested without
importing Streamlit or running a Streamlit page.
"""

import os
import pandas as pd

VALID_RECORD_TYPES = {"observation", "event", "impact_link", "target"}


class DataLoadError(Exception):
    """Raised when a source file is missing or fails basic schema checks."""
    pass


def load_unified_data(path="data/raw/ethiopia_fi_unified_data.csv"):
    """
    Load the unified indicators/events/impact_links/targets dataset.

    Parses observation_date into a real datetime column and validates that
    record_type only contains values the schema allows.
    """
    if not os.path.exists(path):
        raise DataLoadError(f"Unified data file not found at: {path}")

    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError as e:
        raise DataLoadError(f"Unified data file is empty: {path}") from e
    except pd.errors.ParserError as e:
        raise DataLoadError(f"Could not parse unified data file: {path}") from e

    if df.empty:
        raise DataLoadError(f"Unified data file has no rows: {path}")

    required_cols = {
        "record_id", "record_type", "pillar", "indicator", "indicator_code",
        "value_numeric", "observation_date", "fiscal_year",
    }
    missing = required_cols - set(df.columns)
    if missing:
        raise DataLoadError(f"Unified data file is missing expected columns: {sorted(missing)}")

    bad_types = set(df["record_type"].dropna().unique()) - VALID_RECORD_TYPES
    if bad_types:
        raise DataLoadError(f"Unexpected record_type value(s) found: {sorted(bad_types)}")

    df["observation_date"] = pd.to_datetime(df["observation_date"], errors="coerce")
    df["value_numeric"] = pd.to_numeric(df["value_numeric"], errors="coerce")

    return df


def load_forecast_data(path="models/forecast_results.csv"):
    """
    Load models/forecast_results.csv, a pandas MultiIndex-column export
    (columns = (indicator, scenario), index = year), and reshape it into
    a tidy long-format table: year, indicator, scenario, value.
    """
    if not os.path.exists(path):
        raise DataLoadError(f"Forecast results file not found at: {path}")

    try:
        wide = pd.read_csv(path, header=[0, 1], index_col=0)
    except Exception as e:
        raise DataLoadError(f"Could not parse forecast results file: {path}") from e

    if wide.empty:
        raise DataLoadError(f"Forecast results file has no rows: {path}")

    wide.index.name = "year"
    long_df = wide.stack(level=[0, 1], future_stack=True).reset_index()
    long_df.columns = ["year", "indicator", "scenario", "value"]
    long_df["year"] = pd.to_numeric(long_df["year"], errors="coerce").astype("Int64")
    long_df["value"] = pd.to_numeric(long_df["value"], errors="coerce")

    expected_scenarios = {"optimistic", "base", "pessimistic"}
    found_scenarios = set(long_df["scenario"].unique())
    if not found_scenarios.issubset(expected_scenarios | {"nan"}):
        raise DataLoadError(f"Unexpected scenario value(s) in forecast file: {sorted(found_scenarios - expected_scenarios)}")

    return long_df


def get_observations(df):
    """Return only observation rows (actual measured values)."""
    return df[df["record_type"] == "observation"].copy()


def get_events(df):
    """Return only event rows (policy/market events)."""
    return df[df["record_type"] == "event"].copy()


def get_impact_links(df):
    """Return only impact_link rows (event -> indicator effect estimates)."""
    return df[df["record_type"] == "impact_link"].copy()


def get_targets(df):
    """Return only target rows (official policy goals)."""
    return df[df["record_type"] == "target"].copy()


def get_indicator_timeseries(df, indicator_code, gender="all", location="national"):
    """
    Filter observations down to a single indicator's time series, sorted
    by observation date. Used to drive the Trends section's line charts.
    """
    obs = get_observations(df)
    subset = obs[
        (obs["indicator_code"] == indicator_code)
        & (obs["gender"] == gender)
        & (obs["location"] == location)
    ]
    return subset.sort_values("observation_date")


def get_latest_value(df, indicator_code, gender="all", location="national"):
    """
    Return the most recent observation for an indicator, or None if there
    isn't one. Used for the Overview section's summary cards.
    """
    series = get_indicator_timeseries(df, indicator_code, gender, location)
    if series.empty:
        return None
    return series.iloc[-1]


def compute_trend_delta(df, indicator_code, gender="all", location="national"):
    """
    Return (latest_value, previous_value, delta) for an indicator, so the
    Overview cards can show a value plus a change-from-prior-reading arrow.
    Returns (None, None, None) if there are fewer than 2 observations.
    """
    series = get_indicator_timeseries(df, indicator_code, gender, location)
    if len(series) < 2:
        return None, None, None
    latest = series.iloc[-1]["value_numeric"]
    previous = series.iloc[-2]["value_numeric"]
    return latest, previous, latest - previous
