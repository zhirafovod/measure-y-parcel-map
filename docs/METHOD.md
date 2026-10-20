# Method: how a parcel's taxable square footage and annual cost are estimated

This document describes, step by step, how the map turns the County of San Mateo's free GIS downloads into an estimated Measure Y tax for each Belmont parcel. Every step below was checked against the scripts in this repository (`build_data.py`, `build_v3.py`, `classify.py`, `make_publish.py`) and the page logic in `publish/index.html`.

**Data as of October 11, 2026.** These are estimates, not county or city figures, and not a tax bill.

---

## 0. What the measure taxes

Measure Y (Resolution 2026-69, Attachment 2) levies a special tax on building floor area:

| Class | Rate (FY 2027-28) |
|---|---|
| Dwelling units | **$0.33 per sq ft** per year |
| All other property | **$0.54 per sq ft** per year |

**Square footage (Sec. 23-301(j))** is the *gross area of all floors*, including usable basement and porches. It excludes garage and parking areas, balconies and patios.

Other provisions the map reflects:
- Sec. 23-302(c): the Council may raise the rate each year by up to the greater of Bay Area (SF-Oakland-Hayward) CPI-U or California per-capita personal income growth.
- Sec. 23-303: exempts parcels that are exempt by state or federal law, and owner-occupants aged 65+, who must apply each year.
- Sec. 23-304: the tax starts July 1, 2027 and runs "until ended by voters."

The county does not publish "gross area of all floors" for most homes, so the map **models** it from building outlines and roof heights.

---

## 1. Data sources

### 1.1 County building footprints — `BUILDING_FOOTPRINTS.zip`

Source: County of San Mateo **GIS Data Download** page, https://www.smcgov.org/tsd/gis-data-download

- **Format:** an Esri shapefile, which is four files that travel together:
  - `.shp`: the polygon geometry, one roof outline per building.
  - `.dbf`: the attribute table, one row per building.
  - `.shx`: the shape index.
  - `.prj`: the coordinate system.

  Unzipped, the files are named `GIS_ADMIN.BUILDING_FOOTPRINTS.*` and total about 185 MB.
- **Contents:** 229,298 building outlines covering the whole county. The files are dated **August 5, 2021**.
- **Coordinate system:** NAD83 / California State Plane Zone III, in US survey feet (EPSG:2227). Because the units are feet, polygon areas come out directly in square feet.
- **Attribute fields (7):**

| Field | Meaning |
|---|---|
| `OBJECTID` | Row id |
| `BASE_ELEV` | Ground elevation at the building (ft) |
| `BUILDING_E` | Roof elevation (ft) |
| `BUILDING_H` | Height field (not used; the script derives height from the two elevations) |
| `SE_ANNO_CA` | Annotation class |
| `SHAPE_AREA` | Outline area (sq ft) |
| `SHAPE_LEN` | Outline perimeter (ft) |

There is **no APN, address, use or square-footage field**. A building outline is not tied to any parcel until you overlay the two layers geometrically (step 2.2).

### 1.2 County parcels — `SAN_MATEO_COUNTY_ACTIVE_PARCELS.zip`

The parcels file is on the same download page. It is an Esri shapefile in EPSG:2227 with 235,479 parcels countywide (the copy used here is dated Oct 10, 2026). Fields used: `APN` (9-digit assessor parcel number) and `SITUS_ADDR` (street address). It has **no building square footage**. Condominium units appear as separate parcels whose outlines are identical and stacked on top of each other.

### 1.3 Jurisdictional boundaries — `JURISDICTIONAL_BOUNDARIES_GEOJSON.zip`

This file is also on the download page. The city outline is taken from the feature where `COMMONNAME` = `BELMONT` and the feature is not flagged `UNINCORPORATED`. It is saved as `site/belmont.geojson`.

### 1.4 Assessor property-use codes and public-agency parcels

- **Use codes:** the county's public ArcGIS service `https://gis.smcgov.org/maps/rest/services/Common/ACTIVE_PARCELS_APN/MapServer` (layer 0) was queried for Belmont parcels. Only `APN`, `PUC`, `PUCDESC`, `OFFICEGRSBLDAREA` and `FloorDesignator` were saved, to `data/belmont_puc.json`. `PUCDESC` is a text description such as "Single Family Home", "Condominium" or "Office Building - Low-Rise". `OFFICEGRSBLDAREA` is filled in for only a handful of Belmont office parcels, so it is not used.
- **Public-agency parcels:** parcels owned by a public agency (city, county, state, federal, school district, special district) were identified on the server by agency owner name. **Only the APN and the agency type were kept**, in `data/public_owner_apns.json` (211 parcels). No owner names are stored in this repository or in the map.

These two files were fetched by hand; there is no fetch script in the repo.

