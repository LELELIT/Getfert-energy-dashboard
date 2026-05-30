import streamlit.components.v1 as components
import streamlit as st
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px

# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="Getfert 2046 Scenario Dashboard",
    layout="wide"
)

# ============================================================
# LOAD DATA
# ============================================================

data_path = Path("data/getfert_27_scenarios.csv")
df = pd.read_csv(data_path, sep=";", encoding="utf-8-sig")

df.columns = (
    df.columns
    .str.replace("\ufeff", "", regex=False)
    .str.strip()
    .str.lower()
    .str.replace(" ", "_")
)

df = df.rename(columns={
    df.columns[1]: "population_state",
    df.columns[2]: "energy_transition_state",
    df.columns[3]: "green_state"
})

numeric_cols = [
    "population_multiplier",
    "solar_adoption",
    "heatpump_adoption",
    "ev_adoption",
    "electricity_demand_gwh",
    "heating_demand_gwh",
    "ev_demand_gwh",
    "total_demand_gwh",
    "solar_supply_gwh",
    "energy_balance_gwh",
    "renewable_coverage_percent",
    "energy_gap_gwh",
    "additional_solar_required_gwh",
    "additional_rooftop_or_canopy_percent"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(",", ".", regex=False)
            .str.strip()
        )
        df[col] = pd.to_numeric(df[col], errors="coerce")

# ============================================================
# CUBE COORDINATES
# ============================================================

population_map = {"Decrease": 0, "Stable": 1, "Increase": 2}
energy_map = {"Slow": 0, "Moderate": 1, "Rapid": 2}
green_map = {"Minimal": 0, "Moderate": 1, "Extensive": 2}

df["x_population"] = df["population_state"].map(population_map)
df["y_energy"] = df["energy_transition_state"].map(energy_map)
df["z_green"] = df["green_state"].map(green_map)

# ============================================================
# HEADER
# ============================================================

st.caption("Getfert neighbourhood — Energy self-sufficiency 2046")

# ============================================================
# THREE-PANEL LAYOUT
# ============================================================

left, center, right = st.columns([1.15, 3.8, 1.25])

# ============================================================
# LEFT PANEL: SCENARIO CONTROLS
# ============================================================

with left:
    st.markdown("### Scenario Dashboard")

    st.markdown("#### Population & settlement")

    population = st.selectbox(
        "Population scenario",
        ["Decrease", "Stable", "Increase"]
    )

    energy = st.selectbox(
        "Energy transition scenario",
        ["Slow", "Moderate", "Rapid"]
    )

    green = st.selectbox(
        "Green transformation scenario",
        ["Minimal", "Moderate", "Extensive"]
    )

    st.markdown("---")

    st.markdown("#### Scenario meaning")

    st.write(f"**Population:** {population}")
    st.write(f"**Energy transition:** {energy}")
    st.write(f"**Green transformation:** {green}")

    st.markdown("---")

    st.markdown("#### Scenario cube tags")

    st.info(
        f"Population: {population}\n\n"
        f"Energy: {energy}\n\n"
        f"Green: {green}"
    )

# ============================================================
# FILTER SELECTED SCENARIO
# ============================================================

selected = df[
    (df["population_state"] == population) &
    (df["energy_transition_state"] == energy) &
    (df["green_state"] == green)
]

if selected.empty:
    st.error("No matching scenario found. Check scenario names in CSV.")
    st.stop()

scenario = selected.iloc[0]

# ============================================================
# CENTER PANEL: CUBE + CHARTS
# ============================================================

with center:
    st.markdown("### Scenario Cube")

    fig = go.Figure()

    # All 27 scenarios
    fig.add_trace(go.Scatter3d(
        x=df["x_population"],
        y=df["y_energy"],
        z=df["z_green"],
        mode="markers+text",
        text=df["scenario_id"],
        textposition="top center",
        showlegend=False,
        marker=dict(
            size=7,
            color=df["renewable_coverage_percent"],
            colorscale="Viridis",
            colorbar=dict(title="Coverage (%)"),
            opacity=0.85
        ),
        hovertemplate=
            "Scenario: %{text}<br>" +
            "Population: %{customdata[0]}<br>" +
            "Energy: %{customdata[1]}<br>" +
            "Green: %{customdata[2]}<br>" +
            "Coverage: %{customdata[3]:.1f}%<br>" +
            "Balance: %{customdata[4]:.2f} GWh<extra></extra>",
        customdata=df[
            [
                "population_state",
                "energy_transition_state",
                "green_state",
                "renewable_coverage_percent",
                "energy_balance_gwh"
            ]
        ]
    ))

    # Selected scenario marker
    fig.add_trace(go.Scatter3d(
        x=[scenario["x_population"]],
        y=[scenario["y_energy"]],
        z=[scenario["z_green"]],
        mode="markers+text",
        text=["Selected"],
        textposition="bottom center",
        showlegend=False,
        marker=dict(
            size=12,
            color="red",
            symbol="diamond"
        ),
        hovertemplate="Selected scenario<extra></extra>"
    ))

    fig.update_layout(
        height=500,
        scene=dict(
            xaxis=dict(
                title="Population",
                tickvals=[0, 1, 2],
                ticktext=["Decrease", "Stable", "Increase"]
            ),
            yaxis=dict(
                title="Energy transition",
                tickvals=[0, 1, 2],
                ticktext=["Slow", "Moderate", "Rapid"]
            ),
            zaxis=dict(
                title="Green transformation",
                tickvals=[0, 1, 2],
                ticktext=["Minimal", "Moderate", "Extensive"]
            )
        ),
        margin=dict(l=0, r=0, b=0, t=20)
    )

    st.plotly_chart(fig, use_container_width=True, key="scenario_cube_chart")

    st.markdown("### Demand vs Renewable Supply")

    chart_df = pd.DataFrame({
        "Metric": ["Total demand", "Renewable supply"],
        "GWh/year": [
            scenario["total_demand_gwh"],
            scenario["solar_supply_gwh"]
        ]
    })

    fig_bar = px.bar(
        chart_df,
        x="Metric",
        y="GWh/year",
        text="GWh/year",
        title="Selected scenario energy balance"
    )

    fig_bar.update_traces(texttemplate="%{text:.2f}", textposition="outside")
    fig_bar.update_layout(height=360)

    st.plotly_chart(fig_bar, use_container_width=True, key="demand_supply_chart")

