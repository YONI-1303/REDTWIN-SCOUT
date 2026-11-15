from pathlib import Path

import numpy as np
import rasterio
import plotly.graph_objects as go

from rasterio.windows import Window
from pyproj import Transformer

ROOT = Path(__file__).resolve().parents[1]

MOSAIC = (
    ROOT / "data" / "processed" / "earth" /
    "afar" / "afar_srtm_2x2_mosaic.tif"
)

OUTPUT = (
    ROOT / "data" / "processed" / "earth" /
    "afar" / "visualizations" /
    "dallol_terrain_preview.html"
)

# Dallol sampling center
LAT = 14.242
LON = 40.300

# Approximately 15 km across
RADIUS = 250

print("=" * 55)
print("REDTWIN SCOUT — DALLol TERRAIN VISUALIZATION")
print("=" * 55)

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

with rasterio.open(MOSAIC) as src:

    if src.crs is None:
        raise ValueError("Mosaic has no CRS.")

    # Find the Dallol pixel.
    row, col = src.index(LON, LAT)

    r0 = max(0, row - RADIUS)
    r1 = min(src.height, row + RADIUS + 1)

    c0 = max(0, col - RADIUS)
    c1 = min(src.width, col + RADIUS + 1)

    window = Window(
        c0,
        r0,
        c1 - c0,
        r1 - r0
    )

    terrain = src.read(
        1,
        window=window,
        masked=True
    )

    elevation = terrain.astype(np.float32).filled(np.nan)

    valid = np.isfinite(elevation)

    if not valid.any():
        raise ValueError("No valid elevation pixels in window.")

    # Project to UTM Zone 37N for metric map axes.
    transformer = Transformer.from_crs(
        src.crs,
        "EPSG:32637",
        always_xy=True
    )

    center_x, center_y = transformer.transform(LON, LAT)

    # Calculate each pixel center in projected coordinates.
    columns = np.arange(c0, c1)
    rows = np.arange(r0, r1)

    x_lon = np.array([
        src.xy(row, c, offset="center")[0]
        for c in columns
    ])

    y_lat = np.array([
        src.xy(r, col, offset="center")[1]
        for r in rows
    ])

    x_utm, _ = transformer.transform(
        x_lon,
        np.full(x_lon.shape, LAT)
    )

    _, y_utm = transformer.transform(
        np.full(y_lat.shape, LON),
        y_lat
    )

    x_km = (np.asarray(x_utm) - center_x) / 1000
    y_km = (np.asarray(y_utm) - center_y) / 1000

    minimum = float(np.nanmin(elevation))
    maximum = float(np.nanmax(elevation))

    coverage = valid.sum() / elevation.size * 100

    print("\nREGIONAL WINDOW")
    print("Shape:", elevation.shape)
    print("Valid coverage:", round(float(coverage), 2), "%")
    print("Minimum elevation:", minimum, "m")
    print("Maximum elevation:", maximum, "m")

    fig = go.Figure()

    fig.add_trace(
        go.Heatmap(
            z=elevation,
            x=x_km,
            y=y_km,
            colorscale="Earth",
            colorbar=dict(
                title="Elevation (m)"
            ),
            hovertemplate=(
                "East: %{x:.2f} km<br>"
                "North: %{y:.2f} km<br>"
                "Elevation: %{z:.0f} m"
                "<extra></extra>"
            )
        )
    )

    fig.add_trace(
        go.Scatter(
            x=[0],
            y=[0],
            mode="markers+text",
            marker=dict(
                size=12,
                color="red",
                symbol="cross"
            ),
            text=["Dallol sampling center"],
            textposition="top right",
            name="Dallol"
        )
    )

    fig.update_layout(
        title="REDTWIN SCOUT — Dallol Terrain Explorer",
        xaxis_title="East / West distance from Dallol (km)",
        yaxis_title="North / South distance from Dallol (km)",
        width=1000,
        height=800,
        template="plotly_dark"
    )

    fig.update_yaxes(
        scaleanchor="x",
        scaleratio=1
    )

    fig.write_html(
        OUTPUT,
        include_plotlyjs="cdn"
    )

print("\nVISUALIZATION CREATED")
print(OUTPUT)
