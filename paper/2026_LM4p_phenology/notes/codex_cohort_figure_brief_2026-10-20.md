# Task: draw a concept figure of how LM4.1 (PPA) organises vegetation — grid cell → tiles → cohorts → canopy layers

Audience: a climate PhD student who knows CLM4 CNDV (one "average individual" per PFT) and needs to grasp the PPA
cohort idea. Also usable as a Methods/SI schematic in a phenology paper. Labels in English.

## Facts to show (verified from the code / our runs; do not invent other numbers)
- Grid cell (C96 cubed sphere, ~1°) is split into **tiles**: land patches with different history (land use: primary
  / secondary / cropland / pasture; and time since disturbance, e.g. a gap created when canopy trees die). Our runs
  allow up to 18 tiles per cell (restart dimension).
- Each tile has ONE canopy-air temperature and humidity (shared by all cohorts in the tile), one soil column.
- A **cohort** = a group of individuals of the SAME species and SIMILAR size (height/DBH), with a density nindivs
  (individuals m^-2). Same species can appear in several cohorts (big spruce, small spruce). Up to 65 cohorts per tile
  (restart dimension). July 2010, 50–70N tiles with that species: picea mean 7.9 cohorts (max 19), acer 5.8 (max 19),
  c3grass 1.0 (grass ≈ one cohort).
- PPA (Perfect Plasticity Approximation, Purves et al. 2007/2008, Strigul et al. 2008, Weng et al. 2015): cohorts are
  sorted by height; their crowns fill canopy LAYER 1 from the tallest down until crown area = ground area; the rest
  goes to layer 2, etc. Crowns are "plastic" (fill gaps), so only height order matters, not x-y position.
  Upper layer gets light first; lower layers are shaded.
- Per cohort the model solves its own leaf temperature, photosynthesis, and keeps its own leaf ON/OFF status and GDD.
  The phenology temperature (20-day smoothed canopy-AIR temperature) is per tile.
- LAI of a cohort = leaf carbon / LMA / crown area; grid LAI ≈ sum over cohorts of LAI × fraction of ground covered.
- Contrast panel: CLM4 CNDV = PFTs side by side sharing area, one average individual each, no height layering.

## Deliverable
- Write a self-contained Python/matplotlib script `cohort_concept_codex.py` and its output `cohort_concept_codex.png`
  (≥ 200 dpi) into the current working directory only. Interpreter: /opt/homebrew/bin/python3 (matplotlib available).
- Suggested layout (you may improve it): (a) grid cell split into tiles (e.g. old forest, gap after treefall,
  cropland); (b) side view of one forest tile: tree icons of different heights/species, layer-1 / layer-2 boundary,
  sunlight arrow, each cohort labelled (species, height, n per m2), one shared canopy-air box; (c) CNDV vs PPA contrast.
- Keep text minimal and readable; no invented numbers beyond those above (use "e.g." for illustrative heights).
- At the end, print a 5-line explanation of the design choices.
