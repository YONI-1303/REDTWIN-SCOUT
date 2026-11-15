from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[1]

path = (
    ROOT / "data" / "raw" / "earth" /
    "srtmgl1" / "afar" / "n14_e040_1arc_v3.tif"
)

nodata_32767 = 0
nodata_32768 = 0
valid_pixels = 0

minimum = None
maximum = None

with rasterio.open(path) as src:

    print("=" * 55)
    print("REDTWIN — SRTM QUALITY INVESTIGATION")
    print("=" * 55)

    print("Tile:", path.name)
    print("Declared NoData:", src.nodata)

    for row in range(0, src.height, 128):

        height = min(128, src.height - row)

        block = src.read(
            1,
            window=Window(0, row, src.width, height)
        )

        nodata_32767 += int(
            np.count_nonzero(block == -32767)
        )

        nodata_32768 += int(
            np.count_nonzero(block == -32768)
        )

        valid = block[block != src.nodata]

        if valid.size:
            valid_pixels += valid.size

            block_min = int(valid.min())
            block_max = int(valid.max())

            minimum = (
                block_min if minimum is None
                else min(minimum, block_min)
            )

            maximum = (
                block_max if maximum is None
                else max(maximum, block_max)
            )

    total = src.width * src.height

    print("\nFULL TILE SUMMARY")
    print("Total pixels:", total)
    print("Valid pixels:", valid_pixels)
    print("Declared NoData pixels:", nodata_32767)
    print("-32768 pixels:", nodata_32768)

    print("\nVALID ELEVATION RANGE")
    print("Minimum:", minimum, "m")
    print("Maximum:", maximum, "m")

    print("\nVALID DATA COVERAGE:")
    print(round(valid_pixels / total * 100, 2), "%")

    print("\nQUALITY INVESTIGATION COMPLETE")
