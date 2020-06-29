var geometry = /* color: #9cd6d1 */ee.Geometry.Polygon(
        [[[-67.18452148437501, -18.33167913708429],
          [-67.22572021484376, -18.44114671217198],
          [-67.40699462890626, -18.503668342951727],
          [-67.39600830078126, -18.64165599530168],
          [-67.45917968750001, -18.81333299514085],
          [-67.22572021484376, -18.930285201197258],
          [-67.19276123046876, -19.086094131165932],
          [-67.09937744140626, -19.171726675617403],
          [-66.99226074218751, -19.202854764725164],
          [-66.83845214843751, -19.14318742747399],
          [-66.76978759765626, -18.917294544116373],
          [-66.87141113281251, -18.763928713820363],
          [-66.88514404296876, -18.63905348928365],
          [-66.92359619140626, -18.451568566162894],
          [-66.96204833984376, -18.36817605084907],
          [-67.11585693359376, -18.316035243323885]]]);

var dateSTART = ee.Date.fromYMD(2020,5,8);
//var dateSTART = ee.Date.fromYMD(2020,5,1);
var dateEND =  ee.Date.fromYMD(2020,6,25);


var dataset = ee.ImageCollection('LANDSAT/LC08/C01/T1_32DAY_NDWI')
//var dataset = ee.ImageCollection('LANDSAT/LC08/C01/T1_8DAY_NDWI')
                  .filterDate(dateSTART, dateEND);
//               .filterBounds(geometry);

var datandwi = dataset.select('NDWI');

var colorizedVis = {
  min: 0.5,
  max: 1.0,
  palette: ['33ffff', '0055ff','0000ff'],
};


var waterfunction = function(image){
  var wm = image.gt(0.5);
    return image.updateMask(wm).set('system:time_start', image.get('system:time_start'));
};

var lakemask =datandwi.map(waterfunction);



var createTS = function(img){
  var date = img.get('system:time_start');
  
  var value = img.select("NDWI")
                 .reduceRegion({
                    geometry: geometry,
                    reducer: ee.Reducer.count(), 
                    scale: 30
                      })
                 .get("NDWI")
  
  var dataN = ee.Number(value)

  var ft = ee.Feature(null, {'date': ee.Date(date).format("dd-MM-yyyy"), 
                             'value': dataN });
  return ft;
};


var TS = lakemask.map(createTS);

print (TS)


var exportCSV = false
// Export the time-series as a csv.
if (exportCSV) {
  Export.table.toDrive({
    
    folder:'RDI-timeseries',
    description: 'Popoo-px30m',
    fileFormat: 'CSV',
    collection: TS, selectors: 'date, value'
    
  });
  }


var numberImages = lakemask.size()

var lakemaskList = lakemask.toList(numberImages)

print (lakemaskList)

var n = lakemaskList.size().getInfo();


for (var i = 0; i < n ; i++) {  
  
      var image = ee.Image(lakemaskList.get(i));
      var date = ee.Date(image.get('system:time_start')).format("yyyyMMdd").getInfo();
      
      var name = "NDWI-Popoo_" + date
      
      Map.addLayer(image, colorizedVis, 'Colorized');

      Export.image.toDrive({
              image: image,
              description: name,
              crs: 'EPSG:4326',
              scale: 30,
              region: geometry,
              fileFormat: 'GeoTIFF',
              skipEmptyTiles  : "True",
              folder: "NDWI-Poopo-05"

                  });
      
      };
//Map.addLayer(image, colorizedVis, 'Colorized');



Map.setCenter(-66.80, -18.87, 9.5);
Map.addLayer(lakemask.max(), colorizedVis, 'Colorized');
var chartndwi=ui.Chart.image.series({
  imageCollection: lakemask,
  region: geometry,
  reducer: ee.Reducer.count(),
  scale: 30
}).setOptions({title:'Landsat NDWI'});
print(chartndwi);

