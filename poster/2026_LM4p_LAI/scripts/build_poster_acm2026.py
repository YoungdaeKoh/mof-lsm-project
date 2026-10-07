#!/usr/bin/env python3
"""Fill the ACM 2026 poster template with the LM4+ LAI diagnosis (text, table, figures).

template : /Volumes/data01/발표_템플릿/전남대/poster/poster_2026_ACM.pptx (never modified)
output   : ../poster_2026_ACM_draft.pptx
Text formatting (font size, bullets) is copied from the first paragraph of each template box;
figure placeholders are replaced by PNGs scaled to the box width; right-column boxes are re-stacked
so Figure 2 (seasonal cycle + EOS maps) and Figure 3 (normalized cycle) get full column width.
"""
import copy
import shutil
from pptx import Presentation
from pptx.util import Inches, Pt

T = "/Volumes/data01/발표_템플릿/전남대/poster/poster_2026_ACM.pptx"
OUT = "../poster_2026_ACM_draft.pptx"
FIG = "../figures/"
shutil.copy2(T, OUT)
p = Presentation(OUT); s = p.slides[0]
# template shape names (the three title placeholders share the name "Text 1" and are left untouched)
NAMES = {"Header: RESULTS 1": "Header: RESULTS 1: OBSERVED RELATIONSHIP", "Header text: RESULTS 1": "Header text: RESULTS 1: OBSERVED RELATIONSHIP",
         "Header: RESULTS 2": "Header: RESULTS 2: MECHANISM", "Header text: RESULTS 2": "Header text: RESULTS 2: MECHANISM",
         "Header: RESULTS 3": "Header: RESULTS 3: MODEL EXPERIMENT", "Header text: RESULTS 3": "Header text: RESULTS 3: MODEL EXPERIMENT",
         "Header: SUMMARY": "Header: SUMMARY & CONCLUSIONS", "Header text: SUMMARY": "Header text: SUMMARY &amp; CONCLUSIONS",
         "Header: REFERENCES": "Header: REFERENCES & ACKNOWLEDGEMENTS", "Header text: REFERENCES": "Header text: REFERENCES &amp; ACKNOWLEDGEMENTS",
         "Figure 1 placeholder": "Figure 1 placeholder box", "Figure 2 placeholder": "Figure 2 placeholder box", "Figure 3 placeholder": "Figure 3 placeholder box"}
_by_name = {x.name: x for x in s.shapes if x.name != "Text 1"}
sh = {k: _by_name[NAMES.get(k, k)] for k in list(NAMES) + ["Introduction body", "Data table", "Methods body", "Figure 1 placeholder label", "Caption 1",
      "Results 1 body", "Figure 2 placeholder label", "Caption 2", "Results 2 body", "Figure 3 placeholder label", "Results 3 body", "Caption 3",
      "Conclusions body", "References body"]}
IN = 914400


A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
CHECK_PPR = ('<a:pPr xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" marL="457200" indent="-457200">'
             '<a:buFont typeface="Wingdings" pitchFamily="2" charset="2"/><a:buChar char="&#252;"/></a:pPr>')   # check-mark bullet (user's edit, 2026-10-07)


def fill(box, items, size=None, blank_between=False, bullet=None):
    """items: list of (text, bold) -> one paragraph each, formatting copied from the template's first paragraph.
    blank_between: empty paragraph between items; bullet: pPr XML string applied to every item paragraph."""
    from lxml import etree
    tf = box.text_frame
    p0 = tf.paragraphs[0]._p; pPr = p0.find(A + "pPr")
    r0 = tf.paragraphs[0].runs[0]._r; rPr = r0.find(A + "rPr")
    if bullet:
        pPr = etree.fromstring(bullet)
        old = p0.find(A + "pPr")
        if old is not None:
            p0.remove(old)
        p0.insert(0, copy.deepcopy(pPr))
    for par in list(tf.paragraphs)[1:]:
        par._p.getparent().remove(par._p)
    for k, (text, bold) in enumerate(items):
        if k > 0 and blank_between:
            tf.add_paragraph()
        par = tf.paragraphs[0] if k == 0 else tf.add_paragraph()
        if k > 0 and pPr is not None:
            par._p.insert(0, copy.deepcopy(pPr))
        for r in list(par.runs):
            r._r.getparent().remove(r._r)
        run = par.add_run(); run.text = text
        if rPr is not None:
            run._r.insert(0, copy.deepcopy(rPr))
        run.font.bold = bold
        if size:
            run.font.size = Pt(size)


