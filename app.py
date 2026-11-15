"""REDTWIN SCOUT - Earth-Mars terrain analogue explorer.

Run with:  streamlit run app.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import redtwin_core as rc  # noqa: E402

ROOT = rc.ROOT
VAL = ROOT / "outputs/validation"
DOCS = ROOT / "docs"

st.set_page_config(page_title="REDTWIN SCOUT", layout="wide", initial_sidebar_state="expanded")

from redtwin_visual_theme import apply_redtwin_visual_theme
apply_redtwin_visual_theme()


from shape_waves_background import inject_shape_waves_background
inject_shape_waves_background()

ACCENT, TEAL, MUTED = "#d9694a", "#4fb3b0", "#8b98a5"

st.markdown(f"""
<style>
#MainMenu, footer {{visibility:hidden;}}
.block-container {{padding-top:1.4rem; max-width:1500px;}}
h1,h2,h3 {{letter-spacing:-0.01em; font-weight:600;}}
.brand {{font-size:.72rem; letter-spacing:.22em; color:{ACCENT}; text-transform:uppercase; margin-bottom:.1rem;}}
.title {{font-size:2.3rem; font-weight:700; line-height:1.1; margin:0 0 .25rem 0;}}
.sub {{color:{MUTED}; font-size:1.02rem; margin-bottom:1rem;}}
.gale-warn {{border-left:3px solid #e0a030; background:#1d1a12; padding:.55rem .9rem; margin:0 0 1.1rem 0;
  font-size:.86rem; color:#e8d9b5; border-radius:0 4px 4px 0;}}
.kv {{border-top:1px solid #243040; padding-top:.5rem; margin-bottom:.4rem;}}
.kv .k {{font-size:.68rem; letter-spacing:.12em; text-transform:uppercase; color:{MUTED};}}
.kv .v {{font-size:1.65rem; font-weight:600; line-height:1.2;}}
.kv .n {{font-size:.78rem; color:{MUTED};}}
.tag {{display:inline-block; font-size:.66rem; letter-spacing:.1em; text-transform:uppercase; padding:1px 7px;
  border:1px solid #2c3a4a; border-radius:3px; color:{MUTED}; margin-right:.3rem;}}
.tag.m {{color:{TEAL}; border-color:{TEAL};}} .tag.i {{color:#e0a030; border-color:#e0a030;}}
section[data-testid="stSidebar"] {{border-right:1px solid #1c2631;}}
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------- data -------
@st.cache_data(show_spinner=False)
def get_tables():
    return rc.load_tables()


@st.cache_data(show_spinner=False)
def get_gale():
    return rc.load_gale_arrays()


@st.cache_data(show_spinner="Reading terrain window...")
def get_candidate_window(region, lat, lon):
    return rc.candidate_window(region, lat, lon)


@st.cache_data(show_spinner=False)
def get_footprint(region, lat, lon):
    return rc.window_footprint(region, lat, lon)


@st.cache_data(show_spinner=False)
def get_site_windows():
    import rasterio
    out = {}
    for key, fn in [("Dallol window (Afar)", "dallol_afar_463m.tif"),
                    ("San Pedro window (Atacama)", "sanpedro_atacama_463m.tif")]:
        p = rc.SCALE_DIR / fn
        if p.exists():
            with rasterio.open(p) as s:
                out[key] = s.read(1).astype(np.float64)
    return out


def kv(label, value, note=""):
    st.markdown(f'<div class="kv"><div class="k">{label}</div><div class="v">{value}</div>'
                f'<div class="n">{note}</div></div>', unsafe_allow_html=True)


try:
    cand, ranked, gale_ref = get_tables()
except rc.DataMissing as e:
    st.error(f"{e}\n\nThe ranking tables are produced by `scripts/search_terrain_candidates.py`.")
    st.stop()
except Exception as e:  # noqa: BLE001
    st.error(f"Could not load the project tables: {e}")
    st.stop()

ranked = ranked.copy()
GALE_COV = float(ranked["gale_direct_observation_coverage_pct"].iloc[0])
DMIN, DMAX = ranked.standardized_distance.min(), ranked.standardized_distance.max()
ranked["region_rank"] = ranked.groupby("region")["standardized_distance"].rank(method="first").astype(int)
BY_ID = ranked.set_index("candidate_id")

if "sel" not in st.session_state or st.session_state.sel not in BY_ID.index:
    st.session_state.sel = ranked.candidate_id.iloc[0]

# ---------------------------------------------------------------- sidebar ------
PAGES = ["Mission overview", "Candidate explorer", "Terrain lab", "Methodology",
         "Data and provenance", "Results and exports"]
st.sidebar.markdown('<div class="brand">REDTWIN SCOUT</div>', unsafe_allow_html=True)
page = st.sidebar.radio("Section", PAGES, label_visibility="collapsed")
st.sidebar.markdown("---")
st.sidebar.caption(
    "Scope: two 2° × 2° SRTM study areas (Afar, Atacama) compared with one Mars site (Gale). "
    "This is not a search of all of Earth. No lunar comparison has been done.")

st.markdown('<div class="brand">NASA Space Apps · Earth–Mars terrain analogues</div>'
            '<div class="title">REDTWIN SCOUT</div>'
            '<div class="sub">Which places on Earth have terrain measurements that resemble Gale Crater?</div>',
            unsafe_allow_html=True)
st.markdown(
    f'<div class="gale-warn"><b>Read this first.</b> Only {GALE_COV:.2f}% of the Gale window’s cells contain a direct '
    f'MOLA measurement; the rest of the elevation grid is interpolated by the data producer. All rankings are '
    f'exploratory, and the distance is a standardised distance, not a probability or a percent similarity.</div>',
    unsafe_allow_html=True)


# ------------------------------------------------------------- helpers ---------
def val_csv(name):
    p = VAL / name
    return pd.read_csv(p) if p.exists() else None


def plain_language(b: pd.DataFrame) -> list[str]:
    r = b.set_index("feature")
    out = []
    x = r.loc["relief_p95_p05_m"]
    out.append(f"**Relief.** Most of this window spans {x.candidate:,.0f} m from low to high "
               f"(5th to 95th percentile). Gale spans {x.gale:,.0f} m, so the candidate is "
               f"{abs(x.difference):,.0f} m {'shallower' if x.difference < 0 else 'deeper'}.")
    x = r.loc["elevation_std_m"]
    out.append(f"**Elevation spread.** Standard deviation of {x.candidate:,.0f} m against {x.gale:,.0f} m at Gale. "
               f"This tracks relief: a big crater floor-to-rim drop widens it.")
    x = r.loc["slope_median_deg"]
    out.append(f"**Typical slope.** Half the cells are gentler than {x.candidate:.1f}° (Gale: {x.gale:.1f}°). "
               f"Slopes here are averaged over ~460 m cells, so they are far gentler than what a rover feels.")
    x = r.loc["slope_p95_deg"]
    out.append(f"**Steep slopes.** The steepest 5% of cells exceed {x.candidate:.1f}° (Gale: {x.gale:.1f}°).")
    x = r.loc["roughness_3x3_p95_m"]
    out.append(f"**Roughness.** In the roughest 5% of 3×3 patches (about 1.4 km across), elevation varies by "
               f"about {x.candidate:.0f} m (Gale: {x.gale:.0f} m).")
    x = r.loc["local_relief_11x11_p95_m"]
    out.append(f"**Local relief.** Across 11×11 patches (about 5 km), the top 5% show {x.candidate:,.0f} m of "
               f"highest-to-lowest difference (Gale: {x.gale:,.0f} m).")
    out.append("*The three roughness-type measures for Gale are computed mostly on interpolated cells "
               "(see Methodology › Validation), so treat the Gale side of those lines as soft.*")
    return out


def hist_trace(values, name, color, lo, hi, dash=None, nbins=60):
    v = np.asarray(values).ravel()
    v = v[np.isfinite(v)]
    h, e = np.histogram(v, bins=nbins, range=(lo, hi), density=True)
    return go.Scatter(x=(e[:-1] + e[1:]) / 2, y=h, mode="lines", name=name,
                      line=dict(color=color, width=2.2, dash=dash, shape="spline"),
                      hovertemplate="%{x:.1f}: %{y:.4f}<extra>" + name + "</extra>")


PALETTE = ["#d9694a", "#4fb3b0", "#e0b44c", "#9a86d6", "#7fb069", "#e07a9f"]


def build_series(names, gale_z):
    sites = get_site_windows()
    s = {}
    for i, n in enumerate(names):
        col = PALETTE[i % len(PALETTE)]
        if n.startswith("Gale"):
            s[n] = dict(z=gale_z, color="#f2f2f2")
        elif n in sites:
            s[n] = dict(z=sites[n], color=col)
        else:
            row = BY_ID.loc[n]
            s[n] = dict(z=get_candidate_window(row.region, row.center_lat, row.center_lon), color=col)
    return s


def distribution_figure(series, key, title, xlabel, gale_n=None):
    arrays = {n: rc.window_arrays(d["z"]) for n, d in series.items()}
    extra = {}
    if key == "elevation":
        data = {n: a["elevation"] - np.median(a["elevation"]) for n, a in arrays.items()}
        gname = next((n for n in series if n.startswith("Gale")), None)
        if gname is not None and gale_n is not None:
            gz = series[gname]["z"]
            extra["Gale: directly observed cells only"] = gz[gale_n > 0] - np.median(gz)
    else:
        data = {n: a[key] for n, a in arrays.items()}
    allv = np.concatenate([np.ravel(v) for v in data.values()])
    lo, hi = np.percentile(allv, 0.5), np.percentile(allv, 99.5)
    fig = go.Figure()
    for n, v in data.items():
        fig.add_trace(hist_trace(v, n, series[n]["color"], lo, hi))
    for n, v in extra.items():
        fig.add_trace(hist_trace(v, n, "#f2f2f2", lo, hi, dash="dot"))
    fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                      height=360, margin=dict(l=10, r=10, t=40, b=40), title=dict(text=title, font=dict(size=14)),
                      xaxis_title=xlabel, yaxis_title="density", legend=dict(orientation="h", y=-0.28))
    return fig


def _map_fig(arr, title, **kw):
    f = go.Figure(go.Heatmap(z=arr, **kw))
    f.update_yaxes(autorange="reversed", scaleanchor="x", showticklabels=False)
    f.update_xaxes(showticklabels=False)
    f.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=330,
                    margin=dict(l=5, r=5, t=40, b=5), title=dict(text=title, font=dict(size=13)))
    return f


def terrain_tabs(series, gale_n, map_for=None):
    tabs = st.tabs(["Elevation distribution", "Slope", "Roughness (3×3)", "Local relief (11×11)",
                    "Maps" if map_for else "Feature table"])
    with tabs[0]:
        st.plotly_chart(distribution_figure(series, "elevation", "Elevation relative to each window’s median",
                                            "elevation − window median (m)", gale_n), width="stretch")
        st.caption("Absolute elevations differ by kilometres between sites, so each window is centred on its own "
                   "median. The dotted line is Gale using only cells with a direct MOLA observation; the "
                   "solid Gale line includes interpolated cells.")
    with tabs[1]:
        st.plotly_chart(distribution_figure(series, "slope", "Slope per cell (~463 m cells)", "slope (°)"),
                        width="stretch")
    with tabs[2]:
        st.plotly_chart(distribution_figure(series, "roughness", "3×3 local standard deviation of elevation",
                                            "roughness (m)"), width="stretch")
    with tabs[3]:
        st.plotly_chart(distribution_figure(series, "local_relief", "Max − min elevation in 11×11 neighbourhoods",
                                            "local relief (m)"), width="stretch")
    if any(n.startswith("Gale") for n in series):
        st.caption("Gale slope, roughness and local relief come from the full MOLA grid, which is mostly "
                   "interpolated at these scales. Interpolation tends to smooth, so Gale’s true values may be higher.")
    with tabs[4]:
        if map_for:
            win = series[map_for]["z"]
            gz = series[next(n for n in series if n.startswith("Gale"))]["z"]
            lim = float(max(np.ptp(np.percentile(win, [2, 98])), np.ptp(np.percentile(gz, [2, 98])))) / 2
            c1, c2, c3 = st.columns(3)
            kw = dict(colorscale="Cividis", zmin=-lim, zmax=lim, colorbar=dict(title="m", thickness=10))
            c1.plotly_chart(_map_fig(win - np.median(win), map_for, **kw), width="stretch")
            c2.plotly_chart(_map_fig(gz - np.median(gz), "Gale Crater (MOLA)", **kw), width="stretch")
            c3.plotly_chart(_map_fig((gale_n > 0).astype(int), f"Gale: direct observations ({GALE_COV:.1f}%)",
                                     colorscale=[[0, "#222c38"], [1, TEAL]], showscale=False), width="stretch")
            st.caption("Both elevation maps share one colour range, centred on each window’s median. "
                       "Teal cells (right) are directly observed; everything else in Gale’s map is interpolated.")
        else:
            rows = []
            for n in series:
                a = rc.extract_features(series[n]["z"])
                rows.append({"window": n, **{rc.FEATURE_LABELS[k]: round(v, 2) for k, v in a.items()}})
            st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")


# ============================================================ PAGE: overview ==
if page == "Mission overview":
    c1, c2 = st.columns([3, 2], gap="large")
    grid = val_csv("method_variant_results.csv")
    n_var = len(grid) if grid is not None else None
    n_afar = int(grid.afar_leads.sum()) if grid is not None else None
    atac = ranked[ranked.region == "Atacama"]
    with c1:
        st.markdown("""
Rovers, drills and navigation software get tested on Earth long before they fly, and the choice of test site
matters. REDTWIN SCOUT asks a narrow, measurable version of that question: **which Earth terrain windows have
elevation statistics closest to a chosen Mars reference?**

The reference is a ~147 × 152 km window around **Gale Crater** (MOLA, Mars Global Surveyor). The Earth side is two
hand-picked SRTM study areas, **Afar** in the Horn of Africa and the **Atacama** in northern Chile. Each is cut into
Gale-sized windows on the same ~463 m grid. Six terrain measurements are taken from every window and the
windows are ranked by how far their profile sits from Gale’s.

It can tell you which of these windows is *least different* from Gale in relief, slope and roughness, and why.
It cannot tell you that any place is a good analogue, geologically similar, safe or habitable.
""")
        st.markdown("#### Where things stand")
        n_top = int((ranked.head(20).region == "Afar").sum())
        lead = (f"Across {n_var} reasonable method variants Afar leads in only {n_afar}; " if grid is not None else "")
        st.markdown(f"""
- In the original ranking Afar holds {n_top} of the top 20 places and **{ranked.candidate_id.iloc[0]} is closest to Gale**
  (distance {DMIN:.2f}). The closest Atacama window is rank {int(atac['rank'].min())} ({atac.standardized_distance.min():.2f}).
- That lead is **fragile.** {lead}it flips to Atacama when the scaler is fit on Earth data
  alone, with robust scaling, or when only the measurements Gale’s direct observations can support are used.
- **No window is close.** Gale’s relief (4,435 m) is far outside anything in the Earth set (maximum 2,763 m).
- The 36 windows overlap by 90% and only one non-overlapping window fits per area, so this is closer to
  two data points than thirty-six.
""")
    with c2:
        kv("Candidate windows", "36", "20 Afar · 16 Atacama (study areas only)")
        kv("Gale direct MOLA coverage", f"{GALE_COV:.1f}%", "of window cells have a direct observation")
        kv("Smallest distance", f"{DMIN:.2f}", f"{ranked.candidate_id.iloc[0]} · standardised units, not a %")
        if grid is not None:
            kv("Method variants where Afar leads", f"{n_afar} of {n_var}", "see Methodology › Validation")
        st.markdown('<span class="tag m">measured</span><span class="tag i">interpolated</span>'
                    '<span class="tag">assumed</span>', unsafe_allow_html=True)
        st.caption("Tags used across the app. Gale elevations are a mix of measured and interpolated; "
                   "Earth values are SRTM measurements averaged to ~463 m.")
    st.info("Open **Candidate explorer** in the sidebar to pick a region, click a candidate on the map and "
            "compare it with Gale.")

# ========================================================== PAGE: explorer ====
elif page == "Candidate explorer":
    import folium
    from branca.colormap import LinearColormap
    from streamlit_folium import st_folium

    top = st.columns([1.1, 1.4, 1.6, 2])
    region = top[0].radio("Region", ["Afar", "Atacama"], horizontal=True)
    basemap = top[1].selectbox("Basemap", ["Satellite (Esri)", "Terrain (OpenTopoMap)", "Dark (CARTO)",
                                           "None (offline)"])
    reg_df = ranked[ranked.region == region].sort_values("rank")
    ids = list(reg_df.candidate_id)
    # Apply a queued map click / carried-over selection BEFORE the widget exists.
    if st.session_state.get("pending") in ids:
        st.session_state["cand_select"] = st.session_state.pop("pending")
    elif st.session_state.get("cand_select") not in ids:
        st.session_state["cand_select"] = st.session_state.sel if st.session_state.sel in ids else ids[0]
    labels = {i: f"{i} · overall #{BY_ID.loc[i, 'rank']} · d = {BY_ID.loc[i, 'standardized_distance']:.2f}" for i in ids}
    choice = top[2].selectbox("Candidate", ids, key="cand_select", format_func=lambda i: labels[i])
    st.session_state.sel = choice
    top[3].caption("Click a marker to select it. Colour is the standardised distance to Gale "
                   "(same scale in both regions). A blank basemap usually means no internet: pick “None”.")

    tiles = {"Satellite (Esri)": ("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
                                  "Esri, Maxar, Earthstar Geographics"),
             "Terrain (OpenTopoMap)": ("https://tile.opentopomap.org/{z}/{x}/{y}.png", "OpenTopoMap (CC-BY-SA)"),
             "Dark (CARTO)": ("https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}.png", "CARTO, OpenStreetMap contributors"),
             "None (offline)": (None, None)}[basemap]
    m = folium.Map(location=[reg_df.center_lat.mean(), reg_df.center_lon.mean()], zoom_start=8,
                   tiles=tiles[0], attr=tiles[1], control_scale=True)
    if tiles[0] is None:
        m.get_root().html.add_child(folium.Element("<style>.leaflet-container{background:#0b0f14}</style>"))

    try:
        import rasterio
        with rasterio.open(rc.need(rc.REGIONS[region]["mosaic"])) as src:
            bb = src.bounds
        bounds = [[bb.bottom, bb.left], [bb.top, bb.right]]
    except Exception:  # noqa: BLE001
        bounds = [[reg_df.center_lat.min() - 0.8, reg_df.center_lon.min() - 0.8],
                  [reg_df.center_lat.max() + 0.8, reg_df.center_lon.max() + 0.8]]
    folium.Rectangle(bounds, color="#8b98a5", weight=1.5, dash_array="6 6", fill=False,
                     tooltip=f"{region} study mosaic (SRTM 2°×2°): the only area searched").add_to(m)
    m.fit_bounds(bounds)

    cmap = LinearColormap(["#f6d55c", "#ed7d3a", "#a23b72", "#3b1b5a"], vmin=DMIN, vmax=DMAX,
                          caption="Standardised distance to Gale (lower = less different)")
    cmap.add_to(m)
    sel_row = BY_ID.loc[choice]
    try:
        folium.Polygon(get_footprint(region, sel_row.center_lat, sel_row.center_lon), color="#ffffff", weight=2,
                       dash_array="4 4", fill=True, fill_opacity=0.06,
                       tooltip=f"Footprint of {choice} (329×320 cells, ≈152×148 km)").add_to(m)
    except Exception:  # noqa: BLE001
        pass
    for r in reg_df.itertuples():
        pop = (f"<b>{r.candidate_id}</b><br>overall rank {r.rank} (region rank {r.region_rank})<br>"
               f"{r.center_lat:.5f}°, {r.center_lon:.5f}°<br>distance {r.standardized_distance:.3f}")
        folium.CircleMarker([r.center_lat, r.center_lon], radius=7, color="#0b0f14", weight=1, fill=True,
                            fill_color=cmap(r.standardized_distance), fill_opacity=0.95,
                            tooltip=f"{r.candidate_id} | rank {r.rank} | d {r.standardized_distance:.2f}",
                            popup=folium.Popup(pop, max_width=240)).add_to(m)
    folium.CircleMarker([sel_row.center_lat, sel_row.center_lon], radius=13, color="#ffffff", weight=3,
                        fill=False, tooltip=f"SELECTED: {choice}").add_to(m)
    lname, llat, llon = rc.REGIONS[region]["landmark"]
    folium.Marker([llat, llon], tooltip=f"{lname}: reference landmark, not a candidate",
                  popup=f"{lname} ({llat:.4f}°, {llon:.4f}°). Landmark used for earlier previews. "
                        "It is not a candidate result.",
                  icon=folium.DivIcon(html=f'<div style="font:600 11px sans-serif;color:{TEAL};white-space:nowrap;'
                                           f'text-shadow:0 0 3px #000">◆ {lname}</div>')).add_to(m)

    mc, pc = st.columns([3, 2], gap="large")
    with mc:
        try:
            out = st_folium(m, height=600, use_container_width=True, key=f"map_{region}_{basemap}",
                            returned_objects=["last_object_clicked_tooltip"])
            clicked = (out or {}).get("last_object_clicked_tooltip")
            if clicked:
                cid = str(clicked).split("|")[0].replace("SELECTED:", "").strip()
                if cid in set(ids) and cid != st.session_state.sel:
                    st.session_state["pending"] = cid
                    st.rerun()
        except Exception as e:  # noqa: BLE001
            st.warning(f"The map could not be drawn ({e}). The ranking table below still works.")
        st.caption(f"◆ {lname} is a reference landmark, not a candidate. Dashed grey box = SRTM study mosaic. "
                   "Dashed white box = footprint of the selected window.")

    b = rc.breakdown(sel_row, gale_ref, cand)
    with pc:
        st.markdown(f"### {choice}")
        st.caption(f"{region} · {sel_row.center_lat:.5f}°, {sel_row.center_lon:.5f}°")
        a1, a2, a3 = st.columns(3)
        a1.metric("Overall rank", f"{sel_row['rank']} of 36")
        a2.metric(f"Rank in {region}", f"{sel_row.region_rank} of {len(reg_df)}")
        a3.metric("Distance", f"{sel_row.standardized_distance:.2f}")
        st.caption(f"Earth data coverage in window: {sel_row.candidate_valid_coverage_pct:.0f}% · "
                   f"Gale direct coverage: {GALE_COV:.1f}%")
        show = b[["label", "candidate", "gale", "difference", "share_of_distance_pct"]].rename(columns={
            "label": "Feature", "candidate": "Candidate", "gale": "Gale", "difference": "Diff.",
            "share_of_distance_pct": "% of distance"})
        st.dataframe(show.style.format({"Candidate": "{:,.1f}", "Gale": "{:,.1f}", "Diff.": "{:+,.1f}",
                                        "% of distance": "{:.1f}"}), hide_index=True, width="stretch")
        t2 = b.sort_values("share_of_distance_pct", ascending=False).head(2)
        st.markdown(f"**Why this rank:** {t2.iloc[0].label} accounts for {t2.iloc[0].share_of_distance_pct:.0f}% "
                    f"of this window’s distance and {t2.iloc[1].label} for {t2.iloc[1].share_of_distance_pct:.0f}%. "
                    "Lower distance only means a smaller gap on these six numbers.")
        with st.expander("What the measurements mean"):
            for line in plain_language(b):
                st.markdown(line)

    st.markdown("### Compare with Gale")
    gz, gn = get_gale()
    try:
        series = build_series(["Gale Crater (Mars)", choice], gz)
        series[choice]["color"] = ACCENT
        terrain_tabs(series, gn, map_for=choice)
    except rc.DataMissing as e:
        st.error(str(e))
    except Exception as e:  # noqa: BLE001
        st.error(f"Could not build the terrain comparison: {e}")

    st.markdown("### Ranking")
    allr = st.checkbox("Show all 36 candidates", value=False)
    tbl = (ranked if allr else reg_df)[["rank", "candidate_id", "region", "center_lat", "center_lon",
                                        "standardized_distance", "main_feature_differences"]]
    st.dataframe(tbl, hide_index=True, width="stretch", column_config={
        "rank": "Overall rank", "candidate_id": "Candidate", "region": "Region",
        "center_lat": st.column_config.NumberColumn("Lat", format="%.5f"),
        "center_lon": st.column_config.NumberColumn("Lon", format="%.5f"),
        "standardized_distance": st.column_config.NumberColumn("Distance", format="%.3f"),
        "main_feature_differences": "Largest contributors"})

# ============================================================ PAGE: lab =======
elif page == "Terrain lab":
    st.markdown("### Terrain lab")
    st.caption("Overlay any combination of Gale, the two landmark windows and individual candidates. "
               "Every curve comes from the project’s raster windows; nothing is simulated.")
    gz, gn = get_gale()
    sites = get_site_windows()
    options = ["Gale Crater (Mars)"] + list(sites) + list(ranked.candidate_id)
    default = (["Gale Crater (Mars)"] + list(sites) + [ranked.candidate_id.iloc[0],
               ranked[ranked.region == "Atacama"].candidate_id.iloc[0]])[:6]
    pick = st.multiselect("Windows to compare", options, default=default, max_selections=6)
    if not pick:
        st.info("Select at least one window.")
    else:
        try:
            terrain_tabs(build_series(pick, gz), gn)
        except rc.DataMissing as e:
            st.error(str(e))
        except Exception as e:  # noqa: BLE001
            st.error(f"Could not build the comparison: {e}")
    if len(sites) < 2:
        st.warning("One or both landmark windows (common_scale/*_463m.tif) were not found.")

# ====================================================== PAGE: methodology =====
elif page == "Methodology":
    t1, t2, t3 = st.tabs(["Pipeline", "Validation", "Limitations"])
    with t1:
        st.markdown("""
**1 · Data.** Mars: MOLA MEGDR 128 pixel/degree topography (median elevation per bin) and the matching
counts file, which says how many laser shots fell in each bin. Earth: SRTM 1 arc-second tiles (NASA/USGS),
mosaicked into one 2° × 2° block for Afar and one for Atacama.

**2 · Common scale.** One MOLA bin is ~463 m. Earth mosaics are reprojected to UTM and *averaged* onto a
463 m grid whose east-west spacing is corrected to Gale’s latitude (460.97 m), so every window has the same
physical size: 329 × 320 cells, about 152 × 147 km.

**3 · Windows.** Earth windows slide across each mosaic with a 32-cell stride; only windows with
100% valid data are kept (20 Afar, 16 Atacama). Neighbouring windows overlap by 90%.

**4 · Features.** Per window: elevation standard deviation, relief (P95 − P05 of elevation), median and P95
slope, P95 of 3×3 roughness, and P95 of 11×11 local relief. Absolute elevation is deliberately excluded.

**5 · Ranking.** Features are standardised (mean 0, std 1) with a scaler fit on Gale plus all 36 candidates,
then candidates are ordered by Euclidean distance to Gale. Lower means a smaller gap. It is not a probability.

**6 · Observation coverage.** The counts file shows which Gale cells have at least one direct shot. The topography
label states that empty bins hold an interpolated value, so the rest of the Gale grid is not measured.
""")
    with t2:
        st.markdown("Produced by `scripts/run_validation.py` into `outputs/validation/`. "
                    "These are sensitivity checks. They do not validate that any place is a true analogue.")
        grid = val_csv("method_variant_results.csv")
        if grid is None:
            st.info("Run `python scripts/run_validation.py` to generate the validation tables.")
        else:
            st.markdown("#### Does Afar stay ahead?")
            ren = {"sum": "Afar leads", "count": "variants"}
            c1, c2 = st.columns(2)
            c1.markdown("By standardisation method")
            c1.dataframe(grid.groupby("scaler").afar_leads.agg(["sum", "count"]).rename(columns=ren), width="stretch")
            c2.markdown("By feature set")
            c2.dataframe(grid.groupby("features").afar_leads.agg(["sum", "count"]).rename(columns=ren), width="stretch")
            st.markdown(f"**Afar leads in {int(grid.afar_leads.sum())} of {len(grid)} variants.** "
                        "It holds with the original scaler or a log-ratio, and never when the scaler is fit on Earth data only. "
                        "With only the two features Gale’s direct observations support (elevation std, relief), "
                        "Atacama leads every time, by a margin that is essentially a tie.")
            with st.expander("All variants"):
                st.dataframe(grid.round(3), hide_index=True, width="stretch")
        sup = val_csv("gale_direct_support_by_scale.csv")
        dd = val_csv("gale_direct_vs_full_window_stats.csv")
        if sup is not None:
            st.markdown("#### How much of Gale is directly observed, by scale")
            st.dataframe(sup.round(2), hide_index=True, width="stretch")
            st.caption("Single cells: 29%. A 3×3 patch is fully observed only 1.4% of the time and an 11×11 patch "
                       "never. So roughness, P95 slope and local relief at Gale are mostly properties of the "
                       "interpolated surface.")
        if dd is not None:
            st.markdown("#### Window-scale statistics: direct cells vs full grid")
            st.dataframe(dd.round(2), hide_index=True, width="stretch")
            boot = VAL / "bootstrap_direct_only.txt"
            st.caption("The window-scale numbers move by under 1% when interpolated cells are removed. A spatial "
                       "block bootstrap (500 resamples, 20×20-cell blocks) of the direct-only estimate gives: "
                       + (boot.read_text() if boot.exists() else "n/a"))
        rs = val_csv("resolution_sensitivity.csv")
        if rs is not None:
            st.markdown("#### Resolution: 463 m, 926 m and 1.85 km cells")
            st.dataframe(rs.round(3), hide_index=True, width="stretch")
            st.caption("Gale is aggregated from directly observed cells only; “median direct source cells per block” "
                       "is how many real observations support each aggregated cell. Atacama is nominally closer at "
                       "every scale, but the gap is only 1–4%, so this is a tie, not a result.")
        rg = val_csv("gale_vs_earth_range.csv")
        if rg is not None:
            st.markdown("#### Is Gale inside the range of the Earth candidates?")
            st.dataframe(rg.rename(columns={"Unnamed: 0": "feature"}), hide_index=True, width="stretch")
            st.caption("Four of six features sit outside everything in the Earth set. The z-values are inflated "
                       "because the 36 windows are near-duplicates; read them as ‘far outside’.")
        cc = val_csv("feature_correlations.csv")
        if cc is not None:
            cc = cc.set_index(cc.columns[0])
            fig = go.Figure(go.Heatmap(z=cc.values, x=[rc.FEATURE_LABELS[c] for c in cc.columns],
                                       y=[rc.FEATURE_LABELS[c] for c in cc.index], zmin=-1, zmax=1,
                                       colorscale="RdBu", text=cc.round(2).values, texttemplate="%{text}"))
            fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", height=420,
                              margin=dict(l=10, r=10, t=40, b=10),
                              title=dict(text="Feature correlation across the 36 candidates", font=dict(size=14)))
            fig.update_yaxes(autorange="reversed")
            st.plotly_chart(fig, width="stretch")
            st.caption("P95 slope, 3×3 roughness and 11×11 local relief are the same signal (r ≥ 0.98). "
                       "Equal weighting counts it three times.")
        ov = val_csv("overlap_independence.csv")
        if ov is not None:
            st.markdown("#### Independence of the 36 windows")
            st.dataframe(ov.round(1), hide_index=True, width="stretch")
            st.caption("Only one non-overlapping window fits in each 2° block, so there are two independent samples.")
    with t3:
        lim = DOCS / "SCIENTIFIC_LIMITATIONS.md"
        st.markdown(lim.read_text(encoding="utf-8") if lim.exists()
                    else "Limitations file not found (docs/SCIENTIFIC_LIMITATIONS.md).")

# ========================================================= PAGE: provenance ===
elif page == "Data and provenance":
    st.markdown("### Data and provenance")
    files = [
        ("Mars topography", "data/raw/mars/mola_meg128/megt00n090hb.img", "NASA PDS, MGS MOLA MEGDR (MGS-M-MOLA-5-MEGDR-L3-V1.0), 128 px/°",
         "Median of observed shots per bin; empty bins interpolated (per PDS label)", "measured + interpolated"),
        ("Mars observation counts", "data/raw/mars/mola_meg128/megc00n090hb.img", "NASA PDS, same product family",
         "Number of shots per bin; 0 = no direct observation", "measured"),
        ("Earth elevation, Afar", "data/processed/earth/afar/afar_srtm_2x2_mosaic.tif", "NASA/USGS SRTM 1 arc-second, 4 tiles (raw in data/raw/earth/srtmgl1/afar)",
         "2°×2° mosaic; no void values found", "measured"),
        ("Earth elevation, Atacama", "data/processed/earth/atacama/atacama_srtm_2x2_mosaic.tif", "NASA/USGS SRTM 1 arc-second, 4 tiles (raw in data/raw/earth/srtmgl1/atacama)",
         "2°×2° mosaic; no void values found", "measured"),
        ("Gale window", "data/processed/common_scale/gale_mola_window.tif", "Cut from MOLA by build_terrain_features.py",
         "329×320 cells; identical to the raw cells (checked)", "measured + interpolated"),
        ("Gale counts window", "data/processed/common_scale/gale_mola_counts.tif", "Cut from MOLA counts", "Same window", "measured"),
        ("Dallol window", "data/processed/common_scale/dallol_afar_463m.tif", "SRTM averaged to ~463 m", "Landmark window, not a candidate", "measured (averaged)"),
        ("San Pedro window", "data/processed/common_scale/sanpedro_atacama_463m.tif", "SRTM averaged to ~463 m", "Landmark window, not a candidate", "measured (averaged)"),
        ("Candidate features", "data/processed/ai_candidates/earth_candidate_features.csv", "search_terrain_candidates.py", "36 windows, six features (not modified)", "derived"),
        ("Original ranking", "data/processed/ai_candidates/provisional_similarity_rankings.csv", "search_terrain_candidates.py", "Not modified", "derived"),
        ("Window cache (Afar)", "data/processed/derived/afar_common_scale.npy", "Created by this app", "Same reprojection as the search; reproduces stored features to 1e-15", "derived"),
        ("Window cache (Atacama)", "data/processed/derived/atacama_common_scale.npy", "Created by this app", "Same as above", "derived"),
        ("Validation tables", "outputs/validation/method_variant_results.csv", "scripts/run_validation.py", "Sensitivity analysis", "derived"),
    ]
    rows = []
    for n, p, src, note, kind in files:
        f = ROOT / p
        rows.append({"Dataset": n, "File": p, "Source": src, "Notes": note, "Type": kind,
                     "Present": "yes" if f.exists() else "missing",
                     "Size (MB)": round(f.stat().st_size / 1e6, 2) if f.exists() else None})
    st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.markdown("Basemaps (Esri, OpenTopoMap, CARTO) are third-party tiles loaded in your browser for orientation. "
                "They are not analysed and play no part in the numbers.")

# ========================================================== PAGE: exports =====
elif page == "Results and exports":
    st.markdown("### Results and exports")
    st.caption("Everything here is a real project file or is generated from one.")
    all_ids = list(ranked.candidate_id)
    sel = st.selectbox("Candidate for the report", all_ids, index=all_ids.index(st.session_state.sel))
    row = BY_ID.loc[sel]
    b = rc.breakdown(row, gale_ref, cand)
    grid = val_csv("method_variant_results.csv")
    rep = [f"# REDTWIN SCOUT: candidate report, {sel}", "",
           f"- Region: {row.region}", f"- Window centre: {row.center_lat:.5f}, {row.center_lon:.5f}",
           f"- Overall rank: {row['rank']} of 36 (rank {row.region_rank} within {row.region})",
           f"- Standardised distance to Gale: {row.standardized_distance:.3f} (not a probability or percent)",
           f"- Earth data coverage in window: {row.candidate_valid_coverage_pct:.0f}%",
           f"- Gale direct MOLA coverage: {GALE_COV:.2f}%", "",
           "## Features vs Gale", "", "| Feature | Candidate | Gale | Difference | Share of distance |", "|---|---|---|---|---|"]
    for r in b.itertuples():
        rep.append(f"| {r.label} | {r.candidate:,.2f} | {r.gale:,.2f} | {r.difference:+,.2f} | {r.share_of_distance_pct:.1f}% |")
    rep += ["", "## What the numbers say", ""] + [f"- {l}" for l in plain_language(b)]
    if grid is not None:
        rep += ["", "## Robustness of the regional ordering", "",
                f"Afar leads in {int(grid.afar_leads.sum())} of {len(grid)} method variants tested "
                "(outputs/validation/method_variant_results.csv)."]
    rep += ["", "## Limitations", "",
            "- Only 29% of Gale window cells are direct MOLA observations; the rest are interpolated.",
            "- Terrain similarity does not show habitability, landing safety or geological similarity.",
            "- Windows overlap by 90%; each 2° study area holds one non-overlapping window.",
            "- Only the included Afar and Atacama mosaics were searched. No lunar analysis was performed."]
    report_md = "\n".join(rep)

    methods = ""
    for f in ["METHODS.md", "SCIENTIFIC_LIMITATIONS.md"]:
        p = DOCS / f
        if p.exists():
            methods += p.read_text(encoding="utf-8") + "\n\n---\n\n"
    methods = methods or "Methodology files not found in docs/."

    c1, c2 = st.columns(2)
    try:
        with c1:
            st.download_button("Candidate rankings (CSV, original)", rc.need(rc.CAND_DIR / "provisional_similarity_rankings.csv").read_bytes(),
                               "provisional_similarity_rankings.csv", "text/csv", width="stretch")
            st.download_button("Candidate features (CSV, original)", rc.need(rc.CAND_DIR / "earth_candidate_features.csv").read_bytes(),
                               "earth_candidate_features.csv", "text/csv", width="stretch")
            st.download_button("Gale reference features (CSV)", rc.need(rc.CAND_DIR / "gale_reference_features.csv").read_bytes(),
                               "gale_reference_features.csv", "text/csv", width="stretch")
    except rc.DataMissing as e:
        c1.error(str(e))
    with c2:
        st.download_button(f"Report for {sel} (Markdown)", report_md.encode("utf-8"), f"report_{sel}.md",
                           "text/markdown", width="stretch")
        st.download_button("Methodology and limitations (Markdown)", methods.encode("utf-8"),
                           "redtwin_methods_and_limitations.md", "text/markdown", width="stretch")
        if grid is not None:
            st.download_button("Validation: method variants (CSV)", grid.to_csv(index=False).encode(),
                               "method_variant_results.csv", "text/csv", width="stretch")
    with st.expander("Preview report"):
        st.markdown(report_md)
