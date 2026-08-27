import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

# -----------------------------
# Page configuration
# -----------------------------

st.set_page_config(
    page_title="ResilienceMap",
    page_icon="🌍",
    layout="wide"
)

st.title("🌍 ResilienceMap")
st.subheader("Spatial Disaster Risk Assessment — Kamrup Metropolitan")

# -----------------------------
# Load risk data
# -----------------------------

@st.cache_data
def load_data():
    return gpd.read_file(
        "data/processed/resiliencemap_final.gpkg",
        layer="risk_grid"
    )

grid = load_data()

# -----------------------------
# Statistics
# -----------------------------

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Grid Cells",
    len(grid)
)

col2.metric(
    "Buildings",
    f"{grid['building_count'].sum():,}"
)

col3.metric(
    "Highest Risk",
    f"{grid['final_risk_score'].max():.1f}"
)

col4.metric(
    "Critical Cells",
    int((grid["final_risk_class"] == "Critical").sum())
)



map_data = grid.to_crs("EPSG:4326")

# -----------------------------
# Risk Filters
# -----------------------------

st.sidebar.header("Risk Filters")

risk_options = [
    "All",
    "Low",
    "Moderate",
    "High",
    "Very High",
    "Critical"
]

selected_risk = st.sidebar.selectbox(
    "Show Risk Level",
    risk_options
)

if selected_risk != "All":
    map_data = map_data[
        map_data["final_risk_class"] == selected_risk
    ]

# Risk summary
st.sidebar.markdown("---")
st.sidebar.subheader("Risk Summary")

risk_counts = grid["final_risk_class"].value_counts()

for level in ["Low", "Moderate", "High", "Very High", "Critical"]:
    st.sidebar.write(
        f"**{level}:** {risk_counts.get(level, 0)}"
    )

# -----------------------------
# Create map
# -----------------------------

st.subheader("Risk Map")

center = [
    map_data.geometry.centroid.y.mean(),
    map_data.geometry.centroid.x.mean()
]

m = folium.Map(
    location=center,
    zoom_start=11,
    tiles="OpenStreetMap"
)

# -----------------------------
# Risk colours
# -----------------------------

def risk_color(score):

    if score < 20:
        return "green"
    elif score < 40:
        return "yellow"
    elif score < 60:
        return "orange"
    elif score < 80:
        return "red"
    else:
        return "darkred"


# -----------------------------
# Add grid cells
# -----------------------------

for _, row in map_data.iterrows():

    folium.GeoJson(
        row.geometry,
        style_function=lambda feature, score=row["final_risk_score"]: {
            "fillColor": risk_color(score),
            "color": "none",
            "weight": 0,
            "fillOpacity": 0.65
        },
        tooltip=folium.Tooltip(
            f"""
            Cell ID: {row['cell_id']}<br>
            Risk Score: {row['final_risk_score']:.2f}<br>
            Risk Class: {row['final_risk_class']}<br>
            Buildings: {row['building_count']}<br>
            Water Distance: {row['distance_to_water_m']:.0f} m
            """
        )
    ).add_to(m)


# -----------------------------
# Display map
# -----------------------------
st.subheader("Selected Risk Information")

if not map_data.empty:
    highest = map_data.loc[map_data["final_risk_score"].idxmax()]

    a, b, c, d = st.columns(4)

    a.metric("Risk Score", f"{highest['final_risk_score']:.1f}")
    b.metric("Risk Class", highest["final_risk_class"])
    c.metric("Buildings", int(highest["building_count"]))
    d.metric("Water Distance", f"{highest['distance_to_water_m']:.0f} m")
st_folium(
    m,
    width=1200,
    height=650
)
st.subheader("Risk Distribution")

risk_distribution = (
    grid["final_risk_class"]
    .value_counts()
    .reindex(
        ["Low", "Moderate", "High", "Very High", "Critical"],
        fill_value=0
    )
)

st.bar_chart(risk_distribution)
st.subheader("Highest Risk Areas")

display_columns = [
    "cell_id",
    "final_risk_class",
    "final_risk_score",
    "building_count",
    "water_proximity_score",
    "distance_to_water_m"
]

top_risk = (
    grid[display_columns]
    .sort_values("final_risk_score", ascending=False)
    .head(10)
)

st.dataframe(
    top_risk,
    use_container_width=True,
    hide_index=True
)

# -----------------------------
# Legend
# -----------------------------

st.markdown("""
### Risk Levels

🟢 **Low** &nbsp;&nbsp;
🟡 **Moderate** &nbsp;&nbsp;
🟠 **High** &nbsp;&nbsp;
🔴 **Very High** &nbsp;&nbsp;
🟥 **Critical**
""")

st.markdown("---")

st.subheader("About ResilienceMap")

st.write(
    "ResilienceMap is a GIS-based disaster risk assessment prototype "
    "for Kamrup Metropolitan. It combines proximity to waterways, "
    "building exposure, and vulnerability factors to generate a "
    "cell-level risk score."
)