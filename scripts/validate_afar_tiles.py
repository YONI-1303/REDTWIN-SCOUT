from pathlib import Path
import re
import numpy as np
import rasterio
from rasterio.windows import Window

ROOT = Path(__file__).resolve().parents[1]
FOLDER = ROOT / "data" / "raw" / "earth" / "srtmgl1" / "afar"

EXPECTED = {
    "N13E039": (13, 39),
    "N13E040": (13, 40),
    "N14E039": (14, 39),
    "N14E040": (14, 40),
}

print("=" * 65)
print("REDTWIN SCOUT — AFAR FOUR-TILE VALIDATION")
print("=" * 65)

if not FOLDER.exists():
    raise FileNotFoundError(FOLDER)

files = list(FOLDER.glob("*.tif"))

indexed = {}

for path in files:
    match = re.search(
        r"([NS])(\d{2})[_]?([EW])(\d{3})",
        path.name,
        re.IGNORECASE
    )

    if match:
        lat = int(match.group(2))
        lon = int(match.group(4))

        if match.group(1).upper() == "S":
            lat = -lat

        if match.group(3).upper() == "W":
            lon = -lon

        token = (
            f"{'N' if lat >= 0 else 'S'}{abs(lat):02d}"
            f"{'E' if lon >= 0 else 'W'}{abs(lon):03d}"
        )

        if token in EXPECTED:
            indexed[token] = path

print("\nEXPECTED FILES")

for token in EXPECTED:
    status = "FOUND" if token in indexed else "MISSING"
    print(token, ":", status)

results = []

for token, (lat, lon) in EXPECTED.items():

    if token not in indexed:
        continue

    path = indexed[token]

    print("\n" + "-" * 65)
    print("INSPECTING:", path.name)

    with rasterio.open(path) as src:

        print("Dimensions:", src.width, "x", src.height)
        print("Data type:", src.dtypes[0])
        print("CRS:", src.crs)
        print("EPSG:", src.crs.to_epsg() if src.crs else None)
        print("Bounds:", src.bounds)
        print("Resolution:", src.res)
        print("NoData:", src.nodata)
        print("Pixel interpretation:", src.tags().get("AREA_OR_POINT"))

        bounds = src.bounds

        # The one-pixel margin is expected for
        # pixel-center based SRTM GeoTIFF bounds.
        geographic_ok = (
            abs(bounds.left - lon) < 0.001 and
            abs(bounds.right - (lon + 1)) < 0.001 and
            abs(bounds.bottom - lat) < 0.001 and
            abs(bounds.top - (lat + 1)) < 0.001
        )

        metadata_ok = (
            src.width == 3601 and
            src.height == 3601 and
            src.count == 1 and
            src.dtypes[0] == "int16" and
            src.crs is not None and
            src.crs.to_epsg() == 4326
        )

        masked_pixels = 0
        fill_32767 = 0
        fill_32768 = 0
        minimum = None
        maximum = None

        # Read 256 rows at a time to conserve RAM.
        for row in range(0, src.height, 256):

            height = min(256, src.height - row)

            block = src.read(
                1,
                window=Window(0, row, src.width, height),
                masked=True
            )

            masked = np.ma.getmaskarray(block)
            masked_pixels += int(np.count_nonzero(masked))

            raw = np.asarray(block.data)

            fill_32767 += int(
                np.count_nonzero(raw == -32767)
            )

            fill_32768 += int(
                np.count_nonzero(raw == -32768)
            )

            valid = raw[~masked]

            if valid.size:
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
        valid_pixels = total - masked_pixels

        print("\nQUALITY RESULTS")
        print("Masked pixels:", masked_pixels)
        print("Pixels equal to -32767:", fill_32767)
        print("Pixels equal to -32768:", fill_32768)
        print("Valid pixels:", valid_pixels)
        print("Valid coverage (%):",
              round(valid_pixels / total * 100, 2))
        print("Minimum elevation:", minimum, "m")
        print("Maximum elevation:", maximum, "m")

        print("\nCHECKS")
        print("Dimensions:", "PASS" if metadata_ok else "CHECK")
        print("Geographic location:",
              "PASS" if geographic_ok else "CHECK")

        results.append({
            "tile": token,
            "metadata": metadata_ok,
            "geography": geographic_ok,
            "valid": valid_pixels > 0,
            "nodata": src.nodata
        })

print("\n" + "=" * 65)
print("FINAL VALIDATION SUMMARY")
print("=" * 65)

for result in results:
    print(
        result["tile"],
        "| Metadata:", result["metadata"],
        "| Geography:", result["geography"],
        "| Valid data:", result["valid"],
        "| NoData:", result["nodata"]
    )

complete = (
    len(indexed) == 4 and
    len(results) == 4 and
    all(
        r["metadata"] and r["geography"] and r["valid"]
        for r in results
    )
)

print("\nFOUR-TILE VALIDATION:", "PASS" if complete else "CHECK")

if not complete:
    print("Investigate any missing or failed tiles before mosaicking.")
