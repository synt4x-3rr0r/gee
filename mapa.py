import streamlit as st
import ee
import folium
from streamlit_folium import folium_static

# Configuración especial para Streamlit Cloud
try:
    ee.Initialize()
except:
    # Esto solo funciona si ya te autenticaste previamente
    ee.Authenticate()
    ee.Initialize()

# Configuración de la página
st.set_page_config(page_title="Mapa NDVI Interactivo", layout="wide")
st.title("🌍 Mapa de NDVI Global con Google Earth Engine")

# Función para calcular NDVI
def calculate_ndvi(image):
    ndvi = image.normalizedDifference(['B5', 'B4']).rename('NDVI')
    return image.addBands(ndvi)

# Función para obtener imagen de NDVI
def get_ndvi_image(start_date, end_date):
    # Cargar colección de imágenes Landsat 8
    collection = ee.ImageCollection('LANDSAT/LC08/C02/T1_L2') \
        .filterDate(start_date, end_date) \
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
st.sidebar.header("⚙️ Configuración del Mapa")

# Selección de fecha
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input("Fecha de inicio", value=ee.Date('2023-01-01').format().getInfo())
with col2:
    end_date = st.date_input("Fecha de fin", value=ee.Date('2023-12-31').format().getInfo())

# Parámetros de visualización
st.sidebar.subheader("Ajustes Visuales")
min_ndvi = st.sidebar.slider("NDVI mínimo", -1.0, 0.0, -0.2, 0.01)
max_ndvi = st.sidebar.slider("NDVI máximo", 0.0, 1.0, 0.8, 0.01)
opacity = st.sidebar.slider("Opacidad", 0.0, 1.0, 0.7, 0.05)

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
try:
    ndvi_image = get_ndvi_image(str(start_date), str(end_date))
    
    # Mostrar el mapa
    st.subheader("🗺️ Mapa de NDVI")
    with st.spinner('Generando mapa...'):
        display_map(ndvi_image, vis_params)
    
    # Información adicional
    st.markdown("""
    ### 📊 Acerca de este mapa
    - **NDVI (Índice de Vegetación de Diferencia Normalizada)**: 
      Es un indicador de la presencia y estado de la vegetación. 
      Valores cercanos a 1 indican vegetación densa y saludable, 
      mientras que valores negativos pueden indicar agua.
    - **📅 Periodo**: {} a {}
    - **🛰️ Datos**: Imágenes Landsat 8 procesadas en Google Earth Engine
    """.format(start_date, end_date))

except Exception as e:
    st.error(f"Error al cargar los datos: {str(e)}")
    st.info("Asegúrate de que las fechas seleccionadas tengan datos disponibles")

# Nota sobre autenticación
st.sidebar.markdown("---")
st.sidebar.info("""
⚠️ **Nota sobre autenticación**:  
Para que funcione en Streamlit Cloud, debes:
1. Ejecutar localmente primero para autenticarte
2. Subir las credenciales generadas
""")
