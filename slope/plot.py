import json,numpy as np,matplotlib;matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import PolyCollection
from matplotlib.colors import ListedColormap,BoundaryNorm
import rasterio
city=json.load(open("city_estimated_slope.geojson"))["features"]
polys=[];vals=[]
for f in city:
    g=f["geometry"];s=f["properties"]["AvgSlope"]
    if not g or s is None: continue
    rings=[g["coordinates"][0]] if g["type"]=="Polygon" else [p[0] for p in g["coordinates"]]
    for r in rings: polys.append(np.array(r));vals.append(s)
cmap=ListedColormap(["#1a9850","#91cf60","#fee08b","#fc8d59","#d73027","#7f0000"]);norm=BoundaryNorm([0,10.5,15.5,20.5,30.5,44.5,200],6)
fig,ax=plt.subplots(figsize=(14,9.5))
pc=PolyCollection(polys,array=np.array(vals),cmap=cmap,norm=norm,edgecolor="#555",linewidth=0.1);ax.add_collection(pc)
ax.autoscale();ax.set_aspect(1/np.cos(np.radians(37.515)))
cb=fig.colorbar(pc,ax=ax,shrink=0.7,ticks=[5,13,18,25.5,37.5,60]);cb.ax.set_yticklabels(["0–10% FAR .533","11–15% .529–.512","16–20% .506–.480","21–30% .471–.395","31–44% .385–.272","45%+ .267"])
ax.set_title("Belmont: City GIS 'Estimated Slope' (AvgSlope, 5-ft contour method) by BZO Table 4 band");ax.set_xticks([]);ax.set_yticks([])
plt.tight_layout();plt.savefig("map_city_avgslope_bands.png",dpi=110)
# zoom on hills (Western Hills / Cipriani)
ax.set_xlim(-122.305,-122.285);ax.set_ylim(37.508,37.522);ax.set_title("Zoom: Cipriani / Western Hills, slope band per parcel");plt.savefig("map_city_avgslope_zoom.png",dpi=110)
# DEM slope raster
with rasterio.open("belmont_slope_pct_1m.tif") as r: a=r.read(1,out_shape=(1098,1540)).astype(float); a[a==255]=np.nan
fig,ax=plt.subplots(figsize=(14,10));im=ax.imshow(a,cmap="magma_r",vmin=0,vmax=60);fig.colorbar(im,ax=ax,shrink=0.7,label="slope % (USGS 3DEP 1 m, bare earth)")
ax.set_title("Belmont area: slope from USGS 3DEP 1 m lidar DEM");ax.set_xticks([]);ax.set_yticks([]);plt.tight_layout();plt.savefig("map_3dep_slope.png",dpi=100)
# scatter
P=json.load(open("parcel_slope_compare.json"));x=[p["city_avgslope"] for p in P if p["dem_mean"] and p["npx"]>200];y=[p["dem_mean"] for p in P if p["dem_mean"] and p["npx"]>200]
fig,ax=plt.subplots(figsize=(6,6));ax.scatter(x,y,s=1,alpha=.3);ax.plot([0,80],[0,80],"r-");ax.set_xlim(0,80);ax.set_ylim(0,80);ax.set_xlabel("City AvgSlope %");ax.set_ylabel("3DEP mean slope %");ax.set_title("Per-parcel: city vs lidar (r=0.87 all, 0.98 R-1)");plt.tight_layout();plt.savefig("scatter_city_vs_3dep.png",dpi=100)
