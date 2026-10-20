import urllib.request,urllib.parse,os
from pyproj import Transformer
t=Transformer.from_crs(4326,26910,always_xy=True)
x0,y0=t.transform(-122.3300,37.4960); x1,y1=t.transform(-122.2600,37.5350)
x0,y0,x1,y1=[int(v//10*10) for v in (x0,y0,x1+10,y1+10)]
print(x0,y0,x1,y1,(x1-x0),(y1-y0))
T=1500;n=0
for ty in range(y0,y1,T):
  for tx in range(x0,x1,T):
    w=min(T,x1-tx);h=min(T,y1-ty);fn=f"dem/t_{tx}_{ty}.tif"
    if os.path.exists(fn): continue
    q=dict(bbox=f"{tx},{ty},{tx+w},{ty+h}",bboxSR=26910,imageSR=26910,size=f"{w},{h}",format="tiff",pixelType="F32",noDataInterpretation="esriNoDataMatchAny",interpolation="RSP_BilinearInterpolation",f="image")
    u="https://elevation.nationalmap.gov/arcgis/rest/services/3DEPElevation/ImageServer/exportImage?"+urllib.parse.urlencode(q)
    
    for a in range(3):
      try: data=urllib.request.urlopen(u,timeout=300).read(); break
      except Exception as e: print("retry",e)
    else: raise SystemExit("fail")
    open(fn,"wb").write(data); n+=1; print(fn,len(data))