# ============================================================
# RIGHT PANEL: NUMERICAL RESULTS
# ============================================================

with right:
    st.markdown("### Numerical Results")

    st.markdown(f"**Selected scenario:** `{scenario['scenario_id']}`")

    st.metric(
        "Energy supply",
        f"{scenario['solar_supply_gwh']:.2f} GWh/yr"
    )

    st.metric(
        "Energy demand",
        f"{scenario['total_demand_gwh']:.2f} GWh/yr"
    )

    st.metric(
        "Net balance",
        f"{scenario['energy_balance_gwh']:.2f} GWh/yr"
    )

    st.metric(
        "Renewable coverage",
        f"{scenario['renewable_coverage_percent']:.1f}%"
    )

    st.markdown("---")

    st.markdown("#### Energy Gap")

    if "energy_gap_gwh" in df.columns:
        st.metric(
            "Energy gap",
            f"{scenario['energy_gap_gwh']:.2f} GWh/yr"
        )

    if "additional_solar_required_gwh" in df.columns:
        st.metric(
            "Additional solar needed",
            f"{scenario['additional_solar_required_gwh']:.2f} GWh/yr"
        )

    if "additional_rooftop_or_canopy_percent" in df.columns:
        st.metric(
            "Extra rooftop/canopy use",
            f"{scenario['additional_rooftop_or_canopy_percent']:.1f}%"
        )

    st.markdown("---")

    st.markdown("#### Health & Environment")

    st.write(f"**Resilience:** {scenario['resilience_class']}")
    st.write(f"**Health class:** {scenario['health_environment_class']}")

    st.markdown("---")

    st.markdown("#### Recommended Action")

    if "recommended_intervention" in df.columns:
        st.info(scenario["recommended_intervention"])

# ============================================================
# LOWER DASHBOARD SECTION
# ============================================================

st.markdown("---")

bottom_left, bottom_right = st.columns([1.4, 1])

with bottom_left:
    st.markdown("### Top Performing Scenarios")

    top_df = df.sort_values(
        by="renewable_coverage_percent",
        ascending=False
    ).head(5)

    fig_top = px.bar(
        top_df,
        x="renewable_coverage_percent",
        y="scenario_id",
        orientation="h",
        text="renewable_coverage_percent",
        title="Top 5 scenarios by renewable coverage"
    )

    fig_top.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
    fig_top.update_layout(
        yaxis=dict(autorange="reversed"),
        xaxis_title="Renewable coverage (%)",
        yaxis_title="Scenario",
        height=360
    )

    st.plotly_chart(fig_top, use_container_width=True, key="top_scenarios_chart")

with bottom_right:
    st.markdown("### Selected Scenario Interpretation")

    st.success(
        f"{scenario['scenario_id']} combines "
        f"**{scenario['population_state']} population**, "
        f"**{scenario['energy_transition_state']} energy transition**, and "
        f"**{scenario['green_state']} green transformation**."
    )

    if scenario["energy_balance_gwh"] < 0:
        st.warning(
            "This scenario has an energy deficit. Additional renewable production, "
            "storage, or demand-reduction strategies are needed."
        )
    else:
        st.success(
            "This scenario produces enough renewable energy to meet or exceed demand."
        )
        st.markdown("### 3D Getfert Model")
#===========================================================
#3D MODEL DISPLAY
#===========================================================

with center:
    
    st.markdown("### 3D Getfert Model")

    components.iframe(
    "https://lelelit.github.io/Getfert-energy-dashboard/assets/index.html",
    height=500,
    scrolling=False
)

    st.markdown("### Demand vs Renewable Supply")

# ============================================================
# FULL TABLE
# ============================================================

with st.expander("View all 27 scenarios"):
    st.dataframe(df, use_container_width=True)