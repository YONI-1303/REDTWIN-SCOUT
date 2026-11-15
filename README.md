# REDTWIN SCOUT

**Earth–Mars terrain analogue discovery.** NASA Space Apps Challenge entry.

REDTWIN SCOUT compares the terrain of a Mars reference site (Gale Crater) with Gale-sized windows cut from two
Earth study areas, Afar (Horn of Africa) and the Atacama (Chile), and ranks the windows by how close six terrain
measurements are to Gale's. The Streamlit app lets you pick a region, click a candidate on a map, see why it
ranked where it did, and compare its terrain with Gale's using the actual raster data.

## What you should know before using the results

- Only **29.11%** of Gale's window cells hold a direct MOLA measurement. The rest is interpolated by the data producer.
- The distance is a standardised distance. It is not a probability or a percentage.
- **No Earth window is close to Gale.** Gale's relief (4,435 m) is outside everything in the Earth set (max 2,763 m).
- Afar ranks first in the original ranking, but that lead holds in only **10 of 28** method variants we tried. See `docs/VALIDATION_REPORT.md`.
- Only the two included 2° × 2° SRTM mosaics were searched. This is not a search of all Earth.
- No lunar comparison has been done.

## Run it (Windows PowerShell)

```powershell
cd C:\dev\REDTWIN_SCOUT
.\.venv\Scripts\Activate.ps1          # if blocked: Set-ExecutionPolicy -Scope Process Bypass
streamlit run app.py
```

If activation is blocked you can skip it: `.\.venv\Scripts\python.exe -m streamlit run app.py`.
Your `.venv` already has every package needed. `requirements.txt` is pinned to the versions in it.

Optional:

```powershell
pip install -r requirements-dev.txt     # pytest only
python -m pytest tests -q               # 11 tests, ~10 s
python scripts\run_validation.py        # regenerates outputs\validation\ (~1 min)
```

## Layout

| Path | What |
|---|---|
| `app.py` | The Streamlit app (six sections) |
| `src/redtwin_core.py` | Loaders, feature extraction, window regeneration |
| `scripts/` | Original data pipeline (unchanged) + `run_validation.py` (new) |
| `data/processed/ai_candidates/` | Original rankings and features (unchanged, hash-tested) |
| `data/processed/derived/` | Cached 463 m surfaces, created on first run if absent |
| `outputs/validation/` | Sensitivity-analysis tables |
| `docs/` | Methods, data sources, limitations, validation report, demo script, presentation outline |
| `tests/` | Data-integrity and app tests |

## Offline use

Map basemaps (Esri, OpenTopoMap, CARTO) need internet. Choose **None (offline)** in the Basemap box and the
markers, study-area boundary and window footprints still draw. All analysis is local.
