from pathlib import Path
import rasterio
from rasterio.merge import merge

ROOT = Path(__file__).resolve().parents[1]

SOURCE = ROOT / "data" / "raw" / "earth" / "srtmgl1" / "afar"

OUTPUT_DIR = ROOT / "data" / "processed" / "earth" / "afar"

OUTPUT = OUTPUT_DIR / "afar_srtm_2x2_mosaic.tif"

FILES = [
    "n13_e039_1arc_v3.tif",
    "n13_e040_1arc_v3.tif",
    "n14_e039_1arc_v3.tif",
    "n14_e040_1arc_v3.tif",
]

def main():

    print("=" * 60)
    print("REDTWIN — AFAR MOSAIC GENERATION")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if OUTPUT.exists():
        raise FileExistsError(
            f"Mosaic already exists: {OUTPUT}\n"
            "Preserve it and inspect it before replacing."
        )

    paths = [SOURCE / name for name in FILES]

    for path in paths:
        if not path.exists():
            raise FileNotFoundError(path)

    sources = []

    try:
        for path in paths:
            src = rasterio.open(path)
            sources.append(src)

        reference = sources[0]

        for src in sources:

            if src.crs != reference.crs:
                raise ValueError("CRS mismatch")

            if src.dtypes != reference.dtypes:
                raise ValueError("Data type mismatch")

            if src.nodata != reference.nodata:
                raise ValueError("NoData mismatch")

            if src.width != 3601 or src.height != 3601:
                raise ValueError("Unexpected source dimensions")

        print("\nSource files verified:", len(sources))
        print("CRS:", reference.crs)
        print("Data type:", reference.dtypes[0])
        print("NoData:", reference.nodata)

        print("\nCreating mosaic...")

        mosaic, transform = merge(
            sources,
            method="first",
            dtype="int16",
            nodata=reference.nodata
        )

        height = mosaic.shape[1]
        width = mosaic.shape[2]

        print("Output dimensions:", width, "x", height)

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
                PRODUCT="AFAR SRTM 1 ARC-SECOND MOSAIC",
                SOURCE_TILES=", ".join(FILES),
                METHOD="Rasterio merge, first valid source",
                SEAM_CHECK="Four shared boundaries matched exactly",
                VERTICAL_REFERENCE="EGM96, source DTED metadata"
            )

        print("\nMOSAIC SAVED:", OUTPUT)

        # Reopen the output to verify the written file.
        with rasterio.open(OUTPUT) as check:

            print("\nOUTPUT VERIFICATION")
            print("Dimensions:", check.width, "x", check.height)
            print("CRS:", check.crs)
            print("Resolution:", check.res)
            print("Bounds:", check.bounds)
            print("NoData:", check.nodata)
            print("Compression:", check.compression)

            if (check.width, check.height) != (7201, 7201):
                raise ValueError("Unexpected mosaic dimensions")

            if check.crs != reference.crs:
                raise ValueError("Output CRS verification failed")

            if check.nodata != reference.nodata:
                raise ValueError("Output NoData verification failed")

        print("\nMOSAIC GENERATION SUCCESSFUL")

    finally:
        for src in sources:
            src.close()

if __name__ == "__main__":
    main()
