"""Run:  python -m pytest tests -q     (or: python tests/test_redtwin.py)"""
import hashlib
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import redtwin_core as rc  # noqa: E402

# SHA-256 of the ORIGINAL research CSVs as delivered in REDTWIN_SCOUT.zip
ORIGINAL_HASHES = {
    "earth_candidate_features.csv": "fb777d0400e43c8e93be4fccc8a9a9927d5f262a3c0ccbbfe77837bff4dd66b2",
    "gale_reference_features.csv": "f870c430af67bd182f33ad01c561293b0980f62eba4034005682abfc7597f11a",
    "provisional_similarity_rankings.csv": "50d47e71d24e9d108c062c53aefc5c45931d919e89ac8629142cd86ba93e8d76",}


def test_original_csvs_unchanged():
    for name, h in ORIGINAL_HASHES.items():
        assert hashlib.sha256((rc.CAND_DIR / name).read_bytes()).hexdigest() == h, name


def test_candidate_counts_and_consistency():
    cand, ranked, gale = rc.load_tables()
    assert len(ranked) == 36 and ranked.candidate_id.is_unique
    assert (ranked.region == "Afar").sum() == 20 and (ranked.region == "Atacama").sum() == 16
    assert set(cand.candidate_id) == set(ranked.candidate_id)
    assert ranked["rank"].tolist() == list(range(1, 37))
    assert ranked.standardized_distance.is_monotonic_increasing
    assert np.isclose(ranked.gale_direct_observation_coverage_pct.iloc[0], 29.109, atol=0.001)
    assert ranked.iloc[0].candidate_id == "Afar_0002" and np.isclose(ranked.iloc[0].standardized_distance, 8.437698, atol=1e-5)
    best_at = ranked[ranked.region == "Atacama"].iloc[0]
    assert np.isclose(best_at.standardized_distance, 9.212852, atol=1e-5)


def test_coordinates_inside_study_mosaics():
    _, ranked, _ = rc.load_tables()
    box = {"Afar": (13, 15, 39, 41), "Atacama": (-24, -22, -69, -67)}
    for r in ranked.itertuples():
        a, b, c, d = box[r.region]
        assert a <= r.center_lat <= b and c <= r.center_lon <= d, r.candidate_id


def test_rankings_reproduce_from_features():
    from sklearn.preprocessing import StandardScaler
    cand, ranked, gale = rc.load_tables()
    X, G = cand[rc.FEATURES].to_numpy(float), gale[rc.FEATURES].to_numpy(float)
    s = StandardScaler().fit(np.vstack([G, X]))
    d = np.linalg.norm(s.transform(X) - s.transform(G), axis=1)
    got = pd.Series(d, index=cand.candidate_id)[ranked.candidate_id].to_numpy()
    assert np.allclose(got, ranked.standardized_distance, atol=1e-9)


def test_raster_dimensions_and_gale_window():
    import rasterio
    for fn in ["gale_mola_window.tif", "gale_mola_counts.tif", "dallol_afar_463m.tif", "sanpedro_atacama_463m.tif"]:
        with rasterio.open(rc.SCALE_DIR / fn) as s:
            assert s.shape == (rc.ROWS, rc.COLS), fn
    z, n = rc.load_gale_arrays()
    assert np.isclose((n > 0).mean() * 100, 29.109, atol=0.001)


def test_regenerated_windows_match_saved_features():
    cand, _, _ = rc.load_tables()
    for r in cand.itertuples():
        w = rc.candidate_window(r.region, r.center_lat, r.center_lon)
        assert w.shape == (rc.ROWS, rc.COLS) and np.isfinite(w).all()
        f = rc.extract_features(w)
        for k in rc.FEATURES:
            assert np.isclose(f[k], getattr(r, k), rtol=1e-9), (r.candidate_id, k)


def test_breakdown_shares_sum_to_100():
    cand, ranked, gale = rc.load_tables()
    b = rc.breakdown(ranked.iloc[0], gale, cand)
    assert np.isclose(b.share_of_distance_pct.sum(), 100)
    assert b.sort_values("share_of_distance_pct").iloc[-1].feature == "relief_p95_p05_m"


def test_missing_file_message():
    try:
        rc.need(ROOT / "nope.csv")
    except rc.DataMissing as e:
        assert "nope.csv" in str(e)
    else:
        raise AssertionError("DataMissing not raised")


PAGES = ["Mission overview", "Candidate explorer", "Terrain lab", "Methodology", "Data and provenance", "Results and exports"]


def _app():
    from streamlit.testing.v1 import AppTest
    return AppTest.from_file(str(ROOT / "app.py"), default_timeout=120)


def test_every_page_renders_without_exception():
    at = _app().run()
    assert not at.exception, at.exception
    for p in PAGES:
        at.sidebar.radio[0].set_value(p).run()
        assert not at.exception, (p, at.exception)
        assert any("29.11%" in m.value for m in at.markdown), "Gale coverage warning missing on " + p


def test_region_switching_and_candidate_selection():
    at = _app().run()
    at.sidebar.radio[0].set_value("Candidate explorer").run()
    assert not at.exception
    for region in ["Atacama", "Afar", "Atacama"]:
        reg = [r for r in at.radio if r.label == "Region"][0]
        reg.set_value(region).run()
        assert not at.exception, (region, at.exception)
        sel = [s for s in at.selectbox if s.label == "Candidate"][0]
        assert len(sel.options) == (20 if region == "Afar" else 16)
        for opt in [o.split(" · ")[0] for o in sel.options[:3]]:
            sel.set_value(opt).run()
            assert not at.exception, (region, opt, at.exception)
            sel = [s for s in at.selectbox if s.label == "Candidate"][0]
            assert sel.value == opt


def test_all_basemaps():
    at = _app().run()
    at.sidebar.radio[0].set_value("Candidate explorer").run()
    for bm in [s for s in at.selectbox if s.label == "Basemap"][0].options:
        [s for s in at.selectbox if s.label == "Basemap"][0].set_value(bm).run()
        assert not at.exception, (bm, at.exception)


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
