# Scientific limitations

**Gale is mostly interpolated.** 29.11% of the window's cells hold a direct MOLA measurement (median 2 shots per observed bin).
Cells without data are filled by the data producer. At 3×3 scale only 1.4% of neighbourhoods are fully observed; at 11×11, none.
Gale's roughness, P95 slope and local relief are therefore mostly properties of an interpolated, probably smoothed surface.
Elevation spread and relief barely change when only observed cells are used (under 1%).

**No Earth window is close to Gale.** Gale's relief is 4,435 m; the Earth maximum is 2,763 m. Four of six features lie outside the range
of every Earth window. The ranking says which window is least different, not that it is similar.

**The regional ordering is not robust.** Afar leads in 10 of 28 method variants. Atacama leads whenever the scaler is fit on Earth
data only, with median/MAD scaling, or when only the two directly supported features are used.

**The six features are not independent.** P95 slope, 3×3 roughness and 11×11 local relief correlate at 0.98 to 1.00. Equal
weighting counts that signal three times.

**The 36 windows are not 36 samples.** Windows overlap by 90%, and each 2° study area holds one non-overlapping window. The dataset
amounts to two independent Earth samples.

**Study area is small and hand-picked.** Two 2° × 2° SRTM blocks. The tool does not search Earth, and no lunar site has been analysed.

**Resolution mismatch.** SRTM (30 m) is averaged to ~463 m; MOLA bins are medians of sparse shots. Slope and roughness at this
scale describe landscape-scale structure and are not rover-scale hazards.

**Terrain statistics are not site suitability.** Similarity in these six numbers says nothing about geology, mineralogy, habitability,
traction, hazards, dust, climate or landing safety.

**Untested.** Whether interpolation biases Gale's slope and roughness low (expected, not measured); whether the Earth-only scaler
flips the result because it magnifies the relief gap (likely, not tested); any independent validation against known analogue studies.
