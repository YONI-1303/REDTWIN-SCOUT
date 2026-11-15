"""Sensitivity / validation study. Writes only to outputs/validation/.

Does not touch the original ranking CSVs.
Run:  python scripts/run_validation.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import redtwin_core as rc
from scipy.ndimage import uniform_filter

OUT = rc.ROOT / "outputs/validation"
OUT.mkdir(parents=True, exist_ok=True)

cand, ranks, gale_ref = rc.load_tables()
F = rc.FEATURES
X = cand[F].to_numpy(float)
G = gale_ref[F].to_numpy(float)
z, counts = rc.load_gale_arrays()
obs = counts > 0

# 1. Direct observation support ------------------------------------------------
sup = []
for name, k in [("single cell", 1), ("3x3 neighbourhood (roughness, slope)", 3), ("11x11 neighbourhood (local relief)", 11)]:
    f = uniform_filter(obs.astype(float), size=k, mode="nearest")
    sup.append({"scale": name, "share_fully_observed_pct": 100 * np.mean(f > 0.999),
                "share_at_least_half_observed_pct": 100 * np.mean(f >= 0.5),
                "share_with_any_observed_pct": 100 * np.mean(f > 0)})
sup = pd.DataFrame(sup)
sup.to_csv(OUT / "gale_direct_support_by_scale.csv", index=False)

direct = pd.DataFrame([
    {"quantity": "elevation_std_m", "full_window_incl_interpolated": z.std(), "direct_cells_only": z[obs].std()},
    {"quantity": "relief_p95_p05_m", "full_window_incl_interpolated": np.ptp(np.percentile(z, [5, 95])),
     "direct_cells_only": np.ptp(np.percentile(z[obs], [5, 95]))},
])
direct["difference_pct"] = 100 * (direct.direct_cells_only / direct.full_window_incl_interpolated - 1)
direct.to_csv(OUT / "gale_direct_vs_full_window_stats.csv", index=False)

# bootstrap: how stable is the direct-only estimate (spatial blocks of 20x20 px)
rng = np.random.default_rng(42)
bs, br = [], []
bl = 20
nb_r, nb_c = z.shape[0] // bl, z.shape[1] // bl
for _ in range(500):
    pick = rng.integers(0, nb_r * nb_c, nb_r * nb_c)
    vals = np.concatenate([z[(p // nb_c) * bl:(p // nb_c + 1) * bl, (p % nb_c) * bl:(p % nb_c + 1) * bl][
        obs[(p // nb_c) * bl:(p // nb_c + 1) * bl, (p % nb_c) * bl:(p % nb_c + 1) * bl]] for p in pick])
    bs.append(vals.std()); br.append(np.percentile(vals, 95) - np.percentile(vals, 5))
boot = {"elevation_std_ci95": np.percentile(bs, [2.5, 97.5]).round(1).tolist(),
        "relief_ci95": np.percentile(br, [2.5, 97.5]).round(1).tolist()}

# 2. Resolution sensitivity (window-scale features only) ---------------------------
def block(a, k, mask=None):
    h, w = (a.shape[0] // k) * k, (a.shape[1] // k) * k
    a = a[:h, :w].reshape(h // k, k, w // k, k)
    if mask is None:
        return a.mean((1, 3)), np.full((h // k, w // k), k * k)
    m = mask[:h, :w].reshape(h // k, k, w // k, k)
    n = m.sum((1, 3))
    s = np.where(m, a, 0).sum((1, 3))
    return np.where(n > 0, s / np.maximum(n, 1), np.nan), n

def win2(a):
    a = a[np.isfinite(a)]
    return np.array([a.std(), np.percentile(a, 95) - np.percentile(a, 5)])

earth_surf = {r: rc.region_surface(r) for r in rc.REGIONS}
res_rows = []
for k in (1, 2, 4):
    gm, gn = block(z, k, obs)                   # direct-only aggregation
    gref = win2(gm)
    support = gn[gn > 0]
    ed = []
    for _, r in cand.iterrows():
        w = rc.candidate_window(r.region, r.center_lat, r.center_lon)
        wb, _ = block(w, k)
        ed.append(win2(wb))
    ed = np.array(ed)
    for scaler in ("both", "earth"):
        pool = np.vstack([gref, ed]) if scaler == "both" else ed
        mu, sd = pool.mean(0), pool.std(0)
        d = np.linalg.norm((ed - mu) / sd - (gref - mu) / sd, axis=1)
        o = np.argsort(d)
        res_rows.append({"aggregation_factor": k, "cell_size_m": round(rc.DY * k), "scaler_fit": scaler,
                         "gale_blocks_with_direct_data": int((gn > 0).sum()), "gale_blocks_total": gn.size,
                         "median_direct_source_cells_per_block": float(np.median(support)),
                         "top_region": cand.region.values[o[0]], "best_candidate": cand.candidate_id.values[o[0]],
                         "afar_best": d[cand.region.values == "Afar"].min(),
                         "atacama_best": d[cand.region.values == "Atacama"].min()})
pd.DataFrame(res_rows).to_csv(OUT / "resolution_sensitivity.csv", index=False)

# 3. Method-variant grid ---------------------------------------------------------
subsets = {
    "all six features": F,
    "four, de-duplicated": ["elevation_std_m", "relief_p95_p05_m", "slope_median_deg", "slope_p95_deg"],
    "window-scale three": ["elevation_std_m", "relief_p95_p05_m", "slope_median_deg"],
    "directly-supported two": ["elevation_std_m", "relief_p95_p05_m"],
}
cluster = {"slope_p95_deg", "roughness_3x3_p95_m", "local_relief_11x11_p95_m"}
gdir = np.array([[z[obs].std(), np.ptp(np.percentile(z[obs], [5, 95]))]])

def run(cols, scaler, weighting, ref):
    idx = [F.index(c) for c in cols]
    A, B = X[:, idx], ref
    if scaler == "both (original)":
        pool = np.vstack([B, A]); mu, sd = pool.mean(0), pool.std(0)
    elif scaler == "earth only":
        mu, sd = A.mean(0), A.std(0)
    elif scaler == "robust median/MAD (earth)":
        mu = np.median(A, 0); sd = np.median(abs(A - mu), 0) * 1.4826
    elif scaler == "log ratio to Gale":
        a, b = np.log(A), np.log(B); mu, sd = 0, 1
    a, b = ((A - mu) / sd, (B - mu) / sd) if scaler != "log ratio to Gale" else (a, b)
    w = np.array([1 / 3 if (weighting == "cluster-weighted" and c in cluster) else 1.0 for c in cols])
    d = np.sqrt((((a - b) ** 2) * w).sum(1))
    o = np.argsort(d); reg = cand.region.values
    return {"top_region": reg[o[0]], "best_candidate": cand.candidate_id.values[o[0]],
            "afar_in_top10": int((reg[o[:10]] == "Afar").sum()),
            "afar_best": d[reg == "Afar"].min(), "atacama_best": d[reg == "Atacama"].min(),
            "afar_median": np.median(d[reg == "Afar"]), "atacama_median": np.median(d[reg == "Atacama"])}

rows = []
for sname, cols in subsets.items():
    for scaler in ("both (original)", "earth only", "robust median/MAD (earth)", "log ratio to Gale"):
        for wt in ("equal", "cluster-weighted"):
            if wt == "cluster-weighted" and not (set(cols) & cluster):
                continue
            for refname in ("full window (interpolated incl.)", "direct cells only"):
                if refname.startswith("direct"):
                    if sname != "directly-supported two":
                        continue
                    ref = gdir
                else:
                    ref = G[:, [F.index(c) for c in cols]]
                rows.append({"features": sname, "scaler": scaler, "weighting": wt, "gale_reference": refname,
                             **run(cols, scaler, wt, ref)})
grid = pd.DataFrame(rows)
grid["afar_leads"] = grid.top_region == "Afar"
grid.to_csv(OUT / "method_variant_results.csv", index=False)

# drop-one-feature
d1 = []
for f in F:
    cols = [c for c in F if c != f]
    d1.append({"dropped": f, **run(cols, "both (original)", "equal", G[:, [F.index(c) for c in cols]])})
pd.DataFrame(d1).to_csv(OUT / "drop_one_feature.csv", index=False)

# 4. Redundancy, range, overlap -----------------------------------------------------
cand[F].corr().round(3).to_csv(OUT / "feature_correlations.csv")
rng_tab = pd.DataFrame({"gale": G[0], "earth_min": X.min(0), "earth_max": X.max(0),
                        "gale_z_vs_earth": (G[0] - X.mean(0)) / X.std(0)}, index=F)
rng_tab["gale_outside_earth_range"] = (rng_tab.gale < rng_tab.earth_min) | (rng_tab.gale > rng_tab.earth_max)
rng_tab.round(3).to_csv(OUT / "gale_vs_earth_range.csv")

rc_ = [rc.candidate_rowcol(r.region, r.center_lat, r.center_lon) for r in cand.itertuples()]
cand2 = cand.assign(row=[a for a, _ in rc_], col=[b for _, b in rc_])
ov = []
for reg, g in cand2.groupby("region"):
    d = ranks.set_index("candidate_id").loc[g.candidate_id, "standardized_distance"]
    order = d.sort_values().index; chosen = []
    for cid in order:                                 # greedy non-overlapping set, best first
        r_, c_ = g.set_index("candidate_id").loc[cid, ["row", "col"]]
        if all(abs(r_ - r2) >= rc.ROWS or abs(c_ - c2) >= rc.COLS for r2, c2 in chosen):
            chosen.append((r_, c_))
    ov.append({"region": reg, "candidates": len(g), "max_non_overlapping_windows": len(chosen),
               "mean_overlap_with_nearest_neighbour_pct": 100 * (1 - 32 / rc.COLS)})
pd.DataFrame(ov).to_csv(OUT / "overlap_independence.csv", index=False)

# summary ------------------------------------------------------------------------------
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
print(sup.round(2).to_string(index=False)); print(direct.round(2).to_string(index=False)); print("bootstrap", boot)
print(pd.DataFrame(res_rows).round(3).to_string(index=False))
print("\nVARIANTS:", len(grid), "| Afar leads in", int(grid.afar_leads.sum()))
print(grid.groupby(["scaler"]).afar_leads.agg(["sum", "count"]))
print(grid.groupby(["features"]).afar_leads.agg(["sum", "count"]))
print(grid[grid.gale_reference.str.startswith("direct")][["scaler", "top_region", "afar_best", "atacama_best"]].round(3).to_string(index=False))
print(pd.DataFrame(d1)[["dropped", "top_region", "afar_in_top10"]].to_string(index=False))
print(rng_tab.round(2).to_string()); print(pd.DataFrame(ov).to_string(index=False))
(OUT / "bootstrap_direct_only.txt").write_text(str(boot))
