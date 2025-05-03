# --- Librerías necesarias ---
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
df = pd.read_excel(".../data/listado_iiee.xlsx")

# Cargar shapefile de distritos
gdf_distritos = gpd.read_file(".../data\shape_file\DISTRITOS.shp")

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

# Tab 2: Mapas Estáticos

with tab2:
    st.header("🗺️ Mapas Estáticos")

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

# Crear el mapa para Inicial
fig, ax = plt.subplots(1, 1, figsize=(12, 10))
gdf_inicial.plot(column='n_inicial', cmap='Reds', ax=ax, legend=True,
                 edgecolor='black',
                 legend_kwds={'label': "Cantidad de Escuelas Iniciales"}, 
                 linewidth=0.5)
ax.set_title('Distribución de Escuelas Iniciales por Distrito en Perú')

# Crear el mapa para Primaria
fig, ax = plt.subplots(1, 1, figsize=(12, 10))
gdf_primaria.plot(column='n_primaria', cmap='Reds', ax=ax, legend=True,
                 edgecolor='black',
                 legend_kwds={'label': "Cantidad de Escuelas Primarias"}, 
                 linewidth=0.5)
ax.set_title('Distribución de Escuelas Primarias por Distrito en Perú')

# Crear el mapa para Secundaria
fig, ax = plt.subplots(1, 1, figsize=(12, 10))
gdf_secundaria.plot(column='n_secundaria', cmap='Reds', ax=ax, legend=True,
                 edgecolor='black',
                 legend_kwds={'label': "Cantidad de Escuelas Secundarias"}, 
                 linewidth=0.5
                 )

ax.set_title(f'Distribución de colegios - Nivel {nivel.capitalize()}', fontsize=16)
ax.axis('off')
st.pyplot(fig)