// Función para calcular NDVI
function calcularNDVI(imagen) {
  var ndvi = imagen.normalizedDifference(['B8', 'B4']).rename('NDVI');
  return imagen.addBands(ndvi);
}

// Definir la región de Colombia
var colombia = ee.FeatureCollection('FAO/GAUL/2015/level0')
  .filter(ee.Filter.eq('ADM0_NAME', 'Colombia'));

// Obtener los departamentos de Colombia (nivel 1)
var departamentos = ee.FeatureCollection('FAO/GAUL/2015/level1')
  .filter(ee.Filter.eq('ADM0_NAME', 'Colombia'));

// Filtrar imágenes Sentinel-2 para Colombia (período seco para mejor visualización)
var sentinel2 = ee.ImageCollection('COPERNICUS/S2_SR_HARMONIZED')
  .filterBounds(colombia)
  .filterDate('2023-12-01', '2024-03-31') // Período seco en Colombia
  .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 10))
  .map(calcularNDVI);

// Crear un mosaico con la mediana de NDVI
var ndviMediana = sentinel2.select('NDVI').median();

// Aplicar máscara para solo mantener valores dentro de Colombia
var ndviColombia = ndviMediana.clip(colombia);

// Paletas de colores personalizadas para resaltar diferentes tipos de vegetación
var paletaTropical = [
  '#d73027', '#f46d43', '#fdae61', '#fee08b', 
  '#ffffbf', '#d9ef8b', '#a6d96a', '#66bd63', 
  '#1a9850', '#006837'
];

var paletaAndina = [
  '#8c510a', '#bf812d', '#dfc27d', '#f6e8c3',
  '#f5f5f5', '#c7eae5', '#80cdc1', '#35978f',
  '#01665e', '#003c30'
];

var paletaCosta = [
  '#4575b4', '#74add1', '#abd9e9', '#e0f3f8',
  '#ffffcc', '#fee090', '#fdae61', '#f46d43',
  '#d73027', '#a50026'
];

// Diferentes visualizaciones para resaltar aspectos específicos
var visNDVIBasico = {
  min: -0.2,
  max: 0.9,
  palette: ['red', 'yellow', 'green', 'darkgreen']
};

var visNDVITropical = {
  min: 0.0,
  max: 0.9,
  palette: paletaTropical,
  opacity: 0.8
};

var visNDVIAndino = {
  min: 0.1,
  max: 0.8,
  palette: paletaAndina,
  opacity: 0.9
};

var visNDVICosta = {
  min: -0.1,
  max: 0.7,
  palette: paletaCosta,
  opacity: 0.85
};

// Crear composiciones RGB con bandas que resalten la vegetación
var falsoColorInfrarrojo = {
  bands: ['B8', 'B4', 'B3'],
  min: 0,
  max: 3000,
  gamma: 1.4
};

var colorNatural = {
  bands: ['B4', 'B3', 'B2'],
  min: 0,
  max: 3000,
  gamma: 1.2
};

// Obtener una imagen reciente para RGB
var imagenReciente = sentinel2.sort('system:time_start', false).first();

// Centrar el mapa en Colombia con diferentes vistas
Map.centerObject(colombia, 6);

// Añadir capas al mapa
Map.addLayer(imagenReciente.clip(colombia), colorNatural, 'Color Natural', false);
Map.addLayer(imagenReciente.clip(colombia), falsoColorInfrarrojo, 'Falso Color Infrarrojo', false);

// Diferentes visualizaciones de NDVI
Map.addLayer(ndviColombia, visNDVIBasico, 'NDVI Básico', true);
Map.addLayer(ndviColombia, visNDVITropical, 'NDVI Tropical (Amazonía/Llanos)', false);
Map.addLayer(ndviColombia, visNDVIAndino, 'NDVI Andino (Montañas)', false);
Map.addLayer(ndviColombia, visNDVICosta, 'NDVI Costas (Caribe/Pacífico)', false);

// Añadir capa de límites de Colombia (frontera nacional)
Map.addLayer(colombia, {color: 'blue', fillColor: '00000000'}, 'Límites Colombia');

// Añadir capa de departamentos con líneas negras gruesas (SIN BOTÓN)
Map.addLayer(departamentos, 
  {color: 'black', fillColor: '00000000', width: 2.5}, 
  'Departamentos de Colombia'
);

// Añadir elevación
var elevacion = ee.Image('USGS/SRTMGL1_003').clip(colombia);
Map.addLayer(elevacion, {min: 0, max: 5000, palette: ['white', 'brown']}, 'Elevación', false);

// Crear leyenda interactiva
var leyenda = ui.Panel({
  style: {
    position: 'bottom-right',
    padding: '8px 15px'
  }
});

var leyendaTitulo = ui.Label({
  value: '🎯 NDVI Colombia - Leyenda',
  style: {
    fontWeight: 'bold',
    fontSize: '16px',
    margin: '0 0 4px 0',
    padding: '0'
    }
});

var leyendaItems = [
  {color: '#d73027', label: 'Sin vegetación/Agua (NDVI < 0)'},
  {color: '#f46d43', label: 'Vegetación escasa (0-0.2)'},
  {color: '#fdae61', label: 'Vegetación moderada (0.2-0.4)'},
  {color: '#a6d96a', label: 'Vegetación buena (0.4-0.6)'},
  {color: '#66bd63', label: 'Vegetación densa (0.6-0.8)'},
  {color: '#1a9850', label: 'Vegetación muy densa (>0.8)'}
];

leyenda.add(leyendaTitulo);

leyendaItems.forEach(function(item) {
  var colorBox = ui.Label({
    style: {
      backgroundColor: item.color,
      padding: '8px',
      margin: '0 0 4px 0'
    }
  });
  
  var description = ui.Label({
    value: item.label,
    style: {margin: '0 0 4px 6px'}
  });
  
  var holder = ui.Panel({
    widgets: [colorBox, description],
    layout: ui.Panel.Layout.Flow('horizontal')
  });
  
  leyenda.add(holder);
});

Map.add(leyenda);

// Mostrar información de los departamentos
print('🗺️ Departamentos de Colombia:', departamentos);
print('Número de departamentos:', departamentos.size());

// Estadísticas detalladas
print('📊 Estadísticas NDVI Colombia:', ndviColombia.reduceRegion({
  reducer: ee.Reducer.mean().combine({
    reducer2: ee.Reducer.stdDev(),
    sharedInputs: true
  }).combine({
    reducer2: ee.Reducer.minMax(),
    sharedInputs: true
  }),
  geometry: colombia,
  scale: 1000,
  maxPixels: 1e13
}));

// Mostrar información de la imagen
print('🛰️ Imagen utilizada:', imagenReciente);
print('📅 Período analizado: Diciembre 2023 - Marzo 2024');
