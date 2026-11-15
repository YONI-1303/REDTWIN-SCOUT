from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "mars" / "mola_meg128"

ROWS = 5632
COLS = 11520

topography_path = DATA / "megt00n090hb.img"
counts_path = DATA / "megc00n090hb.img"

# Verify the raw files before reading.
assert topography_path.exists(), "Topography file missing"
assert counts_path.exists(), "Observation-count file missing"

expected_topography_size = ROWS * COLS * 2
expected_counts_size = ROWS * COLS

assert topography_path.stat().st_size == expected_topography_size
assert counts_path.stat().st_size == expected_counts_size

print("=" * 60)
print("REDTWIN SCOUT — RAW MOLA DATA VALIDATION")
print("=" * 60)

# NASA PDS specifies MSB_INTEGER, 16-bit for topography.
topography = np.memmap(
    topography_path,
    dtype=">i2",
    mode="r",
    shape=(ROWS, COLS)
)

# NASA PDS specifies UNSIGNED_INTEGER, 8-bit for counts.
counts = np.memmap(
    counts_path,
    dtype=np.uint8,
    mode="r",
    shape=(ROWS, COLS)
)

print("\nTOPOGRAPHY")
print("Shape:", topography.shape)
print("Data type:", topography.dtype)

print("\nOBSERVATION COUNTS")
print("Shape:", counts.shape)
print("Data type:", counts.dtype)

# Inspect the same central 5x5 window in both rasters.
r = ROWS // 2 - 2
c = COLS // 2 - 2

print("\nTOPOGRAPHY SAMPLE:")
print(np.array(topography[r:r+5, c:c+5]))

print("\nOBSERVATION COUNT SAMPLE:")
print(np.array(counts[r:r+5, c:c+5]))

# Scan in small blocks to conserve memory.
histogram = np.zeros(256, dtype=np.uint64)

elevation_min = None
elevation_max = None
zero_elevation_count = 0

for start in range(0, ROWS, 128):
    end = min(start + 128, ROWS)

    elevation_block = topography[start:end, :]
    count_block = counts[start:end, :]

    block_min = int(elevation_block.min())
    block_max = int(elevation_block.max())

    elevation_min = (
        block_min if elevation_min is None
        else min(elevation_min, block_min)
    )

    elevation_max = (
        block_max if elevation_max is None
        else max(elevation_max, block_max)
    )

    zero_elevation_count += int(
        np.count_nonzero(elevation_block == 0)
    )

    histogram += np.bincount(
        count_block.ravel(),
        minlength=256
    ).astype(np.uint64)

total_pixels = ROWS * COLS
zero_counts = int(histogram[0])
observed_bins = total_pixels - zero_counts

print("\nFULL TILE SUMMARY")
print("Total pixels:", total_pixels)
print("Minimum elevation (m):", elevation_min)
print("Maximum elevation (m):", elevation_max)
print("Zero-valued elevation pixels:", zero_elevation_count)
print("Zero-observation bins:", zero_counts)
print("Bins with one or more observations:", observed_bins)
print("Maximum observation count:", int(histogram.max()))

print("\nVALIDATION COMPLETE")
print("Raw MOLA files interpreted using their PDS specifications.")
