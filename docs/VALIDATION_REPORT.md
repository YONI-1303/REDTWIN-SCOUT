# Validation report: how much can the ranking be trusted?

All tables are in `outputs/validation/` and were produced by `scripts/run_validation.py`. The original ranking CSVs were not modified.
This is a sensitivity analysis. It cannot show that a place is a true Mars analogue, and none of these checks does.

## Short answer
The original ranking is reproducible, but its conclusion (Afar ahead of Atacama) is **not robust**, and **no Earth window is close to Gale**.

## What we checked

**1. MOLA labels and counts.** The topography label says each sample is the median observed elevation in a bin and that where no
observations lie in the bin "an interpolated value is supplied". The counts file is the number of observations per bin. A count of 0
therefore means interpolated. Our Gale window matches the raw files cell for cell, and 29.109% of cells have count ≥ 1 (median
count 2, maximum 8).

**2. Direct support by scale.**

| Neighbourhood | Fully observed | At least half observed |
|---|---|---|
| single cell | 29.1% | 29.1% |
| 3×3 | 1.4% | 20.9% |
| 11×11 | 0.0% | 6.0% |

Roughness (3×3), P95 slope and local relief (11×11) at Gale are mostly computed on interpolated cells. We did not compute direct-only
versions of these, because there is no meaningful way to without interpolating. They are reported as unsupported.

**3. Features that direct observations can support.** Elevation std and relief:

| | Full grid | Observed cells only | Difference |
|---|---|---|---|
| Elevation std (m) | 1371.5 | 1380.4 | +0.65% |
| Relief P95−P05 (m) | 4435 | 4476 | +0.92% |

Spatial block bootstrap of the observed-only estimates (95%): std 1246 to 1426 m, relief 4180 to 4573 m. Even the low end of Gale's relief
(4,180 m) is far above the highest Earth window (2,763 m), so "Earth windows are shallower than Gale" holds whatever the interpolation does.

**4. Spatial resolution.** Gale aggregated from observed cells only to 463 m, 926 m and 1.85 km (median 1, 2 and 5 observed cells per
block). On the two supported features the leading region is **Atacama at every scale**, by 1 to 4%, which is a tie.

**5. Feature redundancy.** P95 slope, 3×3 roughness and 11×11 local relief correlate at 0.98 to 1.00; elevation std and relief at 0.72.
Equal weighting gives the local-roughness signal about three times the influence of any other feature, and it is the part of Gale's
profile that is least directly observed.

**6. Standardisation.** The original scaler is fit on Gale plus the candidates. Variants:

| Scaler | Afar leads |
|---|---|
| Original (Gale + candidates) | 5 of 7 variants |
| Log-ratio to Gale | 5 of 7 |
| Fit on Earth candidates only | **0 of 7** |
| Median/MAD on Earth candidates | **0 of 7** |

Our explanation, **not yet tested**: Earth-only scaling divides by the small spread within Earth windows, which magnifies the relief gap, and
Atacama is the closest on relief alone.

**7. Feature sets.** Afar leads in 4 of 8 variants with all six features, 4 of 8 with four de-duplicated features, 2 of 4 with the three
window-scale features, and **0 of 8** with the two directly supported features. Dropping any one feature keeps Afar first, but dropping local
relief shrinks Afar's share of the top 10 from 10 to 6.

**8. Gale versus the Earth range.** Gale lies outside the Earth range for elevation std, relief, median slope and 11×11 local relief. It is
inside for P95 slope and 3×3 roughness.

**9. Overlap.** Windows overlap by 90%. Only one non-overlapping window fits in each 2° × 2° study area. The 36 candidates are two independent
samples, not 36.

## Overall: Afar vs Atacama
Afar leads in **10 of 28** variants. It leads under the original method and under a log-ratio comparison, and loses under Earth-only or
robust scaling and under direct-support-only features. On the numbers we have, we cannot say Afar is a better match than Atacama. We can say
that both fall well short of Gale's relief.

## Still uncertain
- Whether interpolation biases Gale's slope and roughness (expected to lower them; not measured).
- Whether MOLA bin medians and SRTM averages are comparable for roughness, since they smooth differently.
- Anything about additional regions, which would need new data and a larger independent sample.
- Any external validation against published analogue studies. None was attempted.