### 1.5 OpenStreetMap buildings

All `building=*` ways and relations inside Belmont were downloaded from the Overpass API (`out geom`) in four tiles covering lat 37.496–37.535, lon −122.330 to −122.260. They were saved as `osm/t1.json` … `osm/t4.json` (snapshot of October 11, 2026; © OpenStreetMap contributors, ODbL). The map uses two things from them:
- the `building` tag values `garage`, `garages`, `carport` and `shed`, to find detached accessory buildings;
- `addr:housenumber` + `addr:street`, only as a search address for the few parcels with a blank county address.

---

## 2. Steps

All geometry work is done in EPSG:2227 (feet).

### 2.1 Clip parcels to Belmont

The scripts read the parcels inside the city's bounding box, then keep a parcel if its **representative point** (a point guaranteed to be inside the polygon) falls within the Belmont boundary. Using a point rather than "touches the boundary" avoids picking up neighbouring-city parcels that only share an edge. Result: **8,705 parcels**.

### 2.2 Overlay footprints with parcels

1. Parcels with identical outlines (stacked condo units) are grouped into one *lot outline*, and each parcel records how many units share it (`stack_n`).
2. Every building outline is **intersected** with the lot outlines (`geopandas.overlay`, intersection). This cuts a building that straddles a lot line into pieces, each belonging to exactly one lot.
3. Pieces **under 120 sq ft** are dropped. These are slivers from slightly misaligned lines, plus very small sheds.

### 2.3 Height → number of floors

For each footprint:

```
height h = BUILDING_E − BASE_ELEV   (roof elevation minus ground elevation, floored at 0)

floors = 1                               if h ≤ 14 ft (or h is missing)
floors = round((h − 4) / 10.5)           otherwise, clamped to 1 … 12
```

The rule assumes about 10.5 ft per storey plus about 4 ft of roof and foundation. For example, h = 12 ft gives 1 floor, h = 22 ft gives 2, h = 30 ft gives 2, and h = 33 ft gives 3.

### 2.4 Gross area per parcel

```
gross area of a piece  = piece area (sq ft) × floors
parcel gross area      = sum over all pieces on the lot outline
```

### 2.5 Stacked condo parcels: even split

When `stack_n` parcels share one lot outline, each gets `gross area ÷ stack_n`. This is crude: a large and a small unit in the same building get the same number.

### 2.6 Garage, carport and shed removal

Garages and parking areas are excluded from taxable area (Sec. 23-301(j)). The county footprints don't distinguish garages, so two adjustments are applied (in `build_v3.py`).

**(a) Detached accessory buildings mapped in OpenStreetMap.** An OSM `garage` / `garages` / `carport` / `shed` building is matched to a county footprint piece only if:
- its representative point lies on the same lot outline, **and**
- at least 50% of its area overlaps a county piece on that lot.

If the county piece is essentially the accessory building itself (piece area ≤ 1.5 × OSM area + 200 sq ft), the whole piece is removed, all floors. Otherwise the accessory was merged into a larger county outline, and only the overlapping area is removed, at one floor.

Removal per parcel is capped at 50% of the parcel's gross area. This adjusted **294 parcels** (about 160 whole pieces and 150 partial overlaps) and removed about 160,000 sq ft in total.

**(b) Standard attached-garage deduction.** For parcels whose use code is "Single Family Home", "Single Family Home w/ ADU" or "Single Family Home - BMR", and where no OSM garage or carport was matched in (a):

```
estimate = max(gross − 400 sq ft, 0.6 × gross)
```

In other words, it subtracts a typical 400 sq ft attached garage but never more than 40% of the estimate. A parcel where only a shed was removed in (a) still gets this deduction.

No garage deduction is applied to condos, townhomes, apartments or commercial buildings.

The final estimate is rounded to the nearest 10 sq ft.

### 2.7 Rate class (`classify.py`)

The class comes from the assessor `PUCDESC`, checked in this order:

| Class | Rule | Rate on the map |
|---|---|---|
| **Exempt** | Public-agency owner (§1.4), or use is Park, Highway & Streets, Right-of-Way, Pipeline/Canal, Underwater & Marshland, Post Office, Community Center | $0 |
| **May be exempt** | School, Church, College, Educational Facility, Cemetery, Nursing/Convalescent Home, Skilled Nursing, Assisted Living | shown at $0.54 "if taxable" |
| **Residential (dwelling units)** | Single-family (incl. ADU, BMR), 2–4 units, apartments (all sizes), condominium, townhome, SFR converted to 2 units, multiple detached units, mixed residential types, residential misc., independent living | **$0.33** |
| **Other** | Every other use code, including vacant, office, retail, industrial and hotel | **$0.54** |
| Unclassified | No use code, often a condo common area | shown at $0.54 for reference |

