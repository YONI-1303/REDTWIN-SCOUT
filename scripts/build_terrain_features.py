from pathlib import Path
import math

import numpy as np
import pandas as pd
import rasterio

from affine import Affine
from rasterio.windows import Window
from rasterio.warp import reproject, Resampling
from pyproj import Transformer
from scipy.ndimage import (
    uniform_filter,
    maximum_filter,
    minimum_filter,
)

ROOT = Path(__file__).resolve().parents[1]

MOLA_DIR = ROOT / "data/raw/mars/mola_meg128"

AFAR_MOSAIC = (
    ROOT / "data/processed/earth/afar/afar_srtm_2x2_mosaic.tif"
)

ATACAMA_MOSAIC = (
    ROOT / "data/processed/earth/atacama/atacama_srtm_2x2_mosaic.tif"
)

OUT = ROOT / "data/processed/common_scale"

# Common dimensions for every study region.
ROWS = 329
COLS = 320

# MOLA grid spacing from the original ENVI header.
MOLA_PIXEL_M = 463.0576672

# Gale reference location.
GALE_LAT = -5.44
GALE_LON = 137.70
MARS_RADIUS = 3396000.0

# Match local physical east-west spacing at Gale.
DX = MOLA_PIXEL_M * math.cos(math.radians(abs(GALE_LAT)))
DY = MOLA_PIXEL_M

SITES = [
    {
        "name": "Dallol_Afar",
        "path": AFAR_MOSAIC,
        "lat": 14.242,
        "lon": 40.300,
        "epsg": 32637,
    },
    {
        "name": "SanPedro_Atacama",
        "path": ATACAMA_MOSAIC,
        "lat": -22.93222,
        "lon": -68.21333,
        "epsg": 32719,
    },
]


def calculate_features(name, elevation, direct_counts=None):

    elevation = np.asarray(elevation, dtype=np.float32)

    if not np.isfinite(elevation).all():
        raise ValueError(
            f"{name}: missing cells detected. "
            "Investigate before calculating terrain features."
        )

    # Calculate terrain gradients using physical distances.
    dz_dy, dz_dx = np.gradient(
        elevation,
        DY,
        DX
    )

    slope = np.degrees(
        np.arctan(
            np.hypot(dz_dx, dz_dy)
        )
    )

    # Roughness: local 3x3 elevation standard deviation.
    local_mean = uniform_filter(
        elevation,
        size=3,
        mode="nearest"
    )

    local_mean_sq = uniform_filter(
        elevation ** 2,
        size=3,
        mode="nearest"
    )

    roughness = np.sqrt(
        np.maximum(local_mean_sq - local_mean ** 2, 0)
    )

    # Local relief: maximum minus minimum in an 11x11 window.
    local_max = maximum_filter(
        elevation,
        size=11,
        mode="nearest"
    )

    local_min = minimum_filter(
        elevation,
        size=11,
        mode="nearest"
    )

    local_relief = local_max - local_min

    # Absolute elevation is reported for context,
    # but will NOT be used in Earth-Mars similarity.
    result = {
        "site": name,
        "rows": ROWS,
        "columns": COLS,
        "pixel_x_m": DX,
        "pixel_y_m": DY,
        "valid_coverage_pct": 100.0,

        "elevation_mean_m": float(np.mean(elevation)),
        "elevation_median_m": float(np.median(elevation)),
        "elevation_std_m": float(np.std(elevation)),

        "elevation_p05_m": float(np.percentile(elevation, 5)),
        "elevation_p95_m": float(np.percentile(elevation, 95)),

        "relief_p95_p05_m": float(
            np.percentile(elevation, 95)
            - np.percentile(elevation, 5)
        ),

        "slope_mean_deg": float(np.mean(slope)),
        "slope_median_deg": float(np.median(slope)),
        "slope_p95_deg": float(np.percentile(slope, 95)),

        "roughness_3x3_median_m": float(np.median(roughness)),
        "roughness_3x3_p95_m": float(
            np.percentile(roughness, 95)
        ),

        "local_relief_11x11_p95_m": float(
            np.percentile(local_relief, 95)
        ),
    }

    if direct_counts is not None:

        observed = direct_counts > 0

        result["direct_observation_coverage_pct"] = (
            float(np.mean(observed) * 100)
        )

        direct_elevation = elevation[observed]

        if direct_elevation.size:
            result["direct_elevation_std_m"] = float(
                np.std(direct_elevation)
            )
        else:
            result["direct_elevation_std_m"] = np.nan

    else:
        result["direct_observation_coverage_pct"] = np.nan
        result["direct_elevation_std_m"] = np.nan

    return result