def place(box, png, label_box=None, top=None, width=None):
    """Replace a placeholder rectangle by a picture scaled to the box width (aspect kept)."""
    from PIL import Image
    w, h = Image.open(FIG + png).size
    left = box.left; wd = width or box.width; tp = top if top is not None else box.top
    pic = s.shapes.add_picture(FIG + png, left, tp, width=wd)
    box._element.getparent().remove(box._element)
    if label_box is not None:
        label_box._element.getparent().remove(label_box._element)
    pic.name = "Picture " + png
    return pic


def move(box, top, height=None):
    box.top = int(top * IN)
    if height:
        box.height = int(height * IN)


# ---------------------------------------------------------------- title block: unchanged
# ---------------------------------------------------------------- introduction
intro = sh["Introduction body"]; tf = intro.text_frame
fill(intro, [
    ("Background: KIOST is developing KIOST-ESM2 for CMIP7 with GFDL's LM4+ (LM4 family) as its land component. "
     "LM4+ grows vegetation as size-structured cohorts (PPA), so leaf area, biomass and canopy structure evolve with climate.", True),
    ("Vegetation controls the land–atmosphere exchange of energy, water and carbon; a biased leaf area index (LAI) therefore "
     "feeds back on the coupled climate. Offline evaluation under observed forcing isolates the land model's own errors.", False),
    ("Key question: Does offline LM4+ reproduce the magnitude and the phenology of global LAI, and what causes the mismatch?", True),
    ("Objective 1: Benchmark 1982–2010 LAI against GIMMS LAI4g (pattern, magnitude, seasonal cycle).", False),
    ("Objective 2: Trace the autumn leaf-off delay to the phenology rule and test a day-length cue in pilot runs.", False),
])
_ps = list(tf.paragraphs)
for k in (4, 3, 2):          # blank line before the key question and each objective (user's edit); reverse order keeps indices valid
    new = tf.add_paragraph()._p; new.getparent().remove(new); _ps[k]._p.addprevious(new)

# ---------------------------------------------------------------- data table (add one row) and methods
tbl = sh["Data table"].table
tr = tbl._tbl.tr_lst[-1]; tbl._tbl.append(copy.deepcopy(tr))        # 5th row, copies the last row's formatting
rows = [["Dataset", "Setup / variables", "Period / resolution"],
        ["LM4+ offline (KIOST-ESM2)", "PPA cohorts, 6 species, fixed species map, N cycle off, CO₂ fixed", "1979–2023, C96 (≈1°) → 1°"],
        ["WFDE5 forcing (Cucchi et al. 2020)", "ERA5 bias-corrected with CRU/GPCC; T, q, wind, SW, LW, precip.", "1979–2023, 0.5° hourly → C96"],
        ["Initial land state", "KIOST-ESM2 ≈400-yr coupled piControl + 1 cycle WFDE5 1981–2010", "start 1979-01-01"],
        ["GIMMS LAI4g (Cao et al. 2023)", "AVHRR LAI, consolidated with MODIS", "1982–2010, 15-day 1/12° → monthly 1°"]]
for i, row in enumerate(rows):
    tbl.rows[i].height = Inches(0.75 if i == 0 else 1.05)
    for j, txt in enumerate(row):
        cell = tbl.cell(i, j); par = cell.text_frame.paragraphs[0]
        r0 = par.runs[0] if par.runs else par.add_run()
        for r in list(par.runs)[1:]:
            r._r.getparent().remove(r._r)
        r0.text = txt; r0.font.size = Pt(22)
