# Librerías
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import geopandas as gpd
from geopandas import GeoSeries
from shapely.geometry import Point, LineString
import os
import streamlit as st
import folium
from folium import Choropleth, LayerControl
from streamlit_folium import folium_static

# Cargar los datos

# Cargar el Excel descargado
df = pd.read_excel("data/listado_iiee.xlsx")

# Cargar shapefile de distritos
gdf_distritos = gpd.read_file("data/shape_file/DISTRITOS.shp")

# Configurar página de Streamlit
st.set_page_config(page_title="Análisis Geoespacial de Colegios en Perú", layout="wide")

# Tabs
tab1, tab2, tab3 = st.tabs(["🗂️ Descripción de Datos", "🗺️ Mapas Estáticos", "🌍 Mapas Dinámicos"])

# Tab 1: Descripción de datos


with tab1:
    st.header("🗂️ Descripción de Datos")

    st.subheader("Unidad de Análisis")
    st.write("""
    La unidad de análisis de este proyecto es cada escuela en el Perú.
    Cada colegio está tiene un código único que ayuda a identificarlo, además contiene información sobre sus coordenadas (latitud y longitud) y su nivel educativo (Inicial, Primaria o Secundaria).
    El análisis espacial agrupa a los colegios a nivel distrital para observar patrones de acceso educativo en el ámbito distrital.
    """)

    st.subheader("Fuentes de Datos")
    st.write("""
    - **Base de datos de escuelas**: Ministerio de Educación del Perú (MINEDU), obtenido del portal SIGMED (https://sigmed.minedu.gob.pe/mapaeducativo/).
    - **Shapefile de límites distritales**: Fuente oficial del Instituto Nacional de Estadística e Informática (INEI).
    """)

    st.subheader("Supuestos y Preprocesamiento")
    st.write("""
    - Se eliminaron duplicados, registros incompletos o inconsistentes.             
    - Solo se incluyeron colegios que cuentan con coordenadas geográficas válidas y completas.
    - La distancia al colegio más cercano fue estimada en línea recta ("distancia euclidiana") según los datos disponibles.
    - Se agruparon los colegios según 3 niveles de educación: Inicial, Primaria y Secundaria.
    """)


# Convertimos a minúsculas para evitar problemas con mayúsculas/minúsculas
df['nivel_lower'] = df['Nivel / Modalidad'].str.lower()

# Filtros más controlados
filtro_inicial = df['nivel_lower'].str.contains('inicial')
filtro_primaria = df['nivel_lower'].str.contains('primaria')
filtro_secundaria = df['nivel_lower'].str.contains('secundaria')

# Aplicar filtros
df_inicial = df[filtro_inicial]
df_primaria = df[filtro_primaria]
df_secundaria = df[filtro_secundaria]

# Agrupar colegios según nivel educativo para cada distrito
inicial_count = df_inicial.groupby(['Departamento', 'Provincia', 'Distrito']).size().reset_index(name='n_inicial')
primaria_count = df_primaria.groupby(['Departamento', 'Provincia', 'Distrito']).size().reset_index(name='n_primaria')
secundaria_count = df_secundaria.groupby(['Departamento', 'Provincia', 'Distrito']).size().reset_index(name='n_secundaria')

# Unir la geometría de los distritos con los datos de las escuelas por nivel reemplazando NaN por 0
gdf_inicial = gdf_distritos.merge(inicial_count, left_on=['DEPARTAMEN', 'PROVINCIA', 'DISTRITO'], right_on=['Departamento', 'Provincia', 'Distrito'], how='left').fillna({'n_inicial': 0})
gdf_primaria = gdf_distritos.merge(primaria_count, left_on=['DEPARTAMEN', 'PROVINCIA', 'DISTRITO'], right_on=['Departamento', 'Provincia', 'Distrito'], how='left').fillna({'n_primaria': 0})
gdf_secundaria = gdf_distritos.merge(secundaria_count, left_on=['DEPARTAMEN', 'PROVINCIA', 'DISTRITO'], right_on=['Departamento', 'Provincia', 'Distrito'], how='left').fillna({'n_secundaria': 0})


# Tab 2: Mapas Estáticos

# Recorremos y graficamos cada uno
with tab2:
    # Diccionario con los GeoDataFrames y sus respectivas columnas y títulos
    mapas = {
        "Inicial": {"gdf": gdf_inicial, "columna": "n_inicial", "titulo": "Distribución de Escuelas Iniciales por Distrito en Perú"},
        "Primaria": {"gdf": gdf_primaria, "columna": "n_primaria", "titulo": "Distribución de Escuelas Primarias por Distrito en Perú"},
        "Secundaria": {"gdf": gdf_secundaria, "columna": "n_secundaria", "titulo": "Distribución de Escuelas Secundarias por Distrito en Perú"},
    }

    st.header("🗺️ Mapas Estáticos")

    for nivel, info in mapas.items():
        fig, ax = plt.subplots(1, 1, figsize=(12, 10))
        info["gdf"].plot(
            column=info["columna"],
            cmap='Reds',
            ax=ax,
            legend=True,
            edgecolor='black',
            legend_kwds={'label': f"Cantidad de Escuelas {nivel}"},
            linewidth=0.5
        )

        ax.set_title(info["titulo"], fontsize=16)
        ax.axis('off')
        st.pyplot(fig)


