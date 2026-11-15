from pathlib import Path
import math

import numpy as np
import pandas as pd
import rasterio

from affine import Affine
from rasterio.warp import reproject, transform_bounds, Resampling
from pyproj import Transformer
from scipy.ndimage import (
    uniform_filter,
    maximum_filter,
    minimum_filter,
)
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import NearestNeighbors

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data/processed/common_scale"

MOSAICS = [
    {
        "region": "Afar",
        "path": ROOT / "data/processed/earth/afar/afar_srtm_2x2_mosaic.tif",
        "epsg": 32637,
    },
    {
        "region": "Atacama",
        "path": ROOT / "data/processed/earth/atacama/atacama_srtm_2x2_mosaic.tif",
        "epsg": 32719,
    },
]

ROWS = 329
COLS = 320
STRIDE = 32

GALE_LAT = -5.44

# Match the original MOLA physical grid spacing at Gale.
DX = 463.0576672 * math.cos(math.radians(abs(GALE_LAT)))
DY = 463.0576672

FEATURES = [
    "elevation_std_m",
    "relief_p95_p05_m",
    "slope_median_deg",
    "slope_p95_deg",
    "roughness_3x3_p95_m",
    "local_relief_11x11_p95_m",
]

OUTPUT = ROOT / "data/processed/ai_candidates"


def extract_features(elevation, dx, dy):

    z = np.asarray(elevation, dtype=np.float64)

    if not np.isfinite(z).all():
        raise ValueError("Candidate contains missing elevation data.")

    dz_dy, dz_dx = np.gradient(z, dy, dx)

    slope = np.degrees(
        np.arctan(np.hypot(dz_dx, dz_dy))
    )

    mean = uniform_filter(z, size=3, mode="nearest")
    mean_sq = uniform_filter(z * z, size=3, mode="nearest")

    roughness = np.sqrt(
        np.maximum(mean_sq - mean * mean, 0)
    )

    local_max = maximum_filter(z, size=11, mode="nearest")
    local_min = minimum_filter(z, size=11, mode="nearest")

    local_relief = local_max - local_min

    return {
        "elevation_std_m": float(np.std(z)),
        "relief_p95_p05_m": float(
            np.percentile(z, 95) - np.percentile(z, 5)
        ),
        "slope_median_deg": float(np.median(slope)),
        "slope_p95_deg": float(np.percentile(slope, 95)),
        "roughness_3x3_p95_m": float(
            np.percentile(roughness, 95)
        ),
        "local_relief_11x11_p95_m": float(
            np.percentile(local_relief, 95)
        ),
    }


def positions(length, window, stride):

    last = length - window

    if last < 0:
        return []

    result = list(range(0, last + 1, stride))

    if result[-1] != last:
        result.append(last)

    return result


def load_gale():

    elevation_path = DATA / "gale_mola_window.tif"
    counts_path = DATA / "gale_mola_counts.tif"

    with rasterio.open(elevation_path) as src:
        elevation = src.read(1).astype(np.float64)

        dx = abs(src.transform.a) * math.cos(
            math.radians(abs(GALE_LAT))
        )
        dy = abs(src.transform.e)

    with rasterio.open(counts_path) as src:
        counts = src.read(1)

    if elevation.shape != (ROWS, COLS):
        raise ValueError("Unexpected Gale window dimensions.")

    coverage = float(np.mean(counts > 0) * 100)

    return extract_features(elevation, dx, dy), coverage


def build_candidates(region):

    name = region["region"]
    path = region["path"]
    epsg = region["epsg"]
    crs = f"EPSG:{epsg}"

    print(f"\nSEARCHING REGION: {name}")

    reverse = Transformer.from_crs(
        crs,
        "EPSG:4326",
        always_xy=True
    )

    candidates = []

    with rasterio.open(path) as src:

        bounds = transform_bounds(
            src.crs,
            crs,
            *src.bounds,
            densify_pts=41
        )

        left = math.floor(bounds[0] / DX) * DX
        bottom = math.floor(bounds[1] / DY) * DY
        right = math.ceil(bounds[2] / DX) * DX
        top = math.ceil(bounds[3] / DY) * DY

        width = math.ceil((right - left) / DX)
        height = math.ceil((top - bottom) / DY)

        transform = Affine(
            DX, 0, left,
            0, -DY, top
        )

        coarse = np.full(
            (height, width),
            np.nan,
            dtype=np.float32
        )

        print("Reprojecting to common metric scale...")

        reproject(
            source=rasterio.band(src, 1),
            destination=coarse,
            src_transform=src.transform,
            src_crs=src.crs,
            src_nodata=src.nodata,
            dst_transform=transform,
            dst_crs=crs,
            dst_nodata=np.nan,
            resampling=Resampling.average,
            num_threads=1,
            warp_mem_limit=128,
        )

    row_positions = positions(height, ROWS, STRIDE)
    col_positions = positions(width, COLS, STRIDE)

    if not row_positions or not col_positions:
        raise ValueError(f"{name}: mosaic too small for a Gale-sized window.")

    print("Common-scale dimensions:", coarse.shape)
    print("Candidate grid:", len(row_positions), "x", len(col_positions))

    number = 0

    for r in row_positions:
        for c in col_positions:

            window = coarse[r:r+ROWS, c:c+COLS]

            finite_mask = np.isfinite(window)
            coverage = float(finite_mask.mean() * 100)

            # Only accept windows with complete elevation coverage.
            if not finite_mask.all():
                continue

            features = extract_features(window, DX, DY)

            center_x = left + (c + COLS / 2) * DX
            center_y = top - (r + ROWS / 2) * DY

            lon, lat = reverse.transform(center_x, center_y)

            number += 1

            candidates.append({
                "candidate_id": f"{name}_{number:04d}",
                "region": name,
                "center_lat": lat,
                "center_lon": lon,
                "valid_coverage_pct": coverage,
                **features,
            })

    print("Accepted candidates:", len(candidates))

    return candidates


