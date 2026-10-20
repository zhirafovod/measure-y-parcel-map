import json,numpy as np,collections,math
P=json.load(open("parcel_slope_compare.json"))
site=json.load(open("../site/parcels.geojson"))["features"]
S={f["properties"]["p"]:f["properties"] for f in site}
T4={**{i:0.533 for i in range(0,11)},11:.529,12:.525,13:.521,14:.516,15:.512,16:.506,17:.499,18:.493,19:.486,20:.480,21:.471,22:.463,23:.454,24:.446,25:.437,26:.429,27:.420,28:.412,29:.403,30:.395,31:.385,32:.374,33:.364,34:.354,35:.344,36:.334,37:.324,38:.314,39:.303,40:.293,41:.288,42:.283,43:.277,44:.272}
def far(s):
    k=int(math.floor(s+0.5)); return 0.267 if k>=45 else T4[max(k,0)]
def cap5(zone,lot):
    if zone in("R1E","R1H"): return 4500
    if lot<=10000: return 3500
    return min(4500,3500+0.15*(lot-10000))
R1={"R1A","R1B","R1C","R1E","R1H","S-1/R1B"}
a=np.array([(p["city_avgslope"],p["dem_mean"]) for p in P if p["dem_mean"] is not None and p["city_avgslope"] is not None and p["npx"]>200])
d=a[:,1]-a[:,0]
print("n",len(a),"corr",np.corrcoef(a.T)[0,1].round(3),"median diff",np.median(d).round(2),"MAD",np.median(abs(d)).round(2),"p90 absdiff",np.percentile(abs(d),90).round(1))
r1=[p for p in P if p["zone"] in R1 and p["city_avgslope"] is not None]
b=np.array([(p["city_avgslope"],p["dem_mean"]) for p in r1 if p["dem_mean"] is not None])
print("R1 corr",np.corrcoef(b.T)[0,1].round(3),"median diff",np.median(b[:,1]-b[:,0]).round(2),"MAD",np.median(abs(b[:,1]-b[:,0])).round(2))
bands=[(0,10.5,"0–10% (FAR .533)"),(10.5,15.5,"11–15%"),(15.5,20.5,"16–20%"),(20.5,30.5,"21–30%"),(30.5,44.5,"31–44%"),(44.5,999,"45%+ (FAR .267)")]
def bandof(s):
    for lo,hi,n in bands:
        if lo<=s<hi: return n
out={"all_parcels":collections.Counter(bandof(p["city_avgslope"]) for p in P if p["city_avgslope"] is not None),
     "R1_parcels":collections.Counter(bandof(p["city_avgslope"]) for p in r1)}
for k,c in out.items(): print(k,sum(c.values()),[(n,c[n]) for _,_,n in bands])
# FA calc for R1
rows=[];bind=collections.Counter()
for p in r1:
    lot=p["areasf"]; s=p["city_avgslope"]; f=far(s)
    fa4=max(1200,lot*f); fa5=cap5(p["zone"],lot); mx=min(fa4,fa5)
    bind["slope (Table 4)" if fa4<fa5 else "lot-size cap (Table 5)"]+=1
    est=S.get(p["APN"],{}).get("s")
    rows.append(dict(APN=p["APN"],zone=p["zone"],lot=round(lot),slope=round(s,1),far=f,fa_slope=round(fa4),fa_cap=round(fa5),max_fa=round(mx),est=est))
print("binding",bind)
mx=np.array([r["max_fa"] for r in rows]);print("max FA median",np.median(mx),"p10",np.percentile(mx,10),"p90",np.percentile(mx,90))
red=[r for r in rows if r["far"]<0.533];print("R1 lots with FAR reduced by slope",len(red))
withest=[r for r in rows if r["est"]]
over=[r for r in withest if r["est"]>r["max_fa"]];print("R1 with est sqft",len(withest),"est > max allowed",len(over))
apns=set(S); m=sum(1 for p in P if p["APN"] in apns); print("APN match city slope->site parcels",m,"of",len(P),"; site parcels",len(S),"matched",len(apns & {p['APN'] for p in P}))
json.dump(dict(bands={k:dict(v) for k,v in out.items()},binding=dict(bind)),open("slope_stats.json","w"),indent=1)
# validation examples
import random;random.seed(3)
for p in random.sample([p for p in r1 if p["dem_mean"]],8): print(p["APN"],p["addr"],p["zone"],round(p["areasf"]),"city",round(p["city_avgslope"],1),"dem",p["dem_mean"],"med",p["dem_median"],"relief",p["relief_ft"])
json.dump(rows,open("r1_floor_area.json","w"))
