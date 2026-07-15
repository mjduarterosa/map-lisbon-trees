# import libraries
import pandas as pd
import folium
import streamlit as st
from streamlit.components.v1 import html
from folium.plugins import FastMarkerCluster
from pathlib import Path

# configure the Streamlit app layout to be wide
st.set_page_config(layout="wide")

# load data from CSV file and cache it to avoid reloading on every interaction
@st.cache_data
def load_data():
    csv_path = Path(__file__).resolve().parent.parent / "data" / "arvoredo_cleaned.csv"
    return pd.read_csv(csv_path)

with st.spinner("Loading tree dataset..."):
    df = load_data()

# replace NaNs
df = df.fillna("Nao id.")

# optimize data (if needed)
df_minimal = df

# round coordinates to 4 decimals (still city-accurate)
df_minimal['latitude'] = df_minimal['latitude'].round(4)
df_minimal['longitude'] = df_minimal['longitude'].round(4)

# create title of app
st.title("🌳 Árvores de Lisboa 🌳 ")
st.subheader("Aplicação para visualização do inventário das árvores em espaços públicos da cidade de Lisboa.")
st.markdown("Fonte: Avoredo, Câmara Municipal de Lisboa: [Arvoredo - Portal Dados Abertos](https://dadosabertos.cm-lisboa.pt/fr/dataset/arvoredo) (5 May 2026, 10:53 (UTC+01:00))")

# create form to wrap the dropdown menus in a box
with st.form("filter_form"):
    # create four columns for the menus
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        tile = st.selectbox(
            "🗺️ Tipo de Mapa",
            [
                "CartoDB Voyager",
                "CartoDB Positron",
                "OpenStreetMap",
                "Esri.WorldImagery"
            ]
        )

        st.write("")
        st.write("")
        st.form_submit_button("Aplicar Filtros", key="apply_filters")

    # get unique Local options
    local_options = sorted(df_minimal['Local'].unique().tolist())
    local_options.insert(0, "Todos")  # Add "All Locations" as first option

    # get unique Freguesia options
    freguesia_options = sorted(df_minimal['Freguesia'].astype(str).unique().tolist())
    freguesia_options.insert(0, "Todos")

    # get top 10 most common common names, excluding missing values
    common_name_counts = (
        df_minimal['Nome Vulgar']
        .replace("Nao id.", pd.NA)
        .dropna()
        .value_counts()
        .head(50)
    )
    common_name_options = ["Todos"] + common_name_counts.index.tolist()

    with col2:
        selected_common_name = st.selectbox(
            "🌿 Filtrar por Nome Comum (top 50)",
            common_name_options
        )

    with col3:
        selected_freguesia = st.selectbox(
            "🏛️ Filtrar por Freguesia",
            freguesia_options
        )

        manutencao_options = sorted(df_minimal['Manutenção'].astype(str).unique().tolist())
        manutencao_options.insert(0, "Todos")
        selected_manutencao = st.selectbox(
            "🔧 Filtrar por Manutenção",
            manutencao_options
        )

    with col4:
        selected_local = st.selectbox(
            "🏫 Filtrar por Local",
            local_options
        )

        ocupacao_options = sorted(df_minimal['Ocupação'].astype(str).unique().tolist())
        ocupacao_options.insert(0, "Todos")
        selected_ocupacao = st.selectbox(
            "🌱 Filtrar por Ocupação",
            ocupacao_options
        )

# add more info text
st.caption("No mapa, clique no ícone da árvore para mais informações sobre essa árvore (incluindo a espécie).")

# filter data based on the selected dropdown values
df_filtered = df_minimal

if selected_local != "Todos":
    df_filtered = df_filtered[df_filtered['Local'] == selected_local]

if selected_common_name != "Todos":
    df_filtered = df_filtered[df_filtered['Nome Vulgar'] == selected_common_name]

if selected_manutencao != "Todos":
    df_filtered = df_filtered[df_filtered['Manutenção'] == selected_manutencao]

if selected_ocupacao != "Todos":
    df_filtered = df_filtered[df_filtered['Ocupação'] == selected_ocupacao]

if selected_freguesia != "Todos":
    df_filtered = df_filtered[df_filtered['Freguesia'] == selected_freguesia]

if df_filtered.empty:
    st.warning("Zero árvores encontradas. Por favor, selecionar novos filtros.")
    map_center = [38.7223, -9.1393]
    coords = []
else:
    map_center = [df_filtered["latitude"].mean(), df_filtered["longitude"].mean()]
    coords = df_filtered[["latitude", "longitude", "Espécie", "Nome Vulgar", "Local", 
                          "Freguesia", "Morada", "Manutenção", "Ocupação", "Tipologia"]].values.tolist()

m = folium.Map(location=map_center, zoom_start=12, tiles=tile)

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
    '<b>Espécie:</b> ' + row[2] + '<br><b>Nome Vulgar:</b> ' + row[3] + '<br><b>Local:</b> ' 
    + row[4] + '<br><b>Freguesia:</b> ' + row[5] + '<br><b>Morada:</b> ' + row[6] 
    + '<br><b>Manutenção:</b> ' + row[7] + '<br><b>Ocupação:</b> ' + row[8] + '<br><b>Tipologia:</b> ' + row[9]
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
if coords:
    fast_cluster = FastMarkerCluster(
        coords,
        name="Lisbon Trees",
        callback=callback,
        icon_create_function=icon_create_function,
    )

    # add the FastMarkerCluster to the map
    fast_cluster.add_to(m)
else:
    folium.Marker(
        location=map_center,
        popup="Zero árvores encontradas. Por favor, selecionar novos filtros.",
        icon=folium.Icon(color="gray")
    ).add_to(m)

# display map
html(
    m.get_root().render(),
    width=1400,
    height=800,
    scrolling=False,
)

# add contact information
st.divider()
st.caption("Contacto: M. J. Duarte Rosa | 📧 mdr.datascience AT gmail")