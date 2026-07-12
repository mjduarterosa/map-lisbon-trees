# import libraries
import pandas as pd
import folium
import streamlit as st
from streamlit.components.v1 import html
from streamlit.components.v1 import html
from pathlib import Path

# configure the Streamlit app layout to be wide
st.set_page_config(layout="wide")

# load the CSV file into a DataFrame
csv_path = Path(__file__).resolve().parent.parent / "data" / "arvoredo_cleaned.csv"
df = pd.read_csv(csv_path)
df.head()

df = df.fillna("Nao indentificada")
counts = df.isna().sum()

# optimize data
# keep only essential columns
df_minimal = df[['latitude', 'longitude', 'Nome Vulgar', 'Espécie', 'Local']].copy()

# round coordinates to 4 decimals (still city-accurate)
df_minimal['latitude'] = df_minimal['latitude'].round(4)
df_minimal['longitude'] = df_minimal['longitude'].round(4)

# create title of app
st.title("Mapa de Arvores")

# Create form to wrap the dropdown menus in a box
with st.form("filter_form"):
    # Create two columns for the menus
    col1, col2 = st.columns(2)

    with col1:
        tile = st.selectbox(
            "Basemap",
            [
                "CartoDB Voyager",
                "CartoDB Positron",
                "OpenStreetMap",
                "Esri.WorldImagery"
            ]
        )

    # Get unique Local options
    local_options = sorted(df_minimal['Local'].unique().tolist())
    local_options.insert(0, "All Locations")  # Add "All Locations" as first option

    with col2:
        selected_local = st.selectbox(
            "Filter by Local",
            local_options
        )
    
    st.form_submit_button("Apply Filters")

# create a map centered on the average coordinates of the trees
from folium.plugins import FastMarkerCluster

# Filter data based on selected Local
if selected_local == "All Locations":
    df_filtered = df_minimal
else:
    df_filtered = df_minimal[df_minimal['Local'] == selected_local]

map_center = [df_filtered["latitude"].mean(), df_filtered["longitude"].mean()]
m = folium.Map(location=map_center, zoom_start=12, tiles=tile)

coords = df_filtered[["latitude", "longitude", "Espécie", "Nome Vulgar", "Local"]].values.tolist()

# change icon to leaf and add species name to popup
callback = """
function (row) {

    var icon = L.AwesomeMarkers.icon({
        icon: 'leaf',
        prefix: 'fa',
        markerColor: 'green'
    });

    var marker = L.marker(
        [row[0], row[1]],
        {icon: icon}
    );

    marker.bindPopup(
    '<b>Espécie:</b> ' + row[2] + '<br><b>Nome Vulgar:</b> ' + row[3] + '<br><b>Local:</b> ' + row[4]
    );

    return marker;
}
"""
# change icon colour
icon_create_function = """
function(cluster) {
    var childCount = cluster.getChildCount();
    var c = ' marker-cluster-large';

    if (childCount < 5) {
        c = ' marker-cluster-small';
    } else if (childCount < 20) {
        c = ' marker-cluster-medium';
    }

    return new L.DivIcon({
        html: '<div><span>' + childCount + '</span></div>',
        className: 'marker-cluster' + c,
        iconSize: new L.Point(40, 40)
    });
}
"""

# add CSS for colours
css = """
<style>
.marker-cluster-small {
    background-color: rgba(232,245,233,0.6);
}
.marker-cluster-small div {
    background-color: rgba(232,245,233,0.9);
    color: #1b5e20;
}

.marker-cluster-medium {
    background-color: rgba(200,230,201,0.6);
}
.marker-cluster-medium div {
    background-color: rgba(200,230,201,0.9);
    color: #1b5e20;
}

.marker-cluster-large {
    background-color: rgba(102,187,106,0.6);
}
.marker-cluster-large div {
    background-color: rgba(27,94,32,0.9);
    color: white;
}
</style>
"""

# add the CSS to the map
m.get_root().html.add_child(folium.Element(css))


# create cluster map
fast_cluster = FastMarkerCluster(
    coords,
    name="Lisbon Trees",
    callback=callback,
    icon_create_function=icon_create_function,
)

# add the FastMarkerCluster to the map
fast_cluster.add_to(m)

# additional basemaps
#folium.TileLayer(
#    "CartoDB Positron",
#    name="Light Map"
#).add_to(m)

#folium.TileLayer(
#    "CartoDB Voyager",
#    name="Voyager"
#).add_to(m)

#folium.TileLayer(
#    "Esri.WorldImagery",
#    name="Satellite"
#).add_to(m)

#folium.LayerControl(position="topright").add_to(m)

# display map
html(
    m.get_root().render(),
    width=1400,
    height=800,
    scrolling=False,
)