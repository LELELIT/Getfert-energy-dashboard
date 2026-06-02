import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from pathlib import Path
import plotly.graph_objects as go
import plotly.express as px

# ============================================================
# PAGE SETTINGS
# ============================================================

st.set_page_config(
    page_title="Getfert 2046 Energy Sufficiency Dashboard",
    layout="wide"
)

# ============================================================
# STYLE
# ============================================================

st.markdown("""
<style>
.card {
    background-color: white;
    padding: 15px;
    border-radius: 12px;
    border: 0px solid #E0E0E0;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.05);
    margin-bottom: 12px;
}
</style>
""", unsafe_allow_html=True)

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

numeric_cols = [
    "population_multiplier", "heatpump_adoption", "ev_adoption",
    "electricity_demand_gwh", "heating_demand_gwh", "ev_demand_gwh",
    "total_demand_gwh", "rooftop_supply_gwh", "parking_supply_gwh",
    "wind_supply_gwh", "green_space_supply_gwh", "total_supply_gwh",
    "energy_balance_gwh", "renewable_coverage_percent",
    "rooftop_use_percent", "parking_use_percent", "wind_use_percent",
    "green_space_use_percent", "living_environment_score",
    "x_population", "y_energy", "z_green", "intervention_stage"
]

for col in numeric_cols:
    if col in df.columns:
        df[col] = (
            df[col].astype(str)
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

if "x_population" not in df.columns:
    df["x_population"] = df["population_state"].map(population_map)

if "y_energy" not in df.columns:
    df["y_energy"] = df["energy_transition_state"].map(energy_map)

if "z_green" not in df.columns:
    df["z_green"] = df["green_state"].map(green_map)

# ============================================================
# MAXIMUM INTERVENTION POTENTIALS
# ============================================================

ROOFTOP_MAX = 6.37
PARKING_MAX = 2.80
WIND_MAX = 4.536
GREEN_SOLAR_MAX = 1.93

# ============================================================
# HEADER
# ============================================================
st.markdown("""
<div style="
    font-family:'Segoe UI', Arial, sans-serif;
    font-size:24px;
    font-weight:700;
    color:white;
    background:#1F4E79;
    padding:15px;
    border-radius:10px;
    text-align:center;
    margin-bottom:20px;
">
Decision Support Tool for Energy-Sufficient Neighbourhood Planning
</div>

<div style="
    font-family:'Segoe UI', Arial, sans-serif;
    font-size:16px;
    color:#555555;
    text-align:center;
    margin-bottom:20px;
">
Test future population, electrification, and green-transformation scenarios and evaluate renewable-energy intervention pathways for Getfert 2046.
</div>
""", unsafe_allow_html=True)
# ============================================================
# MAIN LAYOUT
# ============================================================

left, center, right = st.columns([1.15, 3.5, 1.35])
with left:
    st.markdown("### Scenario Controls")

    population = st.selectbox(
        "Population scenario",
        ["Decrease", "Stable", "Increase"]
    )

    energy = st.selectbox(
        "Electrification scenario",
        ["Slow", "Moderate", "Rapid"]
    )

    green = st.selectbox(
        "Green transformation",
        ["Minimal", "Moderate", "Extensive"]
    )

    # --------------------------------------------------
    # GREEN TRANSFORMATION RULES
    # --------------------------------------------------

    if green == "Minimal":

        max_wind = 100
        max_green_solar = 100

        default_wind = 50
        default_green_solar = 50

    elif green == "Moderate":

        max_wind = 100
        max_green_solar = 50

        default_wind = 30
        default_green_solar = 20

    else:  # Extensive

        max_wind = 75
        max_green_solar = 0

        default_wind = 20
        default_green_solar = 0

    st.markdown("---")
    st.markdown("### Policy Intervention Controls")

    roof_pct = st.slider(
        "Rooftop solar adoption (%)",
        0, 100, 100, 5
    )

    parking_pct = st.slider(
        "Parking canopy solar adoption (%)",
        0, 100, 100, 5
    )

    wind_pct = st.slider(
        "Small wind turbine adoption (%)",
        0,
        max_wind,
        default_wind,
        5
    )

    if max_green_solar == 0:
        green_solar_pct = 0

        st.info(
            "Green-space solar conversion is disabled under Extensive green transformation "
            "to protect public green space, biodiversity, and cooling benefits."
        )

    else:
        green_solar_pct = st.slider(
            "Green-space solar conversion (%)",
            0,
            max_green_solar,
            default_green_solar,
            5
        )

    st.caption(
        f"Green policy limits: Wind ≤ {max_wind}% | "
        f"Green-space solar ≤ {max_green_solar}%"
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
    st.error("No matching scenario found. Check the CSV names.")
    st.stop()

scenario = selected.iloc[0]
green_state = scenario["green_state"]

if green_state == "Minimal":
    max_green_solar = 100
    max_wind = 100

elif green_state == "Moderate":
    max_green_solar = 50
    max_wind = 100

elif green_state == "Extensive":
    max_green_solar = 0
    max_wind = 75

# ============================================================
# DYNAMIC POLICY SUPPLY CALCULATIONS
# ============================================================

rooftop_supply = ROOFTOP_MAX * (roof_pct / 100)
parking_supply = PARKING_MAX * (parking_pct / 100)
wind_supply = WIND_MAX * (wind_pct / 100)
green_space_supply = GREEN_SOLAR_MAX * (green_solar_pct / 100)

policy_total_supply = (
    rooftop_supply +
    parking_supply +
    wind_supply +
    green_space_supply
)

policy_energy_balance = policy_total_supply - scenario["total_demand_gwh"]

policy_coverage = (
    policy_total_supply / scenario["total_demand_gwh"]
) * 100

living_impact_score = (
    (parking_pct * 0.01) +
    (wind_pct * 0.02) +
    (green_solar_pct * 0.05)
)

if living_impact_score < 2:
    living_class = "Low impact"
elif living_impact_score < 5:
    living_class = "Moderate impact"
else:
    living_class = "High impact"

# ============================================================
# CENTER PANEL — CUBE + CHARTS
# ============================================================

with center:
    st.markdown("### 27-Scenario Cube")

    fig_cube = go.Figure()

    fig_cube.add_trace(go.Scatter3d(
        x=df["x_population"],
        y=df["y_energy"],
        z=df["z_green"],
        mode="markers+text",
        text=df["scenario_id"],
        textposition="top center",
        showlegend=False,
        marker=dict(
    size=7,
    color=df["total_demand_gwh"],
    colorscale="YlOrRd",
    colorbar=dict(title="Demand<br>(GWh/yr)"),
    opacity=0.88
),
        customdata=df[
            [
                "population_state",
                "energy_transition_state",
                "green_state",
                "total_demand_gwh",
                "energy_balance_gwh"
            ]
        ],
        hovertemplate=
            "Scenario: %{text}<br>" +
            "Population: %{customdata[0]}<br>" +
            "Electrification: %{customdata[1]}<br>" +
            "Green: %{customdata[2]}<br>" +
            "Future demand: %{customdata[3]:.2f} GWh/yr<extra></extra>"
    ))

    fig_cube.add_trace(go.Scatter3d(
        x=[scenario["x_population"]],
        y=[scenario["y_energy"]],
        z=[scenario["z_green"]],
        mode="markers+text",
        text=["Selected"],
        textposition="bottom center",
        showlegend=False,
        marker=dict(
            size=8,
            color="blue",
            symbol="diamond"
        )
    ))

    fig_cube.update_layout(
        height=420,
        scene=dict(
            xaxis=dict(
                title="Population",
                tickvals=[0, 1, 2],
                ticktext=["Decrease", "Stable", "Increase"]
            ),
            yaxis=dict(
                title="Electrification",
                tickvals=[0, 1, 2],
                ticktext=["Slow", "Moderate", "Rapid"]
            ),
            zaxis=dict(
                title="Green transformation",
                tickvals=[0, 1, 2],
                ticktext=["Minimal", "Moderate", "Extensive"]
            )
        ),
        margin=dict(l=0, r=0, b=0, t=15)
    )

    st.plotly_chart(fig_cube, use_container_width=True, key="scenario_cube")

    chart_left, chart_right = st.columns(2)

    with chart_left:
        st.markdown("### Demand Breakdown")

        demand_df = pd.DataFrame({
            "Demand source": [
                "Electricity",
                "Heating electrification",
                "EV mobility"
            ],
            "GWh/year": [
                scenario["electricity_demand_gwh"],
                scenario["heating_demand_gwh"],
                scenario["ev_demand_gwh"]
            ]
        })

        fig_demand = px.bar(
            demand_df,
            x="Demand source",
            y="GWh/year",
            text="GWh/year",
            title="Demand drivers"
        )

        fig_demand.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside"
        )

        fig_demand.update_layout(
            height=300,
            margin=dict(l=5, r=5, t=40, b=5)
        )

        st.plotly_chart(fig_demand, use_container_width=True, key="demand_breakdown")

    with chart_right:
        st.markdown("### Policy Supply Mix")

        supply_df = pd.DataFrame({
            "Supply source": [
                "Rooftop solar",
                "Parking canopies",
                "Small wind turbines",
                "Green-space solar"
            ],
            "GWh/year": [
                rooftop_supply,
                parking_supply,
                wind_supply,
                green_space_supply
            ]
        })

        fig_supply = px.bar(
            supply_df,
            x="Supply source",
            y="GWh/year",
            text="GWh/year",
            title="User-selected supply interventions"
        )

        fig_supply.update_traces(
            texttemplate="%{text:.2f}",
            textposition="outside"
        )

        fig_supply.update_layout(
            height=300,
            margin=dict(l=5, r=5, t=40, b=5)
        )

        st.plotly_chart(fig_supply, use_container_width=True, key="policy_supply_breakdown")

# ============================================================
# RIGHT PANEL — DYNAMIC KPI RESULTS
# ============================================================

with right:
    st.markdown("### Selected Scenario")

    st.success(
        f"{scenario['scenario_id']} | "
        f"{scenario['population_state']} | "
        f"{scenario['energy_transition_state']} | "
        f"{scenario['green_state']}"
    )

    st.metric(
        "Total demand",
        f"{scenario['total_demand_gwh']:.2f} GWh/yr"
    )

    st.metric(
        "Policy supply",
        f"{policy_total_supply:.2f} GWh/yr"
    )

    st.metric(
        "Policy balance",
        f"{policy_energy_balance:.2f} GWh/yr"
    )

    st.metric(
        "Renewable coverage",
        f"{policy_coverage:.1f}%"
    )

    st.markdown("---")
    st.markdown("### Intervention impact on theLiving Environment")

    st.write(f"**Impact score:** {living_impact_score:.2f}")
    st.write(f"**Impact class:** {living_class}")

# ============================================================
# RECOMMENDATION + INTERPRETATION
# ============================================================

st.markdown("---")

col_rec, col_interp = st.columns([1, 1])

with col_rec:
    st.markdown("### Policy Result")

    if policy_energy_balance >= 0:
        st.success("This policy mix achieves local energy sufficiency.")
    else:
        st.warning(
            f"This policy mix leaves a deficit of {abs(policy_energy_balance):.2f} GWh/yr."
        )

with col_interp:
    st.markdown("### Energy + Health Interpretation")

    if green_solar_pct > 0:
        st.error(
            "Green-space solar improves energy supply but may reduce recreation space, biodiversity and urban cooling."
        )
    elif wind_pct > 0:
        st.warning(
            "Small wind turbines help close the gap but may create visual and noise concerns."
        )
    elif parking_pct > 0:
        st.info(
            "Parking canopies provide energy, shade and support EV charging infrastructure."
        )
    else:
        st.success(
            "Rooftop solar has the lowest spatial and health trade-off."
        )

# ============================================================
# INTERVENTION SEQUENCE + 3D MODEL
# ============================================================
with center:
    
    st.markdown("### 3D Getfert Model")

    components.iframe(
    "https://lelelit.github.io/Getfert-energy-dashboard/assets/index.html",
    height=600,
      width=1600,
    scrolling=False)

# ============================================================
# FULL TABLE
# ============================================================

with st.expander("View full 27-scenario table"):
    st.dataframe(df, use_container_width=True)