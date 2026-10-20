import json, geopandas as gpd, pandas as pd, numpy as np
from shapely.geometry import shape
D='data/'
j=json.load(open(D+'JURISDICTIONAL_BOUNDARIES_GEOJSON/JURISDICTIONAL_BOUNDARIES_GEOJSON.json'))
city=j[0]; crs=city['crs']['properties']['name'] if city.get('crs') else 'EPSG:2227'
bel=[f for f in city['features'] if f['properties'].get('COMMONNAME','').upper()=='BELMONT' and not f['properties'].get('UNINCORPORATED')]
print('belmont feats',len(bel),[f['properties'] for f in bel], crs)
bgeom=gpd.GeoDataFrame(geometry=[shape(f['geometry']) for f in bel],crs=crs).to_crs(2227)
bb=tuple(bgeom.total_bounds)
P=gpd.read_file(D+'SAN_MATEO_COUNTY_ACTIVE_PARCELS/SAN_MATEO_COUNTY_ACTIVE_PARCELS.shp',bbox=bb).to_crs(2227)
cent=P.copy(); cent['geometry']=P.representative_point()
inside=gpd.sjoin(cent,bgeom,predicate='within',how='inner').index
P=P.loc[inside].copy()
print('parcels in Belmont',len(P), P.SITUS_CITY.value_counts().head())
B=gpd.read_file(D+'BUILDING_FOOTPRINTS/GIS_ADMIN.BUILDING_FOOTPRINTS.shp',bbox=bb).to_crs(2227)
B['geometry']=B.geometry.force_2d() if hasattr(B.geometry,'force_2d') else B.geometry
B['h']=(B.BUILDING_E-B.BASE_ELEV).clip(lower=0)
print('footprints',len(B), B.h.describe())
# stacked parcels (condos): group identical geometry
P['gkey']=P.geometry.apply(lambda g: g.wkb_hex if g is not None else None)
P['gkey']=P.geometry.normalize().apply(lambda g:g.wkb)
grp=P.groupby('gkey')
P['stack_n']=grp['APN'].transform('count')
U=P.drop_duplicates('gkey')[['gkey','geometry']].reset_index(drop=True)
U['uid']=U.index
inter=gpd.overlay(B[['h','geometry']],U[['uid','geometry']],how='intersection',keep_geom_type=True)
inter['a']=inter.area
inter=inter[inter.a>=120]  # ignore slivers/sheds under 120 sf
def floors(h):
    if np.isnan(h) or h<=0: return 1
    return int(max(1,min(12,round((h-4)/10.5)))) if h>14 else 1
inter['fl']=inter.h.apply(floors)
inter['gfa']=inter.a*inter.fl
agg=inter.groupby('uid').agg(fp=('a','sum'),gfa=('gfa','sum'),nb=('a','size'),maxfl=('fl','max'))
U=U.merge(agg,left_on='uid',right_index=True,how='left').fillna({'fp':0,'gfa':0,'nb':0,'maxfl':0})
P=P.merge(U[['gkey','fp','gfa','nb','maxfl']],on='gkey',how='left')
P['est_sf']=(P.gfa/P.stack_n).round(-1)
P['fp_sf']=(P.fp/P.stack_n).round(-1)
out=P[['APN','SITUS_ADDR','stack_n','fp_sf','est_sf','maxfl','geometry']].copy()
out['SITUS_ADDR']=out.SITUS_ADDR.fillna('').str.replace(', BELMONT','',regex=False)
out=out.to_crs(4326)
out['geometry']=out.geometry.simplify(0.000003,preserve_topology=True)
out=out.rename(columns={'SITUS_ADDR':'a','APN':'p','stack_n':'n','fp_sf':'f','est_sf':'s','maxfl':'fl'})
out['n']=out.n.astype(int); out['fl']=out.fl.astype(int); out['f']=out.f.astype(int); out['s']=out.s.astype(int)
out.to_file('site/parcels.geojson',driver='GeoJSON',COORDINATE_PRECISION=6)
bgeom.to_crs(4326).to_file('site/belmont.geojson',driver='GeoJSON')
s=out[out.s>0].s
print('with bldg',len(s),'median est sf',s.median(),'sum est sf',s.sum())
print('naive revenue at 0.33 all:',round(s.sum()*0.33/1e6,2),'M; at 0.54 all:',round(s.sum()*0.54/1e6,2))
