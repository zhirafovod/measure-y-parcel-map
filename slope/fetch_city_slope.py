import json,urllib.request,urllib.parse
B="https://maps.belmont.gov/arcgis/rest/services/Elevation_GISi/MapServer/4/query"
flds="OBJECTID,APN,AreaSF,Con_INT,Con_LEN,AvgSlope,GISacre,NumConInt,PUC_CODE,LUCODE,LU_DESC,ZONECODE,ZONE_DESC,EasyAddr,NeighName"
feats=[];off=0
while True:
    q=dict(where="1=1",outFields=flds,outSR=4326,f="geojson",resultOffset=off,resultRecordCount=1000,orderByFields="OBJECTID",geometryPrecision=6)
    d=json.load(urllib.request.urlopen(B+"?"+urllib.parse.urlencode(q),timeout=120))
    fs=d["features"];feats+=fs;off+=len(fs);print(off)
    if len(fs)<1000: break
json.dump({"type":"FeatureCollection","features":feats},open("city_estimated_slope.geojson","w"))
