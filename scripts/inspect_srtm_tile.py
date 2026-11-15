from pathlib import Path
import rasterio
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[1]

path = (
    ROOT / "data" / "raw" / "earth" /
    "srtmgl1" / "afar" / "n14_e040_1arc_v3.tif"
)

print("=" * 55)
print("REDTWIN SCOUT — SRTM TILE VALIDATION")
print("=" * 55)

if not path.exists():
    raise FileNotFoundError(path)

print("File:", path.name)
print("File size:", path.stat().st_size, "bytes")

with rasterio.open(path) as src:

    print("\nRASTER METADATA")
    print("Driver:", src.driver)
    print("Width:", src.width)
    print("Height:", src.height)
    print("Bands:", src.count)
    print("Data type:", src.dtypes)
    print("CRS:", src.crs)
    print("EPSG:", src.crs.to_epsg() if src.crs else None)
    print("Bounds:", src.bounds)
    print("Resolution:", src.res)
    print("Transform:", src.transform)
    print("NoData:", src.nodata)
    print("Compression:", src.compression)

    print("\nTIFF METADATA TAGS")
    print(src.tags())

    print("\n5x5 CENTER SAMPLE")
    window = Window(
        src.width // 2 - 2,
        src.height // 2 - 2,
        5,
        5
    )

    sample = src.read(1, window=window, masked=True)
    print(sample)

    valid = sample.compressed()

    if valid.size:
        print("Sample minimum:", int(valid.min()))
        print("Sample maximum:", int(valid.max()))
    else:
        print("Sample contains no valid elevation pixels.")

    print("Masked sample pixels:", int(sample.mask.sum()))

    print("\nBASIC VALIDATION")
    print("Dimensions:", "PASS" if
          (src.width, src.height) == (3601, 3601) else "CHECK")

    print("Data type:", "PASS" if
          src.dtypes[0] == "int16" else "CHECK")

    print("NoData:", "PASS" if
          src.nodata == -32768 else "CHECK")

    print("CRS:", "PASS" if
          src.crs and src.crs.to_epsg() == 4326 else "CHECK")

print("\nINSPECTION COMPLETE")
