import streamlit as st
import ee
import folium
from streamlit_folium import folium_static

# Función para autenticar e inicializar Earth Engine
def initialize_earth_engine():
    try:
        # Intenta autenticar e inicializar
        ee.Initialize()
    except Exception as e:
        # Si falla, autentica
        ee.Authenticate()
        ee.Initialize()

# Configuración de la página
st.set_page_config(page_title="Mapa Interactivo GEE", layout="wide")
st.title("Mapa de NDVI Global con Google Earth Engine")

# Inicializar Earth Engine
initialize_earth_engine()

# Función para calcular NDVI
def calculate_ndvi(image):
    ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI')
    return image.addBands(ndvi)

# Función para obtener imagen de NDVI
def get_ndvi_image():
    # Cargar colección de imágenes Landsat 8
    collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .filterDate('2023-01-01', '2023-12-31') \
        .filter(ee.Filter.lt('CLOUD_COVER', 20)) \
        .map(calculate_ndvi)
    
    # Crear un mosaico reduciendo la colección a la mediana
    median = collection.median()
    
    # Seleccionar la banda NDVI
    ndvi = median.select('NDVI')
    
    return ndvi

# Función para visualizar el mapa
def display_map(image, vis_params, center_lat=0, center_lon=0, zoom=2):
    map_dict = image.getMapId(vis_params)
    map = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)
    
    folium.TileLayer(
        tiles=map_dict['tile_fetcher'].url_format,
        attr='Google Earth Engine',
        overlay=True,
        name='NDVI'
    ).add_to(map)
    
    # Añadir control de capas
    folium.LayerControl().add_to(map)
    
    # Mostrar el mapa en Streamlit
    folium_static(map, width=1000, height=600)

# Interfaz de usuario
st.sidebar.header("Configuración del Mapa")

# Selección de fecha
start_date = st.sidebar.date_input("Fecha de inicio", value=ee.Date('2023-01-01').format().getInfo())
end_date = st.sidebar.date_input("Fecha de fin", value=ee.Date('2023-12-31').format().getInfo())

# Parámetros de visualización
min_ndvi = st.sidebar.slider("NDVI mínimo", -1.0, 0.0, -0.2)
max_ndvi = st.sidebar.slider("NDVI máximo", 0.0, 1.0, 0.8)
opacity = st.sidebar.slider("Opacidad", 0.0, 1.0, 0.7)

# Paleta de colores
palette = st.sidebar.text_input("Paleta de colores (separada por comas)", 
                              "red, yellow, green")

# Crear parámetros de visualización
vis_params = {
    'min': min_ndvi,
    'max': max_ndvi,
    'palette': palette.split(','),
    'opacity': opacity
}

# Obtener la imagen de NDVI
ndvi_image = get_ndvi_image()

# Mostrar el mapa
st.subheader("Mapa de NDVI Global")
display_map(ndvi_image, vis_params)

# Información adicional
st.markdown("""
### Acerca de este mapa
- **NDVI (Índice de Vegetación de Diferencia Normalizada)**: 
  Es un indicador de la presencia y estado de la vegetación. 
  Valores cercanos a 1 indican vegetación densa y saludable, 
  mientras que valores negativos pueden indicar agua.
- **Datos**: Imágenes Landsat 8 procesadas en Google Earth Engine.
- **Periodo**: Enero a Diciembre 2023.
""")