move(sh["Methods body"], 27.9, 3.6)
fill(sh["Methods body"], [
    ("Evaluation: 1982–2010 monthly climatology on a common 1° grid; MJJAS mean and bias; seasonal cycles in six IPCC AR6 regions. "
     "SOS/EOS = dates at which the interpolated monthly cycle crosses 50 % of its amplitude.", True),
    ("Pilot runs (year 2010 from the 1 Jan 2010 CTRL state): TC10 raises the leaf-off temperature threshold 5 → 10 °C; "
     "DL14+TC10 adds a day-length (< 14 h) leaf-off condition (code patch; larch and C3 grass).", False),
], size=28)

# ---------------------------------------------------------------- results 1 (left column, Fig. 1)
sh["Header text: RESULTS 1"].text_frame.paragraphs[0].runs[0].text = "RESULTS 1: GROWING-SEASON LAI"
for nm in ("Header: RESULTS 1", "Header text: RESULTS 1"):
    move(sh[nm], 31.8)
pic1 = place(sh["Figure 1 placeholder"], "fig1_lai_mean_bias.png", sh["Figure 1 placeholder label"], top=int(33.3 * IN), width=int(14.0 * IN))
pic1.left = int((1.0 + (16.3 - 14.0) / 2) * IN)
move(sh["Caption 1"], 47.5, 1.4); move(sh["Results 1 body"], 49.0, 5.3)
fill(sh["Caption 1"], [("Figure 1. Growing-season (MJJAS) LAI, 1982–2010: (a) GIMMS LAI4g, (b) LM4+, (c) LM4+ − GIMMS. "
                        "Side panels: zonal means. Polygons: the AR6 regions used in Figs. 2–3.", True)])
fill(sh["Results 1 body"], [
    ("The large-scale pattern is reproduced, but LAI is too high almost everywhere: global MJJAS mean 2.77 vs 1.97 (+41 %); annual +54 %.", False),
    ("Largest excess over tropical and subtropical South America and Africa.", False),
    ("Boreal forest (50–70°N): the summer peak is only +15 % too high, yet the annual mean is +56 % too high — "
     "87 % of the bias comes from the off-season (Sep–Apr). The extratropical excess is a timing problem.", True),
])

# ---------------------------------------------------------------- results 2 (right column, Fig. 2 = seasonal cycle + EOS maps)
sh["Header text: RESULTS 2"].text_frame.paragraphs[0].runs[0].text = "RESULTS 2: SEASONAL TIMING AND ITS CAUSE"
RW = 14.5; RL = int((18.1 + (16.3 - RW) / 2) * IN)        # right-column figure width and left edge (centred)
pic2 = place(sh["Figure 2 placeholder"], "fig2_regional_seasonal_cycle.png", sh["Figure 2 placeholder label"], top=int(12.8 * IN), width=int(RW * IN)); pic2.left = RL
y = pic2.top / IN + pic2.height / IN + 0.15
move(sh["Caption 2"], y, 1.4)
fill(sh["Caption 2"], [("Figure 2. Climatological LAI seasonal cycle, 1982–2010, GIMMS vs LM4+ in six AR6 regions; "
                        "markers: SOS/EOS at 50 % of the amplitude.", True)])
y += 1.5
move(sh["Results 2 body"], y, 4.6)
fill(sh["Results 2 body"], [
    ("Leaf-off (EOS) is 28–70 days too late in every region (NWN +33, ESB +38, RFE +28, ENA +42, WCE +49, EAS +70 d); "
     "boreal leaf-on is also late (+13–24 d).", True),
    ("Cause: leaves are dropped only when the 20-day smoothed canopy temperature falls below 5 °C (10 °C for broadleaf trees). "
     "Daily T < 5 °C is reached ≈20 d after the observed EOS and the smoothing adds ≈17 d: ESB observed 3 Sep → model 11 Oct.", False),
    ("The observed EOS instead clusters at a day length of 11.4–13.3 h regardless of temperature: a day-length cue is missing.", False),
])
y += 4.8
# ---------------------------------------------------------------- results 3 (Fig. 3 normalized cycle, full width)
for nm in ("Header: RESULTS 3", "Header text: RESULTS 3"):
    move(sh[nm], y)
