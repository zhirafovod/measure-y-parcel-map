"""v3: county footprint x floors (primary) + OSM join (accessory-structure removal, fallback addresses).
OSM data (c) OpenStreetMap contributors, ODbL. No owner names are read or stored."""
import json, collections, geopandas as gpd, pandas as pd, numpy as np
from shapely.geometry import Polygon, LineString, shape
from shapely.ops import polygonize, unary_union
from classify import classify, SFR_GARAGE
D='data/'; GARAGE=400; ACC={'garage','garages','shed','carport'}
bel=gpd.read_file('site/belmont.geojson').to_crs(2227); bu=bel.union_all(); bb=tuple(bel.total_bounds)
# ---- county parcels (same as build_data.py)
P=gpd.read_file(D+'SAN_MATEO_COUNTY_ACTIVE_PARCELS/SAN_MATEO_COUNTY_ACTIVE_PARCELS.shp',bbox=bb).to_crs(2227)
P=P[P.representative_point().within(bu)].copy()
P['gkey']=P.geometry.normalize().apply(lambda g:g.wkb)
P['stack_n']=P.groupby('gkey')['APN'].transform('count')
U=P.drop_duplicates('gkey')[['gkey','geometry']].reset_index(drop=True); U['uid']=U.index
# ---- county footprints -> pieces per parcel
B=gpd.read_file(D+'BUILDING_FOOTPRINTS/GIS_ADMIN.BUILDING_FOOTPRINTS.shp',bbox=bb).to_crs(2227)
B['geometry']=B.geometry.force_2d(); B['h']=(B.BUILDING_E-B.BASE_ELEV).clip(lower=0); B['bid']=range(len(B))
I=gpd.overlay(B[['bid','h','geometry']],U[['uid','geometry']],how='intersection',keep_geom_type=True)
I['a']=I.area; I=I[I.a>=120].copy(); I['pid']=range(len(I))
fl=lambda h: 1 if (np.isnan(h) or h<=14) else int(max(1,min(12,round((h-4)/10.5))))
I['fl']=I.h.apply(fl); I['gfa']=I.a*I.fl
# ---- OSM buildings
els={}
for i in range(1,5):
    for e in json.load(open(f'osm/t{i}.json'))['elements']: els[(e['type'],e['id'])]=e
rows=[]
for (t,i),e in els.items():
    g=None
    if t=='way':
        c=[(p['lon'],p['lat']) for p in e.get('geometry',[])]
        if len(c)>=4 and c[0]==c[-1]: g=Polygon(c)
    else:
        mem=lambda r:[LineString([(p['lon'],p['lat']) for p in m['geometry']]) for m in e.get('members',[]) if m.get('role')==r and m['type']=='way' and m.get('geometry')]
        o,inn=mem('outer'),mem('inner')
        if o:
            g=unary_union(list(polygonize(unary_union(o))))
            if inn: g=g.difference(unary_union(list(polygonize(unary_union(inn)))))
            if g.is_empty: g=None
    if g is not None and not g.is_valid: g=g.buffer(0)
    if g is not None: rows.append(dict(osm=f'{t}/{i}',tags=e.get('tags',{}),geometry=g))
O=gpd.GeoDataFrame(rows,geometry='geometry',crs=4326).to_crs(2227)
O=O[O.representative_point().within(bu)].copy().reset_index(drop=True); O['oid']=O.index
O['bt']=O.tags.apply(lambda t:t.get('building','')); O['oa']=O.area
# centroid-in-polygon join to parcels
C=O[['oid','geometry']].copy(); C['geometry']=O.representative_point()
J=gpd.sjoin(C,U[['uid','geometry']],predicate='within',how='left').drop_duplicates('oid')
O['uid']=O.oid.map(J.set_index('oid').uid)
osm_joined=O.uid.notna().mean()
# (a) accessory structures: OSM garage/shed/carport whose centroid is on parcel AND that overlaps a county piece on the same parcel
A=O[O.bt.isin(ACC)&O.uid.notna()]
X=gpd.overlay(A[['oid','uid','bt','oa','geometry']].rename(columns={'uid':'ouid'}),I[['pid','uid','a','geometry']],how='intersection',keep_geom_type=True)
X['ia']=X.area; X=X[X.ouid==X.uid]
X=X[(X.ia/X.oa)>=0.5]                             # OSM accessory mostly lies on a county footprint of the same parcel
X=X.sort_values('ia',ascending=False).drop_duplicates('oid')
X['whole']=(X.a<=1.5*X.oa+200)                    # county piece IS the accessory building -> drop piece (all floors)
Xw=X[X.whole].drop_duplicates('pid'); Xm=X[~X.whole]   # else merged into a larger county outline -> drop overlap, 1 floor
I['acc']=I.pid.map(Xw.set_index('pid').bt)
rem=pd.concat([I[I.acc.notna()][['uid','gfa','acc']].rename(columns={'gfa':'sf'}),
               Xm[['uid','ia','bt']].rename(columns={'ia':'sf','bt':'acc'})])
