from pathlib import Path
import numpy as np
import math

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "raw" / "mars" / "mola_meg128"

ROWS = 5632
COLS = 11520
PPD = 128

# Approximate Gale crater extent from USGS.
NORTH = -4.05
SOUTH = -6.62
WEST = 136.40
EAST = 138.90

CENTER_LAT = -5.44
CENTER_LON = 137.70

# Read the original binary files using NASA's PDS specifications.
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

# Convert geographic boundaries to zero-based pixel indices.
# Pixel centers are at half-pixel offsets.
r0 = math.ceil((-NORTH) * PPD - 0.5)
r1 = math.floor((-SOUTH) * PPD - 0.5)

c0 = math.ceil((WEST - 90.0) * PPD - 0.5)
c1 = math.floor((EAST - 90.0) * PPD - 0.5)

assert 0 <= r0 <= r1 < ROWS
assert 0 <= c0 <= c1 < COLS

# Read only Gale's rectangular bounding window.
elev = np.asarray(topography[r0:r1+1, c0:c1+1])
obs = np.asarray(counts[r0:r1+1, c0:c1+1])

observed = obs > 0
unobserved = obs == 0

total = elev.size
observed_total = int(np.count_nonzero(observed))
unobserved_total = int(np.count_nonzero(unobserved))

# Identify the nearest pixel to the crater center.
center_row = round((-CENTER_LAT) * PPD - 0.5)
center_col = round((CENTER_LON - 90.0) * PPD - 0.5)

# Extract 5x5 center samples.
sample_elev = np.asarray(
    topography[
        center_row-2:center_row+3,
        center_col-2:center_col+3
    ]
)

sample_counts = np.asarray(
    counts[
        center_row-2:center_row+3,
        center_col-2:center_col+3
    ]
)

# Count distribution within Gale's bounding rectangle.
histogram = np.bincount(
    obs.ravel(),
    minlength=256
)

max_count = int(np.flatnonzero(histogram)[-1])

print("=" * 60)
print("REDTWIN SCOUT — GALE CRATER DATA INVESTIGATION")
print("=" * 60)

print("\nGEOGRAPHIC WINDOW")
print("Latitude:", SOUTH, "to", NORTH)
print("Longitude:", WEST, "to", EAST)
print("Rows:", r0, "to", r1)
print("Columns:", c0, "to", c1)
print("Window dimensions:", elev.shape)

print("\nCRATER CENTER")
print("Center coordinates:", CENTER_LAT, CENTER_LON)
print("Center pixel:", center_row, center_col)

print("\nOBSERVATION COVERAGE")
print("Total bins:", total)
print("Observed bins:", observed_total)
print("Unobserved bins:", unobserved_total)
print("Direct coverage (%):", round(
    observed_total / total * 100, 2
))

print("\nELEVATION STATISTICS — ALL BINS")
print("Minimum (m):", int(elev.min()))
print("Maximum (m):", int(elev.max()))
print("Median (m):", float(np.median(elev)))

print("\nELEVATION STATISTICS — DIRECTLY OBSERVED")
observed_elev = elev[observed].astype(np.float64)
print("Minimum (m):", float(observed_elev.min()))
print("Maximum (m):", float(observed_elev.max()))
print("Median (m):", float(np.median(observed_elev)))

print("\nELEVATION STATISTICS — NO DIRECT OBSERVATIONS")
unobserved_elev = elev[unobserved].astype(np.float64)
print("Minimum (m):", float(unobserved_elev.min()))
print("Maximum (m):", float(unobserved_elev.max()))
print("Median (m):", float(np.median(unobserved_elev)))

print("\nOBSERVATION COUNT DISTRIBUTION")
print("Maximum observations in one bin:", max_count)
print("Bins at maximum count:", int(histogram[max_count]))

print("\nZERO ELEVATION CHECK")
zero = elev == 0
print("Zero elevation bins:", int(np.count_nonzero(zero)))
print("With observations:", int(np.count_nonzero(zero & observed)))
print("Without observations:", int(np.count_nonzero(zero & unobserved)))

print("\nCENTER 5x5 ELEVATION SAMPLE")
print(sample_elev)

print("\nCENTER 5x5 OBSERVATION SAMPLE")
print(sample_counts)

print("\nGALE INVESTIGATION COMPLETE")
print("This is a rectangular regional sample, not an exact crater mask.")

