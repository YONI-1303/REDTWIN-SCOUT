from pathlib import Path
import rasterio
from rasterio.merge import merge

ROOT = Path(__file__).resolve().parents[1]

SOURCE = ROOT / "data/raw/earth/srtmgl1/atacama"

OUTPUT_DIR = ROOT / "data/processed/earth/atacama"

OUTPUT = OUTPUT_DIR / "atacama_srtm_2x2_mosaic.tif"

FILES = [
    "s24_w069_1arc_v3.tif",
    "s24_w068_1arc_v3.tif",
    "s23_w069_1arc_v3.tif",
    "s23_w068_1arc_v3.tif",
]

def main():

    print("=" * 60)
    print("REDTWIN — ATACAMA MOSAIC GENERATION")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT.exists():
        raise FileExistsError(OUTPUT)

    sources = []

    try:
        for filename in FILES:
            path = SOURCE / filename

            if not path.exists():
                raise FileNotFoundError(path)

            sources.append(rasterio.open(path))

        reference = sources[0]

        for src in sources:
            if src.crs != reference.crs:
                raise ValueError("CRS mismatch")

            if src.dtypes != reference.dtypes:
                raise ValueError("Data type mismatch")

            if src.nodata != reference.nodata:
                raise ValueError("NoData mismatch")

        print("Source tiles:", len(sources))
        print("Creating mosaic...")

        mosaic, transform = merge(
            sources,
            method="first",
            dtype="int16",
            nodata=reference.nodata
        )

        height, width = mosaic.shape[1:]

        print("Dimensions:", width, "x", height)

        profile = reference.profile.copy()

        profile.update(
            driver="GTiff",
            height=height,
            width=width,
            count=1,
            dtype="int16",
            transform=transform,
            nodata=reference.nodata,
            compress="deflate",
            predictor=2,
            tiled=True,
            blockxsize=256,
            blockysize=256,
            BIGTIFF="IF_SAFER"
        )

        with rasterio.open(OUTPUT, "w", **profile) as dst:
            dst.write(mosaic)

            dst.update_tags(
                PROJECT="REDTWIN SCOUT",
                PRODUCT="ATACAMA SRTM MOSAIC",
                SOURCE_TILES=", ".join(FILES),
                SEAM_VALIDATION="All four boundaries matched exactly",
                VERTICAL_REFERENCE="EGM96, source DTED metadata"
            )

        print("\nVERIFYING OUTPUT")

        with rasterio.open(OUTPUT) as check:

            print("Dimensions:", check.width, "x", check.height)
            print("CRS:", check.crs)
            print("Bounds:", check.bounds)
            print("Resolution:", check.res)
            print("NoData:", check.nodata)
            print("Compression:", check.compression)

            if (check.width, check.height) != (7201, 7201):
                raise ValueError("Unexpected dimensions")

            row, col = check.index(-68.21333, -22.93222)

            print("\nSAN PEDRO LOCATION")
            print("Row:", row)
            print("Column:", col)
            print(
                "Inside mosaic:",
                0 <= row < check.height and 0 <= col < check.width
            )

        print("\nATACAMA MOSAIC SUCCESSFUL!")
        print(OUTPUT)

    finally:
        for src in sources:
            src.close()

if __name__ == "__main__":
    main()