def build_gale():

    print("\n[1/3] EXTRACTING GALE CRATER")

    topo_path = MOLA_DIR / "megt00n090hb.img"
    count_path = MOLA_DIR / "megc00n090hb.img"

    if topo_path.stat().st_size != 129761280:
        raise ValueError("Unexpected MOLA topography file size")

    if count_path.stat().st_size != 64880640:
        raise ValueError("Unexpected MOLA counts file size")

    with rasterio.open(topo_path) as src:

        # MOLA simple cylindrical projection:
        # x = R * (longitude - central meridian)
        # y = R * latitude
        x = MARS_RADIUS * math.radians(GALE_LON - 180.0)
        y = MARS_RADIUS * math.radians(GALE_LAT)

        center_row, center_col = src.index(x, y)

        row_start = center_row - ROWS // 2
        col_start = center_col - COLS // 2

        if (
            row_start < 0
            or col_start < 0
            or row_start + ROWS > src.height
            or col_start + COLS > src.width
        ):
            raise ValueError("Gale window outside MOLA tile")

        window = Window(
            col_start,
            row_start,
            COLS,
            ROWS
        )

        transform = src.window_transform(window)
        mars_crs = src.crs

    # Read PDS files using their CORRECT original data types.
    topo_raw = np.memmap(
        topo_path,
        dtype=">i2",
        mode="r",
        shape=(5632, 11520)
    )

    counts_raw = np.memmap(
        count_path,
        dtype=np.uint8,
        mode="r",
        shape=(5632, 11520)
    )

    raw_elevation = topo_raw[
        row_start:row_start + ROWS,
        col_start:col_start + COLS
    ]

    counts = np.asarray(
        counts_raw[
            row_start:row_start + ROWS,
            col_start:col_start + COLS
        ]
    )

    elevation = np.asarray(
        raw_elevation,
        dtype=np.float32
    )

    OUT.mkdir(parents=True, exist_ok=True)

    # Do not declare zero elevation as NoData.
    profile = {
        "driver": "GTiff",
        "height": ROWS,
        "width": COLS,
        "count": 1,
        "dtype": "int16",
        "crs": mars_crs,
        "transform": transform,
        "nodata": None,
        "compress": "deflate",
        "predictor": 2,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }

    with rasterio.open(
        OUT / "gale_mola_window.tif",
        "w",
        **profile
    ) as dst:

        dst.write(
            np.asarray(raw_elevation, dtype=np.int16),
            1
        )

        dst.update_tags(
            SOURCE="NASA MOLA MEG128",
            NOTE="Original elevation values; zero retained"
        )

    count_profile = profile.copy()
    count_profile.update(dtype="uint8", predictor=1)

    with rasterio.open(
        OUT / "gale_mola_counts.tif",
        "w",
        **count_profile
    ) as dst:

        dst.write(counts, 1)

        dst.update_tags(
            SOURCE="NASA MOLA MEG128 counts",
            NOTE="Zero means no direct observations"
        )

    features = calculate_features(
        "Gale_Mars",
        elevation,
        counts
    )

    print("Gale dimensions:", elevation.shape)
    print(
        "Direct observation coverage:",
        round(features["direct_observation_coverage_pct"], 2),
        "%"
    )

    return features


