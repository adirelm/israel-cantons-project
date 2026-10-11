# Boundary data sources

## municipalities.geojson

Israel Central Bureau of Statistics (CBS), municipal boundary polygons inside the Green Line.

## js/ — Israeli local authorities in Judea and Samaria (retrieved 2026-10-11)

The raw layers are not committed (size, and no license is stated). Re-download them with the queries below into `data/raw/geo/js/`; `scripts/build_boundaries.py` derives `municipalities_js.geojson` from them.

- `cbs_munc2023.geojson` — CBS layer `munc2023_ir_mek_diss`, layer 7: a national layer of locality boundaries based on the Ministry of Interior's continuous layer, updated to the end of 2023. Only the 17 Judea and Samaria cities and local councils (object IDs 140–156). No terms of use stated on the layer.
  `https://services2.arcgis.com/xMRYm7cNgdR5RN6F/arcgis/rest/services/munc2023_ir_mek_diss/FeatureServer/7/query?objectIds=140,141,142,143,144,145,146,147,148,149,150,151,152,153,154,155,156&outFields=*&outSR=4326&f=geojson`
- `ca_regional_councils.geojson` — Civil Administration of Judea and Samaria, regional council areas (`תחומי_מועצות_אזוריות_חופש_המידע_ע`, published under freedom of information; layer last edited 2026-07-29). 6 polygons keyed by `MUNICIPAL_DISTR`: 100 Shomron, 200 Mateh Binyamin, 300 Arvot HaYarden, 400 Gush Etzion, 500 Har Hevron, 600 Megilot (confirmed by member settlements). No terms of use stated.
  `https://services7.arcgis.com/LNelXmPD58p66zmN/ArcGIS/rest/services/תחומי_מועצות_אזוריות_חופש_המידע_ע/FeatureServer/0/query?where=1=1&outFields=*&outSR=4326&f=geojson`
- `ca_settlements.geojson` — Civil Administration, settlement jurisdiction orders (`צוי_בדבר_תחום_שיפוט_ישוב_חופש_המידע`, freedom of information; last edited 2026-09-24). 193 polygons: `NAME_NAME` (settlement), `MUNICIPAL_NAME` (council code; `1` = city or local council, `1000` = Ma'ale Adumim). No terms of use stated.
  `https://services7.arcgis.com/LNelXmPD58p66zmN/ArcGIS/rest/services/צוי_בדבר_תחום_שיפוט_ישוב_חופש_המידע/FeatureServer/0/query?where=1=1&outFields=*&outSR=4326&f=geojson`

Notes: 4 of the 6 council polygons and 64 of the 193 settlement polygons are invalid as published and are repaired (`make_valid`) before use. Council polygons overlap city and local-council areas; the build subtracts the cities and local councils from the councils.
