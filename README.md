# Belmont Measure Y parcel-cost map

An unofficial, parcel-by-parcel estimate of what Belmont, California's **Measure Y** special tax (November 3, 2026 ballot) would cost each property. Measure Y is a tax on building floor area: **$0.33 per sq ft for dwelling units and $0.54 per sq ft for all other property** (Sec. 23-302), starting July 1, 2027.

- **Live map:** https://measure-y-parcel-cost.grok.me/
- **Background on Measure Y** (ballot text, costs, timeline, sources): https://belmont-measure-y.grok.me/
- **How a parcel's square footage and cost are calculated:** [docs/METHOD.md](docs/METHOD.md)

Click a parcel, or search an address, to see its estimated taxable floor area, the yearly tax, and 10- and 30-year totals under 0%, 3% or 4% annual increases. You can also type in your real floor area to get an exact figure.

> **Disclaimer.** These numbers are **estimates, not county or city figures, and not a tax bill.** Floor area is modeled from county building outlines and roof heights, not taken from assessor records. Treat any single parcel as roughly ±20%. This project is not affiliated with the City of Belmont or the County of San Mateo. For your actual floor area, see [Check your own county record](docs/METHOD.md#4-check-your-own-county-record).

## Repository layout

| Path | What it is |
|---|---|
| `publish/index.html` | The live page: one self-contained file with the parcel data inlined (Leaflet + MapLibre from unpkg, OpenFreeMap basemap). |
| `publish/og.png` | Social share image referenced by the page. |
| `site/index.html` | The page template (same as the live page, but it `fetch()`es `parcels.geojson` and `belmont.geojson`). |
| `build_data.py` | Step 1. Clips county parcels to Belmont, overlays building footprints, estimates floors and gross area. Writes `site/belmont.geojson` and a first-pass `site/parcels.geojson`. |
| `build_v3.py` | Step 2 (the version used by the live map). Full pipeline: footprints × floors, OpenStreetMap garage/shed removal, standard garage deduction, rate class. Overwrites `site/parcels.geojson` and writes `site/stats.json`. |
| `classify.py` | Maps county property-use descriptions to a rate class (residential / other / exempt / may be exempt). |
| `make_publish.py` | Step 3. Inlines the two GeoJSON files into `site/index.html` and writes `publish/index.html`. |
| `build_v2.py` | Earlier version (no OSM step), kept for reference. Not used by the live map. |
| `add_slope.py`, `slope/` | Side research on lot slope and allowed floor area under Belmont zoning. **Not used in the tax estimate** and not shown on the live map. See `slope/README.md`. |

## Rebuilding

The raw inputs are not in the repo (the county downloads alone are over 600 MB unzipped). [docs/METHOD.md §1](docs/METHOD.md#1-data-sources) lists every input and where to get it. In short:

```bash
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt

mkdir -p data osm site
# 1. From https://www.smcgov.org/tsd/gis-data-download download and unzip into data/:
#    BUILDING_FOOTPRINTS.zip             -> data/BUILDING_FOOTPRINTS/GIS_ADMIN.BUILDING_FOOTPRINTS.shp (+ .dbf .shx .prj)
#    SAN_MATEO_COUNTY_ACTIVE_PARCELS.zip -> data/SAN_MATEO_COUNTY_ACTIVE_PARCELS/SAN_MATEO_COUNTY_ACTIVE_PARCELS.shp (+ ...)
#    JURISDICTIONAL_BOUNDARIES_GEOJSON.zip -> data/JURISDICTIONAL_BOUNDARIES_GEOJSON/JURISDICTIONAL_BOUNDARIES_GEOJSON.json
# 2. Assessor use codes  -> data/belmont_puc.json           (see METHOD.md §1.4)
#    Public-agency APNs  -> data/public_owner_apns.json     (see METHOD.md §1.4)
# 3. OpenStreetMap buildings (Overpass, 4 tiles) -> osm/t1.json ... osm/t4.json  (see METHOD.md §1.5)

python build_data.py     # -> site/belmont.geojson, first-pass site/parcels.geojson
python build_v3.py       # -> site/parcels.geojson (final), site/stats.json
python make_publish.py   # -> publish/index.html
```

`publish/index.html` is a static file, so any static host works. To preview it locally, run `python -m http.server -d publish`.

Run the scripts from the repository root, since they use relative paths. `build_v3.py` reads `site/belmont.geojson`, so run `build_data.py` first. The steps for fetching items 2 and 3 are documented but have no scripts; they were run by hand against public endpoints.

## Data and credits

- Parcels, building footprints, jurisdiction boundaries and property-use codes: County of San Mateo GIS / Assessor (public data).
- Garage, shed and carport tags, and a few fallback addresses: © OpenStreetMap contributors, [ODbL](https://www.openstreetmap.org/copyright).
- Basemap: © [OpenFreeMap](https://openfreemap.org), © [OpenMapTiles](https://www.openmaptiles.org/), © OpenStreetMap contributors.
- Data as of **October 11, 2026**.

The map uses no owner names; the build never reads them or stores them. Addresses and parcel numbers (APNs) are public county records.

## License

Code and documentation: [MIT](LICENSE). The data embedded in `publish/index.html` remains subject to its sources' terms (County of San Mateo; OpenStreetMap under ODbL).
