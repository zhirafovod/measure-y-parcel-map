# Belmont lot slope / allowable floor area — research (NOT published)

## Existing official source (use this)
- City of Belmont "Estimated Slope" layer, AvgSlope per parcel (8,359 parcels, APN key):
  https://maps.belmont.gov/arcgis/rest/services/Elevation_GISi/MapServer/4  (also OpenData/OpenData/MapServer/14, CSCD/CSCDLayers/MapServer/13)
  Fields: APN, AreaSF, Con_INT (=5 ft for all), Con_LEN, AvgSlope, ZONECODE, LUCODE, EasyAddr. Queryable as GeoJSON, 1000/page.
  AvgSlope = 0.00229 x I x L / acres (verified on 99.98% of rows) -> the code's contour method, using GROSS parcel area.
- Viewer apps: Belmont Elevation Viewer https://belmontca.maps.arcgis.com/apps/Elevations/index.html?appid=4d47ad9ea5d4497aa8aa4fd287f4239b ;
  Elevation Search https://belmontca.maps.arcgis.com/apps/Viewer/index.html?appid=53d9b407558649e7be12521f8ee882e6 ; linked from https://www.belmont.gov/our-city/city-maps
- 5-ft contours: OpenData/OpenData/MapServer/13 (Elevation_GISi/MapServer/3)

## Files
- city_estimated_slope.geojson  city layer (owner/mailing fields excluded), 6.8 MB
- belmont_3dep_1m_dm.tif        USGS 3DEP 1 m bare-earth DEM, int16 decimeters, UTM10N (EPSG:26910)
- belmont_slope_pct_1m.tif      slope % (uint8, capped 254)
- parcel_slope_compare.json     per parcel: city AvgSlope vs 3DEP mean/median slope, relief (ft)
- r1_floor_area.json            R-1 parcels: slope, Table 4 FAR, slope-based FA, Table 5 cap, max allowed GFA, our est. sqft
- slope_stats.json, map_*.png, scatter_city_vs_3dep.png
- src/  Belmont zoning text extracts (Section 4, granicus copies, "current through Ord. 2018-1133")