def main():

    OUTPUT.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("REDTWIN SCOUT — EXPLAINABLE TERRAIN SEARCH")
    print("=" * 65)

    gale, mola_coverage = load_gale()

    print("\nGALE REFERENCE")
    print("Direct observation coverage:", round(mola_coverage, 2), "%")

    candidates = []

    for region in MOSAICS:
        candidates.extend(build_candidates(region))

    if len(candidates) < 5:
        raise ValueError("Insufficient Earth candidates for exploratory search.")

    frame = pd.DataFrame(candidates)

    if not np.isfinite(frame[FEATURES].to_numpy()).all():
        raise ValueError("Candidate feature table contains invalid values.")

    feature_matrix = frame[FEATURES].to_numpy(dtype=np.float64)

    reference = np.array(
        [[gale[key] for key in FEATURES]],
        dtype=np.float64
    )

    # Fit one scaler across the reference and Earth candidate population.
    scaler = StandardScaler()

    combined = np.vstack([reference, feature_matrix])
    scaled = scaler.fit_transform(combined)

    gale_scaled = scaled[:1]
    earth_scaled = scaled[1:]

    # Search all Earth candidates from both regions.
    model = NearestNeighbors(
        n_neighbors=len(frame),
        metric="euclidean",
        algorithm="brute",
    )

    model.fit(earth_scaled)

    distances, indices = model.kneighbors(gale_scaled)

    rankings = []

    for rank, (distance, index) in enumerate(
        zip(distances[0], indices[0]), start=1
    ):

        candidate = frame.iloc[index]

        differences = (
            earth_scaled[index] - gale_scaled[0]
        ) ** 2

        total_difference = differences.sum()

        if total_difference > 0:
            contributions = differences / total_difference * 100
        else:
            contributions = np.zeros(len(FEATURES))

        explanation_order = np.argsort(contributions)[::-1]

        explanation = "; ".join(
            f"{FEATURES[i]} ({contributions[i]:.1f}%)"
            for i in explanation_order[:3]
        )

        rankings.append({
            "rank": rank,
            "candidate_id": candidate["candidate_id"],
            "region": candidate["region"],
            "center_lat": candidate["center_lat"],
            "center_lon": candidate["center_lon"],
            "standardized_distance": float(distance),
            "main_feature_differences": explanation,
            "candidate_valid_coverage_pct": candidate["valid_coverage_pct"],
            "gale_direct_observation_coverage_pct": mola_coverage,
            "interpretation": "EXPLORATORY — MOLA interpolation sensitivity not yet tested",
        })

    ranking_frame = pd.DataFrame(rankings)

    frame.to_csv(
        OUTPUT / "earth_candidate_features.csv",
        index=False
    )

    ranking_frame.to_csv(
        OUTPUT / "provisional_similarity_rankings.csv",
        index=False
    )

    pd.DataFrame([gale]).to_csv(
        OUTPUT / "gale_reference_features.csv",
        index=False
    )

    print("\n" + "=" * 65)
    print("EXPLORATORY NEAREST-NEIGHBOR RESULTS")
    print("=" * 65)

    print("Earth candidates:", len(frame))
    print("Afar candidates:", int((frame.region == "Afar").sum()))
    print("Atacama candidates:", int((frame.region == "Atacama").sum()))

    print("\nTOP 10 CANDIDATES")

    print(
        ranking_frame.head(10)[
            [
                "rank",
                "region",
                "center_lat",
                "center_lon",
                "standardized_distance",
                "main_feature_differences",
            ]
        ].round(4).to_string(index=False)
    )

    print("\nFILES SAVED:")
    print(OUTPUT)

    print("\nIMPORTANT:")
    print("Lower standardized distance indicates closer feature profiles.")
    print("It is NOT a probability or percentage similarity.")
    print("Rankings are exploratory, not validated Mars analog claims.")
    print("Test MOLA interpolation sensitivity before making conclusions.")


if __name__ == "__main__":
    main()
