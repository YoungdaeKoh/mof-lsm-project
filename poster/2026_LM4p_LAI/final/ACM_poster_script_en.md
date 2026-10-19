# ACM 2026 poster — speaking script (easy English)

Poster: "Evaluation of global leaf area index simulated by LM4+, the land component of KIOST-ESM2"
Target length: full version about 3 minutes; short version about 30 seconds.

---

## A. 30-second version (when someone just walks by)

Hi! This poster is about leaves in a land model.
KIOST is building a new Earth system model, KIOST-ESM2, and its land part is LM4+ from GFDL.
I ran LM4+ alone, offline, and compared its leaf area with satellite data.
The model has too many leaves — about 40 percent too many in summer.
In the north, the main problem is timing: the leaves fall more than one month too late in autumn.
The reason is that the model only uses temperature to drop leaves. Real trees also use day length.
When I added a day-length rule, about half of the autumn error went away.

---

## A2. 1-minute version

Hello, I'm Youngdae Koh from Chonnam National University.
KIOST is building a new Earth system model, KIOST-ESM2. Its land part is LM4+, from GFDL.
I ran LM4+ alone, with observed weather, and compared its leaf area index, or LAI, with satellite data from 1982 to 2010.

(Figure 1) The model puts leaves in the right places, but it has too many.
In summer, global LAI is 41 percent too high.
In the boreal forest, most of the error comes from autumn to spring, not from summer.

(Figure 2) The reason is timing. In the north, the model drops its leaves 27 to 38 days too late, every year.
The model uses only temperature to drop leaves. Real trees also use day length.

(Figure 3) So I added a simple rule: leaves can fall only when the day is shorter than 14 hours.
This cut the autumn delay about in half, from 33 to 16 days, and spring did not change.

Next, I will fix the species map and use changing CO2. Thank you!

---

## B. Full version (about 3 minutes)

### 1. Introduction (point to INTRODUCTION)
Hello, I'm Youngdae Koh from Chonnam National University.
KIOST is developing KIOST-ESM2 for CMIP7. Its land model is LM4+, from GFDL.
In LM4+, plants grow as groups of trees of different sizes. We call them cohorts.
So leaves, biomass, and forest structure change with the climate.

Leaves are important because they control how energy, water, and carbon move
between the land and the air. If the leaf amount is wrong, the climate model can also go wrong.

I ran the land model offline. "Offline" means the land model runs alone,
with observed weather as input. This way we can see the land model's own errors.

My question is simple:
Does LM4+ get the right amount of leaves, and the right timing? If not, why?

### 2. Data and methods (point to DATA & METHODS)
For observations, I used the satellite product GIMMS LAI4g.
LAI means leaf area index — how many layers of leaves cover the ground.
I compared 1982 to 2010 on the same 1-degree grid.
I looked at the growing season, May to September, and at the seasonal cycle in four northern regions.
To find the timing, I used the day when LAI crosses 50 percent of its yearly range.
Start of season is "SOS", end of season is "EOS".

### 3. Result 1 — too many leaves (point to Figure 1)
Here is the observation, the model, and the difference.
The model gets the big pattern right. Forests are in the right places.
But the model has too many leaves almost everywhere.
The global summer mean is 2.77 in the model and 1.97 in the satellite data. That is 41 percent too high.
The biggest excess is in South America and Africa.

In the boreal forest, between 50 and 70 degrees north, something interesting happens.
The summer peak is only 15 percent too high.
But the yearly mean is 56 percent too high.
87 percent of this error comes from September to April — outside the growing season.
So in the north, the problem is not "how much", it is "when".

### 4. Result 2 — leaves fall too late (point to Figure 2)
These are the seasonal cycles in four regions: the satellite and the model. The dashed lines show the end of season.
In every region, the model drops its leaves 27 to 38 days too late.
This happens in all 29 years. Spring is also late, by 13 to 27 days.

Why? In the model, leaves fall only when a 20-day average temperature goes below 5 degrees Celsius.
Daily temperature reaches 5 degrees about 20 days after the real leaf fall,
and the 20-day average adds about 17 more days.
For example, in East Siberia, the satellite says leaves fall on September 3rd. The model says October 11th.

When real leaves fall, the day length is about 13 hours.
So real trees seem to use day length as a signal. The model does not have this signal.

### 5. Result 3 — a simple fix (point to Figure 3)
I tested two changes for the year 2010.
First, "TC10": I only raised the temperature limit from 5 to 10 degrees.
Leaves fall earlier, but spring also gets later. That is not good.
Second, "DL14 plus TC10": leaves can fall only when the day is shorter than 14 hours.
This removes the autumn excess: 65 percent in Northern Europe, 50 percent in the Russian Far East,
38 percent in northwest North America, and 20 percent in East Siberia.
Spring does not change.
For 50 to 70 degrees north, the leaf-fall delay goes from 33 days to 16 days — about half.
This also changes the fluxes: in autumn, with the temperature-only change (TC10), evapotranspiration drops about 4.5 percent and GPP about 11 percent.

### 6. Summary (point to SUMMARY)
To sum up:
One. LM4+ gets the pattern of leaves right, but has about 40 percent too many.
Two. In the north, the main reason is late leaf fall in autumn, by one to two months.
Three. The cause is a temperature-only rule. Adding day length fixes about half of the error.
Next, I will replant tree species using an observed map, use changing CO2,
and then test the effect in the coupled KIOST-ESM2.
Thank you! Any questions?

---

## C. Possible questions and simple answers

**Q. Why offline and not coupled?**
A. In a coupled model, the weather in the model also has errors. Offline, the weather comes from observations (WFDE5), so the leaf errors belong to the land model itself.

**Q. Why is LAI too high in the tropics? Day length can't explain that.**
A. Right. In the tropics the error is in the amount, not the timing — it is high all year. One reason is the species map: the model has very little C4 grass in the savanna and more trees and C3 grass. This is my next step.

**Q. Why do you use day length?**
A. In the satellite data, leaves fall when the day is about 12.7 to 13.3 hours long, in several regions. Many studies show that day length controls autumn leaf fall (for example, Zohner et al., 2023).

**Q. Is your spin-up long enough?**
A. I ran the 1981–2010 forcing twice. In the second cycle, LAI changed by less than 1 percent, so leaves and GPP are stable. Only the slow wood carbon is still growing.

**Q. What about CO2?**
A. In this run, CO2 was almost fixed at the pre-industrial level. I am now running a new experiment with the observed CO2 time series and land-use change.

**Q. Did the fix work for larch?**
A. The day-length rule was added for larch and C3 grass. But larch is almost missing in the model's current species map, so I will replant species from an observed map and test again.

**Q. Why is the effect smallest in East Siberia (20 %)?**
A. East Siberia should be mostly larch forest, but the model has almost no larch there. So the new rule has few trees to act on.
