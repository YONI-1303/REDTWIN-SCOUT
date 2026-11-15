# Test report

All results below are from runs we actually performed on 15 Nov 2026.

**Environment:** Linux sandbox, Python 3.12.3. Package versions identical to your `.venv` (numpy 2.5.4, scipy 1.18.1, scikit-learn 1.9.1,
rasterio 1.5.2, pyproj 3.8.0, streamlit 1.67.0, plotly 7.1.0, folium 0.20.0, streamlit-folium 0.27.4) **except pandas 3.0.6 here vs 3.1.1 on your machine**.

## Automated tests: `python -m pytest tests -q` → 11 passed
| Test | What it checks |
|---|---|
| `test_original_csvs_unchanged` | SHA-256 of the three original CSVs equals the hashes from the uploaded ZIP |
| `test_candidate_counts_and_consistency` | 36 rows, unique IDs, 20 Afar / 16 Atacama, ranks 1–36 sorted, Gale coverage 29.109%, best Afar 8.437698 and best Atacama 9.212852 |
| `test_coordinates_inside_study_mosaics` | every candidate centre lies inside its 2° × 2° mosaic |
| `test_rankings_reproduce_from_features` | distances recomputed from feature CSV match the stored ranking (1e-9) |
| `test_raster_dimensions_and_gale_window` | four common-scale rasters are 329 × 320; Gale coverage recomputed from the raster |
| `test_regenerated_windows_match_saved_features` | all 36 windows regenerated from SRTM reproduce the stored features (rtol 1e-9) |
| `test_breakdown_shares_sum_to_100` | per-feature contribution sums to 100%; relief is the top contributor for rank 1 |
| `test_missing_file_message` | missing file raises a readable error |
| `test_every_page_renders_without_exception` | all six pages run headless; the 29.11% warning is present on each |
| `test_region_switching_and_candidate_selection` | Afar ↔ Atacama switching (Afar 20 and Atacama 16 candidates in the dropdown), selecting several candidates |
| `test_all_basemaps` | app builds with each of the four basemap options |

## Other checks run
- Streamlit server started headless: health endpoint returned `ok`, index page HTTP 200.
- App copied to a folder without any data: no exception; shows "Missing project file: …".
- Validation tables, docs and derived cache removed: all pages still render, cache rebuilt on demand.
- Independent recomputation of the Gale window from raw MOLA files: identical to the saved window and counts; coverage 29.109%.
- Peak memory for a full six-page pass: 288 MB.

## Known issues and risks
1. **Not run on your machine** (Windows 11, Python 3.14.7). Pure-Python code and the same package versions, but first run on Windows is the real test.
2. **The map was not seen in a real browser.** Streamlit's test harness doesn't execute the map component. Marker-click selection, tile loading, marker colours, footprint
   and legend were not exercised by tests. The dropdown (same selection state) is tested. **Do a 2-minute click-through before submitting.**
3. No visual / screenshot review of layout was possible. Expect some styling tweaks.
4. Basemaps need internet; "None (offline)" is the fallback.
5. First run creates `data/processed/derived/*.npy` if missing (about 5 s per region) and needs the SRTM mosaics.
6. The app's map-click selection relies on the marker tooltip text (`ID | rank | d`). Don't change the tooltip format.
7. Scientific caveats are in `docs/SCIENTIFIC_LIMITATIONS.md`; they matter more than any software issue.

## Launch
```powershell
cd C:\dev\REDTWIN_SCOUT
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```
