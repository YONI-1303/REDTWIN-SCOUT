from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "mars" / "mola_meg128"

ROWS = 5632
COLS = 11520

topography = np.memmap(
    DATA / "megt00n090hb.img",
    dtype=">i2",
    mode="r",
    shape=(ROWS, COLS)
)

counts = np.memmap(
    DATA / "megc00n090hb.img",
    dtype=np.uint8,
    mode="r",
    shape=(ROWS, COLS)
)

histogram = np.zeros(256, dtype=np.uint64)

zero_elevation_count = 0
zero_elevation_observed = 0
zero_elevation_unobserved = 0

for start in range(0, ROWS, 128):
    end = min(start + 128, ROWS)

    elevation = topography[start:end, :]
    observation_count = counts[start:end, :]

    histogram += np.bincount(
        observation_count.ravel(),
        minlength=256
    ).astype(np.uint64)

    zero = elevation == 0

    zero_elevation_count += int(np.count_nonzero(zero))

    zero_elevation_observed += int(
        np.count_nonzero(zero & (observation_count > 0))
    )

    zero_elevation_unobserved += int(
        np.count_nonzero(zero & (observation_count == 0))
    )

total = ROWS * COLS

maximum_count_value = int(np.flatnonzero(histogram)[-1])

print("=" * 55)
print("REDTWIN SCOUT — MOLA DATA QUALITY REPORT")
print("=" * 55)

print("\nOBSERVATION COVERAGE")
print("Zero-observation bins:", int(histogram[0]))
print("Observed bins:", total - int(histogram[0]))
print("Direct coverage (%):", round(
    (total - int(histogram[0])) / total * 100, 2
))

print("\nOBSERVATION COUNT DISTRIBUTION")
print("Maximum actual count value:", maximum_count_value)
print("Number of bins having that count:",
      int(histogram[maximum_count_value]))

print("\nZERO ELEVATION INVESTIGATION")
print("Total zero-elevation pixels:", zero_elevation_count)
print("Zero elevation with observations:", zero_elevation_observed)
print("Zero elevation without observations:", zero_elevation_unobserved)

print("\nVALIDATION FINISHED")