acc_by_u=rem.groupby('uid').agg(acc_sf=('sf','sum'),acc_garage=('acc',lambda s:int(s.isin({'garage','garages','carport'}).any())))
acc_stats=dict(whole=int(len(Xw)),merged=int(len(Xm)),by_type=X.bt.value_counts().to_dict())
agg=I.groupby('uid').agg(gfa=('gfa','sum'),maxfl=('fl','max'))
U=U.join(agg,on='uid').join(acc_by_u,on='uid').fillna({'gfa':0,'maxfl':0,'acc_sf':0,'acc_garage':0})
# (b) OSM addresses per parcel (largest addressed building)
Ad=O[O.uid.notna()&O.tags.apply(lambda t:'addr:housenumber' in t and 'addr:street' in t)].sort_values('oa',ascending=False)
Ad['addr']=Ad.tags.apply(lambda t:(t['addr:housenumber']+' '+t['addr:street']).upper())
osm_addr=Ad.drop_duplicates('uid').set_index('uid').addr
P=P.merge(U[['gkey','uid','gfa','maxfl','acc_sf','acc_garage']],on='gkey',how='left')
# ---- classification and estimate
puc={r['APN']:r for r in json.load(open(D+'belmont_puc.json'))}; pub=json.load(open(D+'public_owner_apns.json'))
P['pd']=P.APN.map(lambda a:(puc.get(a) or {}).get('PUCDESC'))
cl=[classify(d,pub.get(a)) for d,a in zip(P.pd,P.APN)]
P['c']=[x[0] for x in cl]; P['u']=[(x[1] or '').replace(' (Migrated)','') for x in cl]
n=P.stack_n
raw=P.gfa/n; acc=np.minimum(P.acc_sf/n,0.5*raw); base=raw-acc
sfr=P.pd.isin(SFR_GARAGE)&(base>0)
blanket=sfr&(P.acc_garage==0)                     # no OSM detached garage -> assume attached garage
adj=base.copy(); adj[blanket]=np.maximum(base[blanket]-GARAGE,base[blanket]*0.6)
P['a']=P.SITUS_ADDR.fillna('').str.replace(', BELMONT','',regex=False).str.strip()
need=P.a==''
import re
SUF={'AVENUE':'AVE','STREET':'ST','DRIVE':'DR','ROAD':'RD','BOULEVARD':'BLVD','COURT':'CT','LANE':'LN','PLACE':'PL','WAY':'WAY','CIRCLE':'CIR','TERRACE':'TER'}
norm=lambda x:' '.join(SUF.get(w,w) for w in re.sub(r'[^A-Z0-9 ]','',x.upper()).split())
county_addr=set(P.a[P.a!=''].map(norm))
osm_addr=osm_addr[~osm_addr.map(norm).isin(county_addr)]   # skip OSM addresses already used by a county parcel (building straddles a lot line)
P['ao']=0; P.loc[need,'a']=P.loc[need,'uid'].map(osm_addr).fillna(''); P.loc[need&(P.a!=''),'ao']=1
out=gpd.GeoDataFrame(dict(p=P.APN,a=P.a,c=P.c,u=P.u,n=n.astype(int),
  s=((adj/10).round()*10).astype(int),r=raw.round(-1).astype(int),o=acc.round(-1).astype(int),
  g=blanket.astype(int),ao=P.ao.astype(int),fl=P.maxfl.astype(int)),geometry=P.geometry,crs=2227).to_crs(4326)
out['geometry']=out.geometry.simplify(0.000003,preserve_topology=True)
out.to_file('site/parcels.geojson',driver='GeoJSON',COORDINATE_PRECISION=6)
R=out[out.c=='res'].s.sum(); Oo=out[out.c=='other'].s.sum(); M=out[out.c=='maybe'].s.sum()
nodata=out[(out.s==0)&(out.c!='exempt')]
stats=dict(parcels=len(out),by_class=out.c.value_counts().to_dict(),
  parcels_with_estimate=int((out.s>0).sum()),parcels_with_estimate_taxable=int(((out.s>0)&(out.c!='exempt')).sum()),
  osm_buildings=len(O),osm_joined_pct=round(osm_joined*100,1),
  osm_accessory_tagged=int(O.bt.isin(ACC).sum()),osm_accessory_matched=acc_stats,
  parcels_adjusted_osm=int((out.o>0).sum()),osm_sf_removed=int(out.o.sum()),
  parcels_blank_addr_county=int(need.sum()),parcels_addr_from_osm=int(out.ao.sum()),parcels_still_no_addr=int((out.a=='').sum()),
  res_sf=int(R),other_sf=int(Oo),maybe_sf=int(M),gross_res=round(0.33*R),gross_other=round(0.54*Oo),gross_total=round(0.33*R+0.54*Oo),
  gross_with_maybe=round(0.33*R+0.54*Oo+0.54*M),sfr_median_est=float(out[P.pd.isin(SFR_GARAGE).values&(out.s>0)].s.median()),
  no_building_nonexempt=int(len(nodata)),no_building_by_use=nodata.u.replace('', 'No use code').value_counts().to_dict(),
  no_building_exempt=int(((out.s==0)&(out.c=='exempt')).sum()))
json.dump(stats,open('site/stats.json','w'),indent=1); print(json.dumps(stats,indent=1))
