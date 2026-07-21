"""
Ethiopia Financial Inclusion — Forecasting Dashboard (Task 5)

Four sections per the rubric:
  1. Overview            — summary cards for key indicators
  2. Trends               — historical time series, filterable
  3. Forecasts            — modeled projections with scenario bands
  4. Inclusion Projections — forecast vs official targets

Run with:  streamlit run dashboard/app.py
(run from the repo root so the src/ and data/ relative paths resolve)
"""

import os
import sys

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Allow `from src.data_loader import ...` whether Streamlit is launched
# from the repo root or from inside dashboard/.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_loader import (  # noqa: E402
    DataLoadError,
    load_unified_data,
    load_forecast_data,
    get_observations,
    get_events,
    get_targets,
    get_indicator_timeseries,
    compute_trend_delta,
)

st.set_page_config(
    page_title="Ethiopia Financial Inclusion Dashboard",
    layout="wide",
)


# ---------------------------------------------------------------------------
# Data loading (cached so re-running the app doesn't re-read CSVs every time)
# ---------------------------------------------------------------------------

@st.cache_data
def get_unified_df():
    return load_unified_data()


@st.cache_data
def get_forecast_df():
    return load_forecast_data()


try:
    unified_df = get_unified_df()
except DataLoadError as e:
    st.error(f"Could not load the unified dataset: {e}")
    st.stop()

try:
    forecast_df = get_forecast_df()
    forecast_error = None
except DataLoadError as e:
    forecast_df = pd.DataFrame(columns=["year", "indicator", "scenario", "value"])
    forecast_error = str(e)

observations = get_observations(unified_df)
events = get_events(unified_df)
targets = get_targets(unified_df)


# ---------------------------------------------------------------------------
# Sidebar — global filters
# ---------------------------------------------------------------------------

st.sidebar.title("Filters")

genders = sorted(observations["gender"].dropna().unique().tolist()) if "gender" in observations else ["all"]
locations = sorted(observations["location"].dropna().unique().tolist()) if "location" in observations else ["national"]
indicator_codes = sorted(observations["indicator_code"].dropna().unique().tolist())
indicator_names = (
    observations[["indicator_code", "indicator"]]
    .drop_duplicates()
    .set_index("indicator_code")["indicator"]
    .to_dict()
)

selected_gender = st.sidebar.selectbox("Gender", options=genders, index=genders.index("all") if "all" in genders else 0)
selected_location = st.sidebar.selectbox("Location", options=locations, index=locations.index("national") if "national" in locations else 0)

st.sidebar.markdown("---")
section = st.sidebar.radio(
    "Section",
    ["Overview", "Trends", "Forecasts", "Inclusion Projections"],
)


# ---------------------------------------------------------------------------
# Section 1 — Overview
# ---------------------------------------------------------------------------

def render_overview():
    st.title("Overview")
    st.caption("Latest reading and change vs. the prior observation, per indicator.")

    cols = st.columns(min(4, max(1, len(indicator_codes))))
    for i, code in enumerate(indicator_codes):
        latest, previous, delta = compute_trend_delta(
            unified_df, code, gender=selected_gender, location=selected_location
        )
        with cols[i % len(cols)]:
            label = indicator_names.get(code, code)
            if latest is None:
                st.metric(label, "no data")
            else:
                st.metric(label, f"{latest:,.2f}", delta=f"{delta:+,.2f}" if delta is not None else None)

    st.markdown("---")
    st.subheader("Indicators by pillar")
    if "pillar" in observations.columns:
        pillar_counts = observations.groupby("pillar")["indicator_code"].nunique().reset_index()
        pillar_counts.columns = ["pillar", "num_indicators"]
        fig = px.bar(pillar_counts, x="pillar", y="num_indicators", title="Indicator coverage by pillar")
        st.plotly_chart(fig, use_container_width=True)

    if not events.empty and "observation_date" in events.columns:
        st.subheader("Recent events")
        event_cols = [c for c in ["observation_date", "indicator", "value_numeric"] if c in events.columns]
        st.dataframe(events.sort_values("observation_date", ascending=False)[event_cols].head(10))


# ---------------------------------------------------------------------------
# Section 2 — Trends
# ---------------------------------------------------------------------------

