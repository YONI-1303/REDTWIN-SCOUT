from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[1]

MOSAIC = (
    ROOT / "data" / "processed" / "earth" /
    "afar" / "afar_srtm_2x2_mosaic.tif"
)

DALLol_LAT = 14.242
DALLol_LON = 40.300

print("=" * 60)
print("REDTWIN — FINAL AFAR MOSAIC VERIFICATION")
print("=" * 60)

with rasterio.open(MOSAIC) as src:

    print("\nMOSAIC INFORMATION")
    print("Dimensions:", src.width, "x", src.height)
    print("CRS:", src.crs)
    print("Resolution:", src.res)
    print("Bounds:", src.bounds)
    print("NoData:", src.nodata)

    # Locate Dallol in the mosaic.
    row, col = src.index(DALLol_LON, DALLol_LAT)

    print("\nDALLol LOCATION")
    print("Latitude:", DALLol_LAT)
    print("Longitude:", DALLol_LON)
    print("Raster row:", row)
    print("Raster column:", col)

    pixel_lon, pixel_lat = src.xy(row, col)

    print("Pixel center:", pixel_lat, pixel_lon)

    if not (0 <= row < src.height and 0 <= col < src.width):
        raise ValueError("Dallol is outside the mosaic.")

    # Read a small 5x5 window around Dallol.
    window = Window(col - 2, row - 2, 5, 5)

    sample = src.read(1, window=window, masked=True)

    print("\nDALLol 5x5 ELEVATION SAMPLE (METRES)")
    print(sample)

    valid_sample = sample.compressed()

    if valid_sample.size:
        print("Local minimum:", int(valid_sample.min()))
        print("Local maximum:", int(valid_sample.max()))

    # Scan the complete mosaic in small blocks.
    valid_pixels = 0
    masked_pixels = 0
    elevation_min = None
    elevation_max = None

    for start in range(0, src.height, 128):

        height = min(128, src.height - start)

        block = src.read(
            1,
            window=Window(0, start, src.width, height),
            masked=True
        )

        mask = np.ma.getmaskarray(block)
        valid = block.data[~mask]

        masked_pixels += int(mask.sum())
        valid_pixels += valid.size

        if valid.size:
            block_min = int(valid.min())
            block_max = int(valid.max())

            elevation_min = (
                block_min if elevation_min is None
                else min(elevation_min, block_min)
            )

            elevation_max = (
                block_max if elevation_max is None
                else max(elevation_max, block_max)
            )

    total = src.width * src.height

    print("\nFULL MOSAIC QUALITY")
    print("Total pixels:", total)
    print("Valid pixels:", valid_pixels)
    print("Masked pixels:", masked_pixels)
    print("Valid coverage (%):",
          round(valid_pixels / total * 100, 2))
    print("Minimum elevation:", elevation_min, "m")
    print("Maximum elevation:", elevation_max, "m")

print("\nAFAR MOSAIC VERIFICATION COMPLETE")