sh["Header text: RESULTS 3"].text_frame.paragraphs[0].runs[0].text = "RESULTS 3: DAY-LENGTH LEAF-OFF PILOT RUNS"
y += 1.5
pic3 = place(sh["Figure 3 placeholder"], "fig3b_phentest_regions_normalised_dl.png", sh["Figure 3 placeholder label"], top=int(y * IN), width=int(RW * IN)); pic3.left = RL
y += pic3.height / IN + 0.1
move(sh["Caption 3"], y, 1.4)
fill(sh["Caption 3"], [("Figure 3. Normalized 2010 LAI cycle, (LAI − min)/(max − min), in six regions: GIMMS, CTRL, TC10 and DL14+TC10.", True)])
y += 1.5
b3 = sh["Results 3 body"]; b3.left = int(18.1 * IN); b3.width = int(16.3 * IN); move(b3, y, 5.0)
fill(b3, [
    ("Temperature threshold alone (TC10): the autumn drop moves little and spring leaf-on is delayed as a side effect.", False),
    ("DL14+TC10 removes 20–50 % of the Sep–Oct excess in boreal regions (NWN 38 %, ESB 20 %, RFE 50 %); "
     "the 50–70°N EOS bias falls from +33 to +16 d with spring unchanged.", True),
    ("Temperate regions are unchanged: the rule was applied only to larch and C3 grass; broadleaf trees need a ≈11.5 h cue.", False),
    ("Even the small TC10 shift changes Sep–Oct fluxes at 50–70°N: ET −4.5 %, GPP −11 %, runoff +4.7 %.", False),
])
y += 5.2
# ---------------------------------------------------------------- summary
for nm in ("Header: SUMMARY", "Header text: SUMMARY"):
    move(sh[nm], y)
y += 1.5
move(sh["Conclusions body"], y, 5.6)
fill(sh["Conclusions body"], [
    ("Offline LM4+ reproduces the global LAI pattern but overestimates it (+41 % in MJJAS); in the extratropics the excess "
     "comes mainly from a 1–2 month delay of autumn leaf-off.", True),
    ("The delay follows from a temperature-only phenology rule (5 °C threshold on a 20-day smoothed temperature); "
     "observations point to day length as the missing cue.", True),
    ("A day-length leaf-off rule removes about half of the boreal EOS bias with no spring side effect; "
     "type-specific thresholds (larch 13.5 h, C3 grass 12.5 h, broadleaf 11.5 h) are being tested.", True),
    ("Next: replant species from an observed map (larch is nearly absent in the current state), time-varying CO₂ "
     "and the C–N version, then coupled KIOST-ESM2 experiments.", False),
], bullet=CHECK_PPR)
y += 5.8 + 0.56              # references header 0.56 in lower (user's edit)
for nm in ("Header: REFERENCES", "Header text: REFERENCES"):
    move(sh[nm], y)
y += 1.4
move(sh["References body"], y, 3.39)
fill(sh["References body"], [
    ("Cao, S., et al. (2023). ESSD, 15, 4877. • Cucchi, M., et al. (2020). ESSD, 12, 2097. • Shevliakova, E., et al. (2024). JAMES, 16. "
     "• Weng, E., et al. (2015). Biogeosciences, 12, 2655. • Iturbide, M., et al. (2020). ESSD, 12, 2959. "
     "• Zohner, C. M., et al. (2023). Science, 381, eadf5098.", False),
    ("Acknowledgements: This work was supported by Korea Environment Industry & Technology Institute (KEITI) through "
     "“Climate Change R&D Project for New Climate Regime.”, funded by Korea Ministry of Climate, Energy and Environment (MCEE) "
     "(RS-2022-KE002160). This research was supported by Korea Institute of Marine Science & Technology Promotion (KIMST) "
     "funded by the Ministry of Oceans and Fisheries (RS-2026-25543619).", True),
], size=20)
p.save(OUT)
print("saved", OUT, "| bottom of references box at %.1f in (slide %.1f)" % (y + sh["References body"].height / IN, 55.12))
for nm in ("Picture fig1_lai_mean_bias.png", "Picture fig2_regional_seasonal_cycle.png", "Picture fig3b_phentest_regions_normalised_dl.png"):
    x = [q for q in s.shapes if q.name == nm][0]
    print("  %-48s y %.1f..%.1f  w %.1f" % (nm, x.top / IN, (x.top + x.height) / IN, x.width / IN))
