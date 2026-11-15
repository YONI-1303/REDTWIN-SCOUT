"""Shared loaders and terrain-feature code for REDTWIN SCOUT.

Read-only with respect to the original research data. Anything derived is written
to data/processed/derived/ (new folder).
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
CAND_DIR = ROOT / "data/processed/ai_candidates"
SCALE_DIR = ROOT / "data/processed/common_scale"
DERIVED = ROOT / "data/processed/derived"

ROWS, COLS, STRIDE = 329, 320, 32
GALE_LAT = -5.44
DY = 463.0576672
DX = DY * math.cos(math.radians(abs(GALE_LAT)))

FEATURES = [
    "elevation_std_m",
    "relief_p95_p05_m",
    "slope_median_deg",
    "slope_p95_deg",
    "roughness_3x3_p95_m",
    "local_relief_11x11_p95_m",
]

FEATURE_LABELS = {
    "elevation_std_m": "Elevation std (m)",
    "relief_p95_p05_m": "Relief, P95-P05 (m)",
    "slope_median_deg": "Median slope (deg)",
    "slope_p95_deg": "P95 slope (deg)",
    "roughness_3x3_p95_m": "3x3 roughness, P95 (m)",
    "local_relief_11x11_p95_m": "11x11 local relief, P95 (m)",
}

REGIONS = {
    "Afar": {
        "mosaic": ROOT / "data/processed/earth/afar/afar_srtm_2x2_mosaic.tif",
        "epsg": 32637,
        "landmark": ("Dallol", 14.242, 40.300),
    },
    "Atacama": {
        "mosaic": ROOT / "data/processed/earth/atacama/atacama_srtm_2x2_mosaic.tif",
        "epsg": 32719,
        "landmark": ("San Pedro de Atacama", -22.93222, -68.21333),
    },
}

GALE_SITE = ("Gale Crater (Mars reference)", GALE_LAT, 137.70)


class DataMissing(RuntimeError):
    pass


def need(path: Path) -> Path:
    if not Path(path).exists():
        raise DataMissing(f"Missing project file: {path}")
    return Path(path)


def extract_features(elevation, dx=DX, dy=DY) -> dict:
    """The same six features as scripts/search_terrain_candidates.py."""
    from scipy.ndimage import maximum_filter, minimum_filter, uniform_filter

    z = np.asarray(elevation, dtype=np.float64)
    if not np.isfinite(z).all():
        raise ValueError("elevation contains missing cells")
    gy, gx = np.gradient(z, dy, dx)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    m = uniform_filter(z, size=3, mode="nearest")
    m2 = uniform_filter(z * z, size=3, mode="nearest")
    rough = np.sqrt(np.maximum(m2 - m * m, 0))
    lrel = maximum_filter(z, size=11, mode="nearest") - minimum_filter(z, size=11, mode="nearest")
    return {
        "elevation_std_m": float(np.std(z)),
        "relief_p95_p05_m": float(np.percentile(z, 95) - np.percentile(z, 5)),
        "slope_median_deg": float(np.median(slope)),
        "slope_p95_deg": float(np.percentile(slope, 95)),
        "roughness_3x3_p95_m": float(np.percentile(rough, 95)),
        "local_relief_11x11_p95_m": float(np.percentile(lrel, 95)),
    }


def load_tables():
    """Return (candidates, rankings, gale_reference). Raises DataMissing."""
    cand = pd.read_csv(need(CAND_DIR / "earth_candidate_features.csv"))
    rank = pd.read_csv(need(CAND_DIR / "provisional_similarity_rankings.csv"))
    gale = pd.read_csv(need(CAND_DIR / "gale_reference_features.csv"))
    df = rank.merge(
        cand[["candidate_id"] + FEATURES], on="candidate_id", how="left", validate="1:1"
    )
    return cand, df, gale


def load_gale_arrays():
    import rasterio

    with rasterio.open(need(SCALE_DIR / "gale_mola_window.tif")) as s:
        z = s.read(1).astype(np.float64)
    with rasterio.open(need(SCALE_DIR / "gale_mola_counts.tif")) as s:
        n = s.read(1)
    return z, n


def _grid(region: str):
    """Common metric grid used by the original search (same maths)."""
    import rasterio
    from rasterio.warp import transform_bounds

    info = REGIONS[region]
    crs = f"EPSG:{info['epsg']}"
    with rasterio.open(need(info["mosaic"])) as src:
        b = transform_bounds(src.crs, crs, *src.bounds, densify_pts=41)
    left = math.floor(b[0] / DX) * DX
    bottom = math.floor(b[1] / DY) * DY
    right = math.ceil(b[2] / DX) * DX
    top = math.ceil(b[3] / DY) * DY
    return left, top, math.ceil((right - left) / DX), math.ceil((top - bottom) / DY)


def region_surface(region: str) -> np.ndarray:
    """463 m common-scale surface for a region (cached to data/processed/derived)."""
    cache = DERIVED / f"{region.lower()}_common_scale.npy"
    if cache.exists():
        return np.load(cache)
    import rasterio
    from affine import Affine
    from rasterio.warp import Resampling, reproject

    info = REGIONS[region]
    left, top, w, h = _grid(region)
    out = np.full((h, w), np.nan, dtype=np.float32)
    with rasterio.open(need(info["mosaic"])) as src:
        reproject(
            source=rasterio.band(src, 1), destination=out,
            src_transform=src.transform, src_crs=src.crs, src_nodata=src.nodata,
            dst_transform=Affine(DX, 0, left, 0, -DY, top), dst_crs=f"EPSG:{info['epsg']}",
            dst_nodata=np.nan, resampling=Resampling.average, num_threads=1, warp_mem_limit=128,
        )
    DERIVED.mkdir(parents=True, exist_ok=True)
    np.save(cache, out)
    return out


def candidate_rowcol(region: str, lat: float, lon: float):
    from pyproj import Transformer

    left, top, _, _ = _grid(region)
    x, y = Transformer.from_crs("EPSG:4326", f"EPSG:{REGIONS[region]['epsg']}", always_xy=True).transform(lon, lat)
    c = int(round((x - left) / DX - COLS / 2))
    r = int(round((top - y) / DY - ROWS / 2))
    return r, c


def candidate_window(region: str, lat: float, lon: float) -> np.ndarray:
    r, c = candidate_rowcol(region, lat, lon)
    return region_surface(region)[r:r + ROWS, c:c + COLS]


def window_footprint(region: str, lat: float, lon: float):
    """Exact lat/lon corners of a candidate's 329x320 window on the common grid."""
    from pyproj import Transformer

    left, top, _, _ = _grid(region)
    r, c = candidate_rowcol(region, lat, lon)
    x0, x1 = left + c * DX, left + (c + COLS) * DX
    y0, y1 = top - r * DY, top - (r + ROWS) * DY
    back = Transformer.from_crs(f"EPSG:{REGIONS[region]['epsg']}", "EPSG:4326", always_xy=True)
    pts = [back.transform(x, y) for x, y in [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]]
    return [(la, lo) for lo, la in pts]


