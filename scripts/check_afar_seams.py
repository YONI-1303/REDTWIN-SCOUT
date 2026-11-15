from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data/raw/earth/srtmgl1/afar"

FILES = {
    "N13E039": "n13_e039_1arc_v3.tif",
    "N13E040": "n13_e040_1arc_v3.tif",
    "N14E039": "n14_e039_1arc_v3.tif",
    "N14E040": "n14_e040_1arc_v3.tif",
}

def read_edge(tile, edge):
    path = FOLDER / FILES[tile]

    with rasterio.open(path) as src:
        if edge == "left":
            window = Window(0, 0, 1, src.height)
        elif edge == "right":
            window = Window(src.width - 1, 0, 1, src.height)
        elif edge == "top":
            window = Window(0, 0, src.width, 1)
        elif edge == "bottom":
            window = Window(0, src.height - 1, src.width, 1)

        return src.read(1, window=window, masked=True)

pairs = [
    ("N13E039", "right", "N13E040", "left"),
    ("N14E039", "right", "N14E040", "left"),
    ("N13E039", "top", "N14E039", "bottom"),
    ("N13E040", "top", "N14E040", "bottom"),
]

print("=" * 60)
print("REDTWIN — AFAR SEAM VALIDATION")
print("=" * 60)

for tile_a, edge_a, tile_b, edge_b in pairs:

    a = read_edge(tile_a, edge_a)
    b = read_edge(tile_b, edge_b)

    valid = (
        ~np.ma.getmaskarray(a) &
        ~np.ma.getmaskarray(b)
    )

    av = a.data[valid].astype(np.int32)
    bv = b.data[valid].astype(np.int32)

    if av.size == 0:
        print("\nNO VALID OVERLAP:", tile_a, tile_b)
        continue

    difference = np.abs(av - bv)

    print(f"\n{tile_a} ({edge_a}) vs {tile_b} ({edge_b})")
    print("Compared samples:", len(difference))
    print("Exact matches:", int(np.count_nonzero(difference == 0)))
    print("Different samples:", int(np.count_nonzero(difference != 0)))
    print("Maximum difference:", int(difference.max()), "metres")
    print("Mean absolute difference:", round(float(difference.mean()), 3), "metres")

print("\nSEAM INVESTIGATION COMPLETE")
