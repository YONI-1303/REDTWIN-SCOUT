from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/raw/earth/srtmgl1/atacama"

TILES = {
    "S23W068": ("s23_w068_1arc_v3.tif", -23, -68),
    "S23W069": ("s23_w069_1arc_v3.tif", -23, -69),
    "S24W068": ("s24_w068_1arc_v3.tif", -24, -68),
    "S24W069": ("s24_w069_1arc_v3.tif", -24, -69),
}

print("=" * 65)
print("REDTWIN — ATACAMA DATA VALIDATION")
print("=" * 65)

all_passed = True
sources = {}

for name, (filename, lat, lon) in TILES.items():

    path = FOLDER / filename

    print("\n" + "-" * 55)
    print("TILE:", name)

    if not path.exists():
        print("MISSING:", filename)
        all_passed = False
        continue

    with rasterio.open(path) as src:

        bounds = src.bounds

        metadata_ok = (
            src.width == 3601
            and src.height == 3601
            and src.count == 1
            and src.dtypes[0] == "int16"
            and src.crs is not None
            and src.crs.to_epsg() == 4326
        )

        geographic_ok = (
            abs(bounds.left - lon) < 0.001
            and abs(bounds.right - (lon + 1)) < 0.001
            and abs(bounds.bottom - lat) < 0.001
            and abs(bounds.top - (lat + 1)) < 0.001
        )

        masked_pixels = 0
        minimum = None
        maximum = None

        for row in range(0, src.height, 256):

            height = min(256, src.height - row)

            block = src.read(
                1,
                window=Window(0, row, src.width, height),
                masked=True
            )

            mask = np.ma.getmaskarray(block)
            masked_pixels += int(mask.sum())

            valid = block.data[~mask]

            if valid.size:
                low = int(valid.min())
                high = int(valid.max())

                minimum = low if minimum is None else min(minimum, low)
                maximum = high if maximum is None else max(maximum, high)

        total = src.width * src.height

        print("Dimensions:", src.width, "x", src.height)
        print("CRS:", src.crs)
        print("Resolution:", src.res)
        print("Bounds:", bounds)
        print("NoData:", src.nodata)
        print("Valid coverage (%):",
              round((total - masked_pixels) / total * 100, 2))
        print("Elevation range:", minimum, "to", maximum, "m")
        print("Metadata:", "PASS" if metadata_ok else "CHECK")
        print("Geographic position:",
              "PASS" if geographic_ok else "CHECK")

        all_passed &= metadata_ok and geographic_ok
        sources[name] = path

# Check San Pedro is actually inside the intended tile.
if "S23W069" in sources:

    with rasterio.open(sources["S23W069"]) as src:

        row, col = src.index(-68.21333, -22.93222)

        center_inside = (
            0 <= row < src.height
            and 0 <= col < src.width
        )

        print("\nSAN PEDRO LOCATION CHECK")
        print("Latitude: -22.93222")
        print("Longitude: -68.21333")
        print("Inside S23W069:", center_inside)

        all_passed &= center_inside

# Correct neighbor relationships in the Southern and Western hemispheres.
PAIRS = [
    ("S23W069", "right", "S23W068", "left"),
    ("S24W069", "right", "S24W068", "left"),
    ("S24W069", "top", "S23W069", "bottom"),
    ("S24W068", "top", "S23W068", "bottom"),
]

def read_edge(name, edge):

    with rasterio.open(sources[name]) as src:

        if edge == "left":
            window = Window(0, 0, 1, src.height)
        elif edge == "right":
            window = Window(src.width - 1, 0, 1, src.height)
        elif edge == "top":
            window = Window(0, 0, src.width, 1)
        else:
            window = Window(0, src.height - 1, src.width, 1)

        return src.read(1, window=window, masked=True)

print("\n" + "=" * 65)
print("ATACAMA SHARED-EDGE VALIDATION")
print("=" * 65)

for a, edge_a, b, edge_b in PAIRS:

    if a not in sources or b not in sources:
        print("SKIPPED:", a, b)
        all_passed = False
        continue

    first = read_edge(a, edge_a)
    second = read_edge(b, edge_b)

    valid = (
        ~np.ma.getmaskarray(first)
        & ~np.ma.getmaskarray(second)
    )

    av = first.data[valid].astype(np.int32)
    bv = second.data[valid].astype(np.int32)

    if av.size == 0:
        print("NO VALID EDGE SAMPLES:", a, b)
        all_passed = False
        continue

    differences = np.abs(av - bv)

    matches = int(np.count_nonzero(differences == 0))
    exact = matches == len(differences)

    print(f"\n{a} vs {b}")
    print("Compared:", len(differences))
    print("Exact matches:", matches)
    print("Maximum difference:", int(differences.max()), "m")
    print("Boundary:", "PASS" if exact else "CHECK")

    all_passed &= exact

print("\n" + "=" * 65)
print("FINAL RESULT:", "PASS" if all_passed else "CHECK")
print("=" * 65)

