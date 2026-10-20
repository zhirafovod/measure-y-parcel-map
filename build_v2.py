"""Build publish-ready parcel data for the Measure Y cost map.
Inputs: county building footprints + active parcels (smcgov.org GIS download),
county public use codes (Common/ACTIVE_PARCELS_APN, PUCDESC only; owner names never fetched/stored),
public-agency APNs (matched server-side by agency name; only APNs stored)."""
import geopandas as gpd, json, numpy as np
from classify import classify, SFR_GARAGE
GARAGE=400
g=gpd.read_file('data/parcels_v1.geojson')       # v1 output: p,a,n,f,s,fl
puc={r['APN']:r for r in json.load(open('data/belmont_puc.json'))}
pub=json.load(open('data/public_owner_apns.json'))
g['pd']=g.p.map(lambda a:(puc.get(a) or {}).get('PUCDESC'))
cl=[classify(pd,pub.get(a)) for pd,a in zip(g.pd,g.p)]
g['c']=[x[0] for x in cl]; g['u']=[(x[1] or '').replace(' (Migrated)','') for x in cl]
raw=g.s.astype(float)
adj=raw.copy()
m=g.pd.isin(SFR_GARAGE)&(raw>0)
adj[m]=np.maximum(raw[m]-GARAGE, raw[m]*0.6)
g['r']=raw.round(-1).astype(int)          # footprint x floors, before garage deduction
g['s']=(adj/10).round().astype(int)*10    # estimate shown
g['g']=m.astype(int)                      # garage deduction applied
out=g[['p','a','c','u','n','s','r','g','fl','geometry']]
out.to_file('site/parcels.geojson',driver='GeoJSON',COORDINATE_PRECISION=6)
R=out[out.c=='res'].s.sum(); O=out[out.c=='other'].s.sum(); M=out[out.c=='maybe'].s.sum()
stats=dict(parcels=len(out),by_class=out.c.value_counts().to_dict(),res_sf=int(R),other_sf=int(O),maybe_sf=int(M),
  gross_res=round(0.33*R),gross_other=round(0.54*O),gross_total=round(0.33*R+0.54*O),gross_with_maybe=round(0.33*R+0.54*O+0.54*M),
  sfr_median_est=float(out[out.g==1].s.median()))
json.dump(stats,open('site/stats.json','w'),indent=1); print(json.dumps(stats,indent=1))
