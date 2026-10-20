import json,glob,numpy as np,rasterio
from rasterio.merge import merge
from rasterio.features import rasterize
from shapely.geometry import shape
from shapely.ops import transform as stx
from pyproj import Transformer
srcs=[rasterio.open(f) for f in sorted(glob.glob("dem/t_*.tif"))]
dem,tr=merge(srcs); dem=dem[0].astype("float32"); nod=srcs[0].nodata
if nod is not None: dem[dem==nod]=np.nan
dem[dem<-100]=np.nan
print("mosaic",dem.shape,np.nanmin(dem),np.nanmax(dem),tr)
# save compact copy: int16 decimeters, deflate
prof=srcs[0].profile.copy(); prof.update(height=dem.shape[0],width=dem.shape[1],transform=tr,dtype="int16",nodata=-32768,compress="deflate",predictor=2,tiled=True)
with rasterio.open("belmont_3dep_1m_dm.tif","w",**prof) as o: o.write(np.where(np.isnan(dem),-32768,np.round(dem*10)).astype("int16"),1)
px=tr.a
gy,gx=np.gradient(dem,px)   # m/m
sl=np.hypot(gx,gy)*100
prof2=prof.copy(); prof2.update(dtype="uint8",nodata=255)
with rasterio.open("belmont_slope_pct_1m.tif","w",**prof2) as o: o.write(np.where(np.isnan(sl),255,np.clip(sl,0,254)).astype("uint8"),1)
city=json.load(open("city_estimated_slope.geojson"))["features"]
T=Transformer.from_crs(4326,26910,always_xy=True).transform
shapes=[];meta=[]
for i,f in enumerate(city):
    if not f["geometry"]: continue
    g=stx(T,shape(f["geometry"])); shapes.append((g,i+1)); meta.append(i)
lab=rasterize(shapes,out_shape=dem.shape,transform=tr,fill=0,dtype="int32")
L=lab.ravel(); v=~np.isnan(sl.ravel())&(L>0)
n=len(city)+1
cnt=np.bincount(L[v],minlength=n); s=np.bincount(L[v],weights=sl.ravel()[v],minlength=n)
mean=np.where(cnt>0,s/np.maximum(cnt,1),np.nan)
# robust: median per parcel via sorting
order=np.argsort(L[v],kind="stable"); Ls=L[v][order]; Ss=sl.ravel()[v][order]
bounds=np.searchsorted(Ls,np.arange(n+1))
med=np.full(n,np.nan); emin=np.full(n,np.nan); emax=np.full(n,np.nan)
E=dem.ravel()[v][order]
for k in range(1,n):
    a,b=bounds[k],bounds[k+1]
    if b>a: med[k]=np.median(Ss[a:b]); emin[k]=E[a:b].min(); emax[k]=E[a:b].max()
out=[]
for i,f in enumerate(city):
    p=f["properties"];k=i+1
    out.append(dict(APN=p["APN"],addr=p["EasyAddr"],zone=p["ZONECODE"],lu=p["LUCODE"],areasf=p["AreaSF"],city_avgslope=p["AvgSlope"],
        dem_mean=None if np.isnan(mean[k]) else round(float(mean[k]),2),dem_median=None if np.isnan(med[k]) else round(float(med[k]),2),
        relief_ft=None if np.isnan(emax[k]) else round(float((emax[k]-emin[k])/0.3048),1),npx=int(cnt[k])))
json.dump(out,open("parcel_slope_compare.json","w"))
print("done",len(out))
