# Methods

## Data
- **Mars:** MOLA MEGDR 128 pixel/degree products, `megt00n090hb` (median topography per bin) and `megc00n090hb`
  (shot count per bin). Simple cylindrical projection, 463.06 m per bin at the equator. Tile covers 0° to 44°S, 90°E to 180°E.
- **Earth:** SRTM 1 arc-second tiles, mosaicked to a 2° × 2° block for Afar (13–15°N, 39–41°E) and for Atacama (22–24°S, 67–69°W).

## Common scale
Gale's window is 329 rows × 320 columns of MOLA bins around 5.44°S, 137.70°E. East-west ground spacing at that
latitude is 463.06 × cos(5.44°) = 460.97 m; north-south is 463.06 m. The window is about 152 km × 148 km.
Earth mosaics are reprojected to UTM (EPSG:32637 Afar, EPSG:32719 Atacama) and *averaged* (not sampled) onto a grid with
those same spacings, so every window has identical physical size and cell count.

## Candidate windows
Windows slide over each reprojected mosaic with a 32-cell stride; only windows with 100% valid cells are kept.
This gives 20 windows in Afar and 16 in Atacama. Adjacent windows overlap by 90%.

## Six features (per window)
1. Elevation standard deviation.
2. Relief: 95th minus 5th percentile of elevation.
3. Median slope (from gradients using the metric cell spacing).
4. 95th percentile slope.
5. 95th percentile of 3×3 roughness (local standard deviation of elevation).
6. 95th percentile of 11×11 local relief (max minus min).

Absolute elevation is intentionally excluded: Mars and Earth use different vertical datums and absolute height is
not a terrain-character measure.

## Ranking
Features are standardised with a `StandardScaler` fit on Gale plus all 36 candidates. Candidates are ordered by
Euclidean distance to Gale in standardised units. The "share of distance" for a feature is its squared standardised
difference divided by the sum over all six.

## Observation coverage
The counts raster tells us which Gale cells have at least one direct shot (29.11%). The PDS label says empty bins carry
an interpolated value. The original ranking used the full grid including interpolated cells; the validation study
also uses direct-only variants where a quantity can be computed from direct cells alone.

## Validation (new)
`scripts/run_validation.py` writes to `outputs/validation/`:
- direct-observation support by neighbourhood size;
- elevation std and relief from directly observed cells only, with a spatial block bootstrap (500 resamples, 20×20-cell blocks);
- aggregation to 463 m, 926 m and 1.85 km using only observed Gale cells (the number of observed cells behind each block is reported);
- 28 variants: four scalers (original, Earth-only, median/MAD, log-ratio to Gale) × four feature sets × equal vs cluster-weighted features, plus direct-only Gale references;
- drop-one-feature runs, feature correlations, Gale-vs-Earth range, and a window-independence count.

Results and interpretation: `docs/VALIDATION_REPORT.md`.

## Not computed
Slope, roughness and local relief from directly observed Gale cells only. A 3×3 neighbourhood is fully observed 1.4% of
the time and an 11×11 neighbourhood never, so these cannot be computed without interpolation. We report them as unsupported
instead of substituting a number.