# Tab 3: Mapas Dinámicos

with tab3:
    
    # Asegurar de que esté en EPSG:4326 para usar con Folium
    gdf_distritos = gdf_distritos.to_crs(epsg=4326)

    # Convertir a minúsculas para evitar problemas con mayúsculas/minúsculas
    df['nivel_lower'] = df['Nivel / Modalidad'].str.lower()

    # Filtros más controlados
    filtro_inicial = df['nivel_lower'].str.contains('inicial')
    filtro_primaria = df['nivel_lower'].str.contains('primaria')
    filtro_secundaria = df['nivel_lower'].str.contains('secundaria')

    # Aplicar filtros
    df_inicial = df[filtro_inicial]
    df_primaria = df[filtro_primaria]
    df_secundaria = df[filtro_secundaria]

    # Crear GeoDataFrames por nivel
    gdf_inicial = gpd.GeoDataFrame(df_inicial, geometry=gpd.points_from_xy(df_inicial['Longitud'], df_inicial['Latitud']), crs="EPSG:4326")
    gdf_primaria = gpd.GeoDataFrame(df_primaria, geometry=gpd.points_from_xy(df_primaria['Longitud'], df_primaria['Latitud']), crs="EPSG:4326")
    gdf_secundaria = gpd.GeoDataFrame(df_secundaria, geometry=gpd.points_from_xy(df_secundaria['Longitud'], df_secundaria['Latitud']), crs="EPSG:4326")

    # Contar por Ubigeo
    conteo_inicial = gdf_inicial.groupby('Ubigeo').size().reset_index(name='inicial')
    conteo_primaria = gdf_primaria.groupby('Ubigeo').size().reset_index(name='primaria')
    conteo_secundaria = gdf_secundaria.groupby('Ubigeo').size().reset_index(name='secundaria')

    # Cambiar nombre IDDIST por Ubigeo para hacer el merge
    gdf_distritos['Ubigeo'] = (gdf_distritos['IDDIST'].astype(str).str.zfill(2))

    # Asegurar que los Ubigeos en conteos sean string
    conteo_inicial['Ubigeo'] = conteo_inicial['Ubigeo'].astype(str)
    conteo_primaria['Ubigeo'] = conteo_primaria['Ubigeo'].astype(str)
    conteo_secundaria['Ubigeo'] = conteo_secundaria['Ubigeo'].astype(str)

    # Asegurar sistema de coordenadas compatible
    gdf_distritos = gdf_distritos.to_crs(epsg=4326)

    # Unir conteos al shapefile
    gdf_mapa = gdf_distritos.merge(conteo_inicial, on='Ubigeo', how='left')
    gdf_mapa = gdf_mapa.merge(conteo_primaria, on='Ubigeo', how='left')
    gdf_mapa = gdf_mapa.merge(conteo_secundaria, on='Ubigeo', how='left')

    # Rellenar NaN con 0
    for col in ['inicial', 'primaria', 'secundaria']:
        gdf_mapa[col] = gdf_mapa[col].fillna(0)

    # Diccionario con los GeoDataFrames y sus respectivas columnas y títulos
    mapas = {
        "Inicial": {"gdf": gdf_inicial, "columna": "n_inicial", "titulo": "Distribución de Escuelas Iniciales por Distrito en Perú"},
        "Primaria": {"gdf": gdf_primaria, "columna": "n_primaria", "titulo": "Distribución de Escuelas Primarias por Distrito en Perú"},
        "Secundaria": {"gdf": gdf_secundaria, "columna": "n_secundaria", "titulo": "Distribución de Escuelas Secundarias por Distrito en Perú"},
    }

    st.header("🌍 Mapas Dinámicos")

    st.subheader("Distribución de colegios por nivel educativo (mapa interactivo)")

    # Simplifica geometrías
    gdf_mapa["geometry"] = gdf_mapa["geometry"].simplify(tolerance=0.01, preserve_topology=True)

    # Crear el mapa base centrado en Perú (ajusta según coordenadas promedio de tu shapefile)
    m = folium.Map(location=[-9.19, -75.02], zoom_start=5)

    # Diccionario de niveles con sus configuraciones
    levels = {
        "inicial": {"color": "YlGnBu", "legend": "Nivel Inicial"},
        "primaria": {"color": "YlOrRd", "legend": "Nivel Primaria"},
        "secundaria": {"color": "BuPu", "legend": "Nivel Secundaria"}
    }

    # Crear cada Choropleth
    for level, config in levels.items():
        folium.Choropleth(
            geo_data=gdf_mapa,
            name=f"choropleth_{level}",
            data=gdf_mapa,
            columns=['Ubigeo', level],
            key_on='feature.properties.Ubigeo',
            fill_color=config["color"],
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name=config["legend"],
        ).add_to(m)

    # Añadir control de capas
    LayerControl(collapsed=False).add_to(m)

    folium_static(m, width=1200, height=700)