def build_earth(site):

    print(f"\n[EARTH] EXTRACTING {site['name']}")

    transformer = Transformer.from_crs(
        "EPSG:4326",
        f"EPSG:{site['epsg']}",
        always_xy=True
    )

    center_x, center_y = transformer.transform(
        site["lon"],
        site["lat"]
    )

    # Exact physical dimensions shared with the Gale window.
    dst_transform = Affine(
        DX,
        0,
        center_x - COLS * DX / 2,
        0,
        -DY,
        center_y + ROWS * DY / 2
    )

    elevation = np.full(
        (ROWS, COLS),
        np.nan,
        dtype=np.float32
    )

    with rasterio.open(site["path"]) as src:

        reproject(
            source=rasterio.band(src, 1),
            destination=elevation,

            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,

            dst_transform=dst_transform,
            dst_crs=f"EPSG:{site['epsg']}",
            dst_nodata=np.nan,

            resampling=Resampling.average,

            num_threads=1,
            warp_mem_limit=128
        )

    valid_coverage = float(
        np.isfinite(elevation).mean() * 100
    )

    print("Dimensions:", elevation.shape)
    print("UTM EPSG:", site["epsg"])
    print("Valid coverage:", round(valid_coverage, 2), "%")

    if valid_coverage < 99.9:
        raise ValueError(
            f"{site['name']}: incomplete comparison window. "
            "Inspect tile coverage before continuing."
        )

    profile = {
        "driver": "GTiff",
        "height": ROWS,
        "width": COLS,
        "count": 1,
        "dtype": "float32",
        "crs": f"EPSG:{site['epsg']}",
        "transform": dst_transform,
        "nodata": float("nan"),
        "compress": "deflate",
        "predictor": 3,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    }

    output_name = site["name"].lower() + "_463m.tif"

    output_path = OUT / output_name

    with rasterio.open(
        output_path,
        "w",
        **profile
    ) as dst:

        dst.write(elevation, 1)

        dst.update_tags(
            SOURCE="USGS SRTM 1 Arc-Second Global",
            RESAMPLING="Average",
            TARGET_SPACING="Comparable to MOLA MEG128 at Gale",
            VERTICAL_REFERENCE="EGM96"
        )

    features = calculate_features(
        site["name"],
        elevation
    )

    features["valid_coverage_pct"] = valid_coverage

    print(
        "Elevation range:",
        round(float(np.nanmin(elevation)), 2),
        "to",
        round(float(np.nanmax(elevation)), 2),
        "m"
    )

    return features


def main():

    print("=" * 65)
    print("REDTWIN SCOUT — COMMON-SCALE TERRAIN FEATURE ENGINE")
    print("=" * 65)

    OUT.mkdir(parents=True, exist_ok=True)

    required = [
        AFAR_MOSAIC,
        ATACAMA_MOSAIC,
        MOLA_DIR / "megt00n090hb.img",
        MOLA_DIR / "megc00n090hb.img",
    ]

    for path in required:
        if not path.exists():
            raise FileNotFoundError(path)

    features = []

    # Mars first.
    features.append(build_gale())

    # Earth candidates.
    for site in SITES:
        features.append(build_earth(site))

    frame = pd.DataFrame(features)

    csv_path = OUT / "terrain_features.csv"

    frame.to_csv(csv_path, index=False)

    print("\n" + "=" * 65)
    print("TERRAIN FEATURE EXTRACTION COMPLETE")
    print("=" * 65)

    display_columns = [
        "site",
        "elevation_std_m",
        "relief_p95_p05_m",
        "slope_median_deg",
        "slope_p95_deg",
        "roughness_3x3_p95_m",
        "local_relief_11x11_p95_m",
        "direct_observation_coverage_pct",
    ]

    print("\nCOMPARISON TABLE")
    print(frame[display_columns].round(3).to_string(index=False))

    print("\nCSV SAVED:")
    print(csv_path)

    print("\nPROCESSED RASTERS:")
    print(OUT)


if __name__ == "__main__":
    main()
