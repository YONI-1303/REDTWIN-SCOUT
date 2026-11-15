# Five-minute demo script

Start: `streamlit run app.py`, browser open at the first page, window full-screen. Pre-select **Satellite (Esri)** basemap and test the
internet once beforehand. If the Wi-Fi is bad, switch to **None (offline)**; the demo still works.

**0:00 – 0:35 · Mission overview** (page opens here)
- "Rovers get tested on Earth. We ask which Earth terrain is least different from Gale Crater on six measurements."
- Point at the amber bar: "Only 29% of Gale's cells are real MOLA measurements. We show this on every page."
- Point at the four numbers: 36 windows, 29.1%, 8.44, "Afar leads in 10 of 28".
- Read the bullet "No window is close": relief 4,435 m vs Earth max 2,763 m.

**0:35 – 2:00 · Candidate explorer**
- Click **Candidate explorer**. Region **Afar** is selected. "Dashed grey box is the only area we searched."
- Point at the colour bar: "Colour is distance to Gale. Lower is less different. It is not a percentage."
- Point at the diamond: "Dallol is a landmark, not a result."
- **Click the lightest marker.** The white ring and dashed box move; the right panel shows Afar_0002: rank 1 of 36, distance 8.44.
- Read "Why this rank": relief 51%, elevation std 29%.
- Open **What the measurements mean** and read the Relief line.
- Switch **Region** to **Atacama**. "Same colour scale. Best Atacama is overall rank 14, 9.21."

**2:00 – 3:15 · Compare with Gale (scroll down on the same page)**
- **Elevation distribution** tab: solid white = Gale, dotted = Gale from real observations only. "The two Gale lines are almost the same, so
  the window-scale picture doesn't depend on interpolation."
- **Maps** tab: right-hand teal map. "This is how little of Gale is directly observed."
- **Roughness** tab: "This is where interpolation matters most; treat the Gale line as soft."

**3:15 – 4:15 · Methodology › Validation**
- Click **Methodology**, tab **Validation**.
- "We tried 28 reasonable method variants. Afar leads in 10." Point at the by-scaler table: Earth-only and robust scaling, 0.
- Point at the support table: 3×3 patches 1.4% fully observed, 11×11 zero.
- Point at the correlation heatmap: "Three of our six features are the same signal."
- Say it plainly: "So we don't claim Afar beats Atacama. We claim neither is close, and we show why."

**4:15 – 4:45 · Results and exports**
- Click **Results and exports**. Pick Afar_0002, press **Report for Afar_0002 (Markdown)**; open **Preview report**.
- Mention the original CSVs are downloadable unchanged.

**4:45 – 5:00 · Close**
- "A researcher can add a Mars reference and Earth region and get a ranked, explained, honest first-pass shortlist. Next: more regions, independent windows,
  and a Moon reference."

**If something breaks:** the map is only one part. Use the candidate dropdown (same selection) and the **Terrain lab** page. Turn the basemap to **None (offline)**.