def window_arrays(z: np.ndarray, dx=DX, dy=DY) -> dict:
    """Per-cell slope, roughness and local relief (for distribution plots)."""
    from scipy.ndimage import maximum_filter, minimum_filter, uniform_filter

    z = np.asarray(z, dtype=np.float64)
    gy, gx = np.gradient(z, dy, dx)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    m = uniform_filter(z, size=3, mode="nearest")
    m2 = uniform_filter(z * z, size=3, mode="nearest")
    rough = np.sqrt(np.maximum(m2 - m * m, 0))
    lrel = maximum_filter(z, size=11, mode="nearest") - minimum_filter(z, size=11, mode="nearest")
    return {"elevation": z, "slope": slope, "roughness": rough, "local_relief": lrel}


def breakdown(candidate_row, gale_ref, cand_table) -> pd.DataFrame:
    """Per-feature comparison using the original scaler (fit on Gale + all candidates)."""
    X = cand_table[FEATURES].to_numpy(float)
    G = gale_ref[FEATURES].to_numpy(float)[0]
    pool = np.vstack([G, X])
    mu, sd = pool.mean(0), pool.std(0)
    c = np.array([candidate_row[f] for f in FEATURES], float)
    dz = (c - G) / sd
    contrib = dz ** 2 / (dz ** 2).sum() * 100
    return pd.DataFrame({
        "feature": FEATURES, "label": [FEATURE_LABELS[f] for f in FEATURES],
        "candidate": c, "gale": G, "difference": c - G,
        "difference_pct_of_gale": (c - G) / G * 100,
        "std_units": dz, "share_of_distance_pct": contrib,
    })
