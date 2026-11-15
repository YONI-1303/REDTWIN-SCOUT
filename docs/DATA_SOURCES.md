# Data sources

| Data | Files | Source | Notes |
|---|---|---|---|
| Mars topography | `data/raw/mars/mola_meg128/megt00n090hb.img/.lbl/.hdr/.xml` | NASA PDS, Mars Global Surveyor MOLA, data set `MGS-M-MOLA-5-MEGDR-L3-V1.0`, product version 2.0, producer MGS MOLA Team (D. E. Smith, GSFC) | Median observed elevation per 1/128° bin; empty bins hold interpolated values (stated in the label). Elevation relative to the GMM-3 areoid. |
| Mars counts | `megc00n090hb.img/.lbl/.hdr/.xml` | Same product family | Number of shots per bin (uint8). 0 = no direct observation. |
| Earth elevation | `data/raw/earth/srtmgl1/afar/*.tif`, `.../atacama/*.tif` (4 tiles each) | NASA/USGS SRTM 1 arc-second Global, v3 tiles | Heights relative to EGM96. No void values (`-32768` / `-32767`) found in either mosaic. |
| Mosaics | `data/processed/earth/*/..._2x2_mosaic.tif` | Built from the tiles above | 7201 × 7201, EPSG:4326 |
| Common-scale windows | `data/processed/common_scale/*.tif` | Built by `scripts/build_terrain_features.py` | Gale window verified identical to the raw MOLA cells. |
| Candidate tables | `data/processed/ai_candidates/*.csv` | `scripts/search_terrain_candidates.py` | Unchanged; SHA-256 checked in `tests/`. |
| Map basemaps | Esri World Imagery, OpenTopoMap, CARTO | Third-party tile servers | Display only, loaded by the browser. Not analysed. |

Reference landmarks (Dallol 14.242°N 40.300°E; San Pedro de Atacama 22.932°S 68.213°W) are sampling references used
in earlier scripts. They are drawn on the map but are not candidates.

Note: the MOLA `.hdr` files say `data ignore value = 0`. That is wrong for topography (0 m is a real elevation). The
pipeline reads the files with `numpy.memmap` and never treats 0 as nodata.