def render_trends():
    st.title("Trends")
    st.caption("Historical values for a chosen indicator, filtered by gender/location and date range.")

    code = st.selectbox(
        "Indicator",
        options=indicator_codes,
        format_func=lambda c: indicator_names.get(c, c),
        key="trends_indicator",
    )

    series = get_indicator_timeseries(unified_df, code, gender=selected_gender, location=selected_location)

    if series.empty:
        st.warning("No observations for this indicator/gender/location combination.")
        return

    min_date, max_date = series["observation_date"].min(), series["observation_date"].max()
    date_range = st.slider(
        "Date range",
        min_value=min_date.to_pydatetime(),
        max_value=max_date.to_pydatetime(),
        value=(min_date.to_pydatetime(), max_date.to_pydatetime()),
    )
    filtered = series[
        (series["observation_date"] >= date_range[0]) & (series["observation_date"] <= date_range[1])
    ]

    fig = px.line(
        filtered,
        x="observation_date",
        y="value_numeric",
        markers=True,
        title=f"{indicator_names.get(code, code)} over time",
    )

    # Overlay event markers that fall in the visible date range, if any.
    if not events.empty and "observation_date" in events.columns:
        visible_events = events[
            (events["observation_date"] >= date_range[0]) & (events["observation_date"] <= date_range[1])
        ]
        for _, ev in visible_events.iterrows():
            fig.add_vline(x=ev["observation_date"], line_dash="dot", line_color="gray")

    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(filtered[["observation_date", "value_numeric"]].sort_values("observation_date", ascending=False))


# ---------------------------------------------------------------------------
# Section 3 — Forecasts
# ---------------------------------------------------------------------------

def render_forecasts():
    st.title("Forecasts")
    st.caption("Modeled projections by scenario, with the optimistic/pessimistic range shown as a band.")

    if forecast_error:
        st.error(f"Could not load forecast results: {forecast_error}")
        return

    forecast_indicators = sorted(forecast_df["indicator"].dropna().unique().tolist())
    if not forecast_indicators:
        st.warning("No forecast data available.")
        return

    code = st.selectbox("Indicator", options=forecast_indicators, key="forecast_indicator")
    subset = forecast_df[forecast_df["indicator"] == code].sort_values("year")

    pivot = subset.pivot(index="year", columns="scenario", values="value")

    fig = go.Figure()
    if "optimistic" in pivot.columns and "pessimistic" in pivot.columns:
        fig.add_trace(go.Scatter(
            x=pivot.index, y=pivot["optimistic"], line=dict(width=0), showlegend=False, hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(
            x=pivot.index, y=pivot["pessimistic"], fill="tonexty", fillcolor="rgba(99,110,250,0.15)",
            line=dict(width=0), name="Optimistic–pessimistic range",
        ))
    for scenario in ["pessimistic", "base", "optimistic"]:
        if scenario in pivot.columns:
            fig.add_trace(go.Scatter(x=pivot.index, y=pivot[scenario], mode="lines+markers", name=scenario))

    fig.update_layout(title=f"{code} — forecast by scenario", xaxis_title="year", yaxis_title="value")
    st.plotly_chart(fig, use_container_width=True)
    st.dataframe(pivot.reset_index())


# ---------------------------------------------------------------------------
# Section 4 — Inclusion Projections vs. targets
# ---------------------------------------------------------------------------

def render_inclusion_projections():
    st.title("Inclusion Projections")
    st.caption("Base-scenario forecast against official policy targets.")

    if forecast_error:
        st.error(f"Could not load forecast results: {forecast_error}")
        return

    if targets.empty:
        st.warning("No target records found in the unified dataset.")
        return

    # Targets use fiscal_year as the target year and value_numeric as the
    # target value, matched to a forecast series via indicator_code.
    forecast_indicators = sorted(forecast_df["indicator"].dropna().unique().tolist())
    code = st.selectbox("Indicator", options=forecast_indicators, key="projection_indicator")

    base = forecast_df[(forecast_df["indicator"] == code) & (forecast_df["scenario"] == "base")].sort_values("year")

    # forecast_df's "indicator" values may be codes (e.g. ACC_OWNERSHIP) or
    # full names (e.g. "Account Ownership Rate") depending on how
    # forecast_results.csv was built — match against both so this works
    # either way.
    ind_targets = targets[
        (targets.get("indicator_code", pd.Series(dtype=object)) == code)
        | (targets.get("indicator", pd.Series(dtype=object)) == code)
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=base["year"], y=base["value"], mode="lines+markers", name="Base forecast"))
    if not ind_targets.empty:
        fig.add_trace(go.Scatter(
            x=ind_targets["fiscal_year"], y=ind_targets["value_numeric"],
            mode="markers", marker=dict(size=14, symbol="star", color="red"), name="Target",
        ))
    else:
        st.info("No matching target found for this indicator's code/name — showing forecast only.")
    fig.update_layout(title=f"{code} — forecast vs. target", xaxis_title="year", yaxis_title="value")
    st.plotly_chart(fig, use_container_width=True)


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

if section == "Overview":
    render_overview()
elif section == "Trends":
    render_trends()
elif section == "Forecasts":
    render_forecasts()
elif section == "Inclusion Projections":
    render_inclusion_projections()
