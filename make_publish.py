"""Inline site/parcels.geojson + site/belmont.geojson into publish/index.html (single self-contained file)."""
import json, os
s=open('site/index.html').read()
d=json.dumps(json.load(open('site/parcels.geojson')),separators=(',',':'))
b=json.dumps(json.load(open('site/belmont.geojson')),separators=(',',':'))
t=s.replace("fetch('belmont.geojson').then(r=>r.json()).then(g=>","Promise.resolve(BOUNDARY).then(g=>",1)
t=t.replace("fetch('parcels.geojson').then(r=>r.json()).then(g=>{","Promise.resolve(PARCELS).then(g=>{",1)
assert 'fetch(' not in t
inl='<script>const PARCELS='+d.replace('</','<\\/')+';\nconst BOUNDARY='+b.replace('</','<\\/')+';</script>\n'
i=t.index('<script src="https://unpkg.com/leaflet'); t=t[:i]+inl+t[i:]
os.makedirs('publish',exist_ok=True); open('publish/index.html','w').write(t)
