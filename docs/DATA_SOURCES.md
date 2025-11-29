# Data Sources Guide

This document lists all data sources needed for the Israel Cantons project.

## 1. Election Data

### Central Elections Committee (ועדת הבחירות המרכזית)

Download election results by locality (תוצאות לפי יישובים) for each Knesset:

| Knesset | Election Date | Main URL | City Results Page |
|---------|---------------|----------|-------------------|
| 21st | April 9, 2019 | https://votes21.bechirot.gov.il/ | https://votes21.bechirot.gov.il/cityresults |
| 22nd | September 17, 2019 | https://votes22.bechirot.gov.il/ | https://votes22.bechirot.gov.il/cityresults |
| 23rd | March 2, 2020 | https://votes23.bechirot.gov.il/ | https://votes23.bechirot.gov.il/cityresults |
| 24th | March 23, 2021 | https://votes24.bechirot.gov.il/ | https://votes24.bechirot.gov.il/cityresults |
| 25th | November 1, 2022 | https://votes25.bechirot.gov.il/ | https://votes25.bechirot.gov.il/cityresults |

### Download Instructions

1. Visit each "City Results" URL above
2. Look for download/export button (usually Excel or CSV format)
3. Save files to: `data/raw/elections/`
4. Suggested naming convention:
   - `knesset_21_results.xlsx`
   - `knesset_22_results.xlsx`
   - `knesset_23_results.xlsx`
   - `knesset_24_results.xlsx`
   - `knesset_25_results.xlsx`

### Alternative Source: Israel Open Data Portal

- URL: https://data.gov.il/dataset/votes-knesset
- Search for "בחירות לכנסת" or "Knesset elections"
- May have consolidated datasets in CSV format

---

## 2. Geographic Data (Municipal Boundaries)

### Primary Source: Ministry of Interior ArcGIS Portal

**URL:** https://gvulot-shiput-statutory-moinil.opendata.arcgis.com/

This portal contains:
- Current statutory municipal boundaries (גבולות שיפוט)
- Local authority polygons
- Geographic layers

**Download formats available:** Shapefile, GeoJSON, CSV, KML

### Alternative Sources

1. **CBS GIS Portal**
   - URL: https://gis.cbs.gov.il/localities/
   - Contains localities data with geographic information

2. **GovMap (Official Israel Map Portal)**
   - URL: https://www.govmap.gov.il/?lay=125
   - Layer 125 = Local authorities
   - Can export data in various formats

3. **Israel Open Data Portal**
   - URL: https://data.gov.il/dataset?q=Gis&res_format=ZIP
   - Search for GIS data with ZIP format

### Download Instructions

1. Visit the Ministry of Interior ArcGIS portal
2. Find "רשויות מקומיות" (Local Authorities) or "גבולות שיפוט" (Jurisdiction Boundaries)
3. Click on the dataset and look for "Download" button
4. Choose Shapefile or GeoJSON format
5. Save to: `data/raw/geo/`
6. Suggested naming: `municipal_boundaries.shp` or `municipal_boundaries.geojson`

---

## 3. Data Fields Expected

### Election Data Fields
- Municipality code (סמל יישוב)
- Municipality name (שם יישוב)
- Total eligible voters (בעלי זכות בחירה)
- Total votes cast (מצביעים)
- Valid votes (כשרים)
- Invalid votes (פסולים)
- Votes per party/list (קולות לפי רשימה)

### Geographic Data Fields
- Municipality code
- Municipality name
- Polygon geometry (boundaries)
- Area
- District/Region (מחוז/נפה)

---

## 4. Data Quality Notes

### Known Issues to Watch For
- Municipality codes may differ between election data and geographic data
- Municipality names may have spelling variations (Hebrew transliteration)
- Some municipalities may have merged or split between elections
- Small localities may be grouped differently across datasets

### Validation Steps
1. Count municipalities in each dataset
2. Check for matching municipality codes
3. Identify any missing or extra entries
4. Document discrepancies for later resolution

---

## 5. File Organization

After downloading, organize files as follows:

```
data/raw/
├── elections/
│   ├── knesset_21_results.xlsx
│   ├── knesset_22_results.xlsx
│   ├── knesset_23_results.xlsx
│   ├── knesset_24_results.xlsx
│   └── knesset_25_results.xlsx
└── geo/
    ├── municipal_boundaries.shp
    ├── municipal_boundaries.shx
    ├── municipal_boundaries.dbf
    └── municipal_boundaries.prj
```

Or if using GeoJSON:
```
data/raw/geo/
└── municipal_boundaries.geojson
```
