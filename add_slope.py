"""Add city slope fields (sl=AvgSlope %, z=zone code, la=gross lot sq ft) to site/parcels.geojson by APN.
Source: City of Belmont Estimated Slope layer (Elevation_GISi/MapServer/4). Cost fields are not touched."""
import json
src=json.load(open('site/parcels.v3.geojson'))
c={}
for f in json.load(open('slope/city_estimated_slope.geojson'))['features']:
    p=f['properties']; a=p['APN']
    if a in c and c[a]['AreaSF']>=p['AreaSF']: continue
    c[a]=p
n=0; zc={}
for f in src['features']:
    p=f['properties']; r=c.get(p['p'])
    if not r: continue
    p['sl']=round(r['AvgSlope'],3); p['z']=r['ZONECODE'] or ''; p['la']=int(round(r['AreaSF'])); n+=1
    zc[p['z']]=zc.get(p['z'],0)+1
json.dump(src,open('site/parcels.geojson','w'),separators=(',',':'))
print('joined',n,'of',len(src['features'])); print(dict(sorted(zc.items(),key=lambda x:-x[1])))