"May be exempt" parcels are flagged because the measure exempts only what state or federal law exempts. Whether nonprofit property-tax exemptions apply to a per-square-foot special tax is not settled here.

### 2.8 Annual cost and multi-year totals (page logic)

```
year-1 tax  = estimated sq ft × rate                (0 if exempt, or if the 65+ box is ticked on a $0.33 parcel)
year-k tax  = year-1 × (1 + increase)^(k−1)          increase = 0%, 3% (≈ Bay Area CPI) or 4% (≈ CA per-capita income)
10-/30-year = sums of years 1–10 / 1–30
```

You can overwrite the estimated square footage with your real floor area, and change the rate class.

**Worked example (generic).** Take an example 1950s single-story home with an 1,800 sq ft footprint. The roof is under 14 ft above grade, so it counts as 1 floor and the gross area is 1,800 sq ft. No detached garage is mapped, so the standard deduction applies: 1,800 − 400 = **1,400 sq ft**, which is above the 60% floor of 1,080. At $0.33/sq ft that is about **$462 per year**. With 3% yearly increases it becomes about $603 in year 10 and about $5,300 over the first 10 years.

### 2.9 Sanity check against the city's figure

Summing all taxable parcels (residential at $0.33, other at $0.54, excluding "may be exempt") gives about **$8.4M** before senior exemptions. The City Attorney's impartial analysis estimates about **$7.1M** in the first year. The gap is consistent with senior exemptions (roughly 20% of residential revenue), but it could also mean the floor areas run high. No scaling was applied. Treat any single parcel as roughly ±20%.

---

## 3. Known limitations

- **2021 footprints.** The county building layer dates from August 2021. Anything built, expanded or demolished since then is missing or out of date.
- **Lower floors on sloped lots.** Height is measured from `BASE_ELEV` to the roof. On a hillside, a daylight basement or lower storey under the main floor may not be counted, or the floor count can come out too high or too low. A usable basement counts toward the tax.
- **Apartments and commercial buildings** show the whole building's area for the parcel, i.e. what the owner pays. Per unit, divide by the number of units.
- **Garages inside buildings.** Podium or underground parking and multi-story garages inside buildings are not removed, so those parcels run high.
- **Attached garages are assumed, not measured.** The 400 sq ft deduction applies to every single-family home without a mapped detached garage, including homes that have no garage, or a larger one.
- **Porches, balconies and patios** are counted wherever they are part of the roof outline (covered porches should count, covered balconies and patios should not). The outlines can't tell them apart.
- **Condo split is even** across units sharing a lot outline.
- **Rate class** depends on the county use code. A few parcels have none, and the exempt / may-be-exempt calls are this project's reading, not a determination.
- **Senior exemption** (owner-occupant 65+) can't be known per parcel. The page has a checkbox for it.

---

## 4. Check your own county record

The county publishes some building facts per parcel through a public, no-login assessor service. You need your **9-digit APN**, which is printed on your property tax bill. You can also look it up in the county map portal (below), or click your parcel on this map.

**Building characteristics (single-family):**

```
https://gis.smcgov.org/Geocortex/Essentials/REST/sites/Assessor_PROPUB_555/searchTables/Details_SFR/search?apn=<9-digit APN>
```

Type the APN as digits only, without dashes (for example `123456789`, not `123-456-789`). The response lists `yearBuilt`, `landArea`, `baseArea`, `totalRooms`, `bedrooms` and `bathrooms`.

Replace `Details_SFR` with one of these to see other records:
- `Roll`: assessed land and improvement values by year.
- `Sales_History`: recorded sales.
- `Summary`: owner and mailing address, situs address, district.
- `Legal_Description`.

**County map portal:** https://gis.smcgov.org/Html5Viewer/?viewer=raster
1. Click **Agree** on the disclaimer.
2. Choose **Search Parcels by APN**.
3. Enter the APN as digits without dashes and search. Address search is less reliable.
4. The result shows the address, legal description and assessor-map links, but **no building size**. For that, use the `Details_SFR` link above.

**What to expect:** the county's total square footage field (`TOTALSQFT`) is usually blank for houses. **`baseArea` is usually the only building size the county publishes**, and there are no garage, porch or number-of-stories fields. `baseArea` is not necessarily the same as Measure Y's "gross area of all floors". If your home has more than one storey or a usable basement, or if `baseArea` includes a garage, your taxable area will differ. If you know your real floor area, from plans, an appraisal or a permit, type it into the map's floor-area box for an exact figure.

---

## 5. Reproducing the build

See the [README](../README.md#rebuilding). The live page was produced by running `build_data.py`, then `build_v3.py`, then `make_publish.py`. `build_v2.py`, `add_slope.py` and `slope/` are earlier or side work and do not feed the published numbers.
