# Presentation outline (about 8 slides, 5–7 minutes)

**1. The problem.** Rover and instrument tests need Earth sites that behave like the target terrain. Choosing them is mostly done by expert
judgement. Can measured terrain statistics give a first shortlist?

**2. What we built.** REDTWIN SCOUT: pick a Mars reference, rank Earth terrain windows by six measured terrain statistics, click through candidates
on a map, see why each ranked where it did. Screenshot of the explorer.

**3. Why Gale.** Well-studied Mars site with strong relief (crater floor to rim), and it is where Curiosity works. Its MOLA coverage is thin (29% direct, see slide 7).
(Say this as motivation. Don't claim Gale is typical of Mars.)

**4. Earth regions and data.** Afar (Dallol/Danakil area) and the Atacama: arid, tectonically or volcanically active, sparsely vegetated, and
commonly cited as Mars-like environments. We chose them; we did not search the world. Data: NASA/USGS SRTM 30 m (Earth), NASA MOLA 463 m (Mars).

**5. How the comparison works.** Put both on the same ~463 m grid (329 × 320 cells, about 152 × 148 km). Six features per window: elevation spread,
relief, median and steep slope, roughness, local relief. Standardise, rank by distance to Gale. Distance is not a probability.

**6. What we found.** In the original ranking Afar_0002 (14.19°N, 39.82°E) is closest, distance 8.44; best Atacama is rank 14 at 9.21. Afar edges ahead
because the single closest window on five of six features is in Afar; on relief, the largest single gap, the closest window is in Atacama.

**7. What the 29.11% means and how we tested.** Only 29% of Gale's cells are real measurements; the rest are interpolated. Direct-only elevation spread and
relief change by under 1%; roughness and local relief can't be measured directly at all. We ran 28 method variants: Afar leads in 10. With only the
directly supported features, Atacama leads, by a hair. No Earth window matches Gale's relief (4,435 m vs max 2,763 m). Windows overlap 90%: effectively
two independent samples.

**8. What remains uncertain, and what's next.** Not shown: geology, habitability, safety, any lunar result. Next: more Earth regions and non-overlapping windows,
feature set built from directly observed data only, a Moon reference, expert validation. How it helps: a transparent first-pass screen that tells a
researcher where to look, and says how much to trust it.

## Say / don't say
- Say: "least different", "preliminary", "exploratory", "29% directly observed".
- Don't say: "best analogue", "similarity percentage", "proves", "AI predicts", "searches the Earth".
- If asked "is it AI?": it's a feature-extraction and nearest-neighbour ranking, a standard statistical method; no neural networks, no learned model.
