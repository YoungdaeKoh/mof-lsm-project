# LMWG (lnd_diag) 표준 진단 변수표

출처: `CESM_postprocessing-master/lnd_diag/inputFiles/` (set*.txt + variable_master4.3.ncl)

생성: `analysis/diag/extract_lmwg_varlist.py`. 기계용 전체 표는 `lmwg_diag_variables.csv`.

- 진단 세트 8개 / 고유 변수 481개 / (세트,변수) 항목 1541개

## set1 — Global annual trends (energy balance, soil water/ice+T, runoff, snow, photosynthesis)

**C13 isotope** (74)

| 변수 | 설명 | 단위 |
|---|---|---|
| `C13_NEE` | C13 Net Ecosys Exchange of C | gC/m^2/s |
| `C13_NBP` | C13 net biome production, includes fire, landuse and harvest flux | gC/m^2/s |
| `C13_NEP` | C13 Net Ecosystem Production | gC/m^2/s |
| `C13_GPP` | C13 Gross Primary Production | gC/m^2/s |
| `C13_PSNSUN_TO_CPOOL` | C13 GPP from Sunlit Canopy | gC/m^2/s |
| `C13_PSNSHADE_TO_CPOOL` | C13 GPP from Shaded Canopy | gC/m^2/s |
| `C13_NPP` | C13 Net Primary Production | gC/m^2/s |
| `C13_AGNPP` | C13 Aboveground NPP | gC/m^2/s |
| `C13_BGNPP` | C13 Belowground NPP | gC/m^2/s |
| `C13_MR` | C13 Maintenance Respiration | gC/m^2/s |
| `C13_GR` | C13 Total Growth Respiration | gC/m^2/s |
| `C13_AR` | C13 Autotrophic Respiration (MR + GR) | gC/m^2/s |
| `C13_LITHR` | C13 Litter Hetereotrophic Respiration | gC/m^2/s |
| `C13_SOMHR` | C13 SOM Hetereotrophic Respiration | gC/m^2/s |
| `C13_HR` | C13 Total Hetereotrophic Respiration | gC/m^2/s |
| `C13_RR` | C13 Root Respiration (Fine Root MR + Total Root GR) | gC/m^2/s |
| `C13_SR` | C13 Totl Soil Respiration (HR + Root Resp) | gC/m^2/s |
| `C13_ER` | C13 Totl Ecosystem Respiration (AR + HR) | gC/m^2/s |
| `C13_LEAFC` | C13 Leaf Carbon | gC/m^2 |
| `C13_SOIL3C` | C13 Soil Organic Matter C (Slow Pool) | gC/m^2 |
| `C13_SOIL4C` | C13 Soil Organic Matter C (Slowest Pool) | gC/m^2 |
| `C13_FROOTC` | C13 Fine Root CC | gC/m^2 |
| `C13_LIVESTEMC` | C13 Live Stem C | gC/m^2 |
| `C13_DEADSTEMC` | C13 Dead Stem Carbon | gC/m^2 |
| `C13_LIVECROOTC` | C13 Live Coarse Root Carbon | gC/m^2 |
| `C13_DEADCROOTC` | C13 Dead Coarse Root Carbon | gC/m^2 |
| `C13_CPOOL` | C13 Temporary Photosynthate C Pool | gC/m^2 |
| `C13_TOTVEGC` | C13 Total Vegetation C, Excluding Cpool | gC/m^2 |
| `C13_CWDC` | C13 Coarse Woody Debris Carbon | gC/m^2 |
| `C13_CWD_C` | C13 Coarse Woody Debris Carbon | gC/m^2 |
| `C13_TOTLITC` | C13 Totl Litter Carbon | gC/m^2 |
| `C13_TOTSOMC` | C13 Total SOM Carbon | gC/m^2 |
| `C13_TOTECOSYSC` | C13 Totl Ecosystem C, Incl Veg But Excl Cpool | gC/m^2 |
| `C13_COL_CTRUNC` | C13 Column-Level Sink for C Truncation | gC/m^2 |
| `C13_PFT_CTRUNC` | C13 Pft-Level Sink for C Truncation | gC/m^2 |
| `C13_COL_FIRE_CLOSS` | C13 Totl Col-Level Fire C Loss | gC/m^2/s |
| `C13_PFT_FIRE_CLOSS` | C13 Totl Pft-Level Fire C Loss | gC/m^2/s |
| `C14_NEE` | C14 Net Ecosys Exchange of C | gC/m^2/s |
| `C14_NBP` | C14 net biome production, includes fire, landuse and harvest flux | gC/m^2/s |
| `C14_NEP` | C14 Net Ecosystem Production | gC/m^2/s |
| `C14_GPP` | C14 Gross Primary Production | gC/m^2/s |
| `C14_PSNSUN_TO_CPOOL` | C14 GPP from Sunlit Canopy | gC/m^2/s |
| `C14_PSNSHADE_TO_CPOOL` | C14 GPP from Shaded Canopy | gC/m^2/s |
| `C14_NPP` | C14 Net Primary Production | gC/m^2/s |
| `C14_AGNPP` | C14 Aboveground NPP | gC/m^2/s |
| `C14_BGNPP` | C14 Belowground NPP | gC/m^2/s |
| `C14_MR` | C14 Maintenance Respiration | gC/m^2/s |
| `C14_GR` | C14 Total Growth Respiration | gC/m^2/s |
| `C14_AR` | C14 Autotrophic Respiration (MR + GR) | gC/m^2/s |
| `C14_LITHR` | C14 Litter Hetereotrophic Respiration | gC/m^2/s |
| `C14_SOMHR` | C14 SOM Hetereotrophic Respiration | gC/m^2/s |
| `C14_HR` | C14 Total Hetereotrophic Respiration | gC/m^2/s |
| `C14_RR` | C14 Root Respiration (Fine Root MR + Total Root GR) | gC/m^2/s |
| `C14_SR` | C14 Totl Soil Respiration (HR + Root Resp) | gC/m^2/s |
| `C14_ER` | C14 Totl Ecosystem Respiration (AR + HR) | gC/m^2/s |
| `C14_LEAFC` | C14 Leaf Carbon | gC/m^2 |
| `C14_SOIL3C` | C14 Soil Organic Matter C (Slow Pool) | gC/m^2 |
| `C14_SOIL4C` | C14 Soil Organic Matter C (Slowest Pool) | gC/m^2 |
| `C14_FROOTC` | C14 Fine Root CC | gC/m^2 |
| `C14_LIVESTEMC` | C14 Live Stem C | gC/m^2 |
| `C14_DEADSTEMC` | C14 Dead Stem Carbon | gC/m^2 |
| `C14_LIVECROOTC` | C14 Live Coarse Root Carbon | gC/m^2 |
| `C14_DEADCROOTC` | C14 Dead Coarse Root Carbon | gC/m^2 |
| `C14_CPOOL` | C14 Temporary Photosynthate C Pool | gC/m^2 |
| `C14_TOTVEGC` | C14 Total Vegetation C, Excluding Cpool | gC/m^2 |
| `C14_CWDC` | C14 Coarse Woody Debris Carbon | gC/m^2 |
| `C14_CWD_C` | C14 Coarse Woody Debris Carbon | gC/m^2 |
| `C14_TOTLITC` | C14 Totl Litter Carbon | gC/m^2 |
| `C14_TOTSOMC` | C14 Total SOM Carbon | gC/m^2 |
| `C14_TOTECOSYSC` | C14 Totl Ecosystem C, Incl Veg But Excl Cpool | gC/m^2 |
| `C14_COL_CTRUNC` | C14 Column-Level Sink for C Truncation | gC/m^2 |
| `C14_PFT_CTRUNC` | C14 Pft-Level Sink for C Truncation | gC/m^2 |
| `C14_COL_FIRE_CLOSS` | C14 Totl Col-Level Fire C Loss | gC/m^2/s |
| `C14_PFT_FIRE_CLOSS` | C14 Totl Pft-Level Fire C Loss | gC/m^2/s |

**CASA** (55)

| 변수 | 설명 | 단위 |
|---|---|---|
| `SURFMETC` | Total Metabolized Litter C | gC/m^2 |
| `SURFSTRC` | Total Structural Litter C | gC/m^2 |
| `SOILMETC` | Total Metabolized Structural Soil C | gC/m^2 |
| `SOILSTRC` | Total Structural Soil C | gC/m^2 |
| `SURFMIC` | Total Microbial Litter C | gC/m^2 |
| `SOILMIC` | Total Microbial Soil C | gC/m^2 |
| `SLOWC` | Total Slow C Pool | gC/m^2 |
| `PASSIVEC` | Total Passive C Pool | gC/m^2 |
| `RESP_LEAFC` | Respired Leaf C | gC/m^2 |
| `RESP_WOODC` | Respired Wood C | gC/m^2 |
| `RESP_FROOTC` | Respired Fine Root C | gC/m^2 |
| `RESP_SURFMETC` | Respired Metabolized Litter C | gC/m^2 |
| `RESP_SURFSTRC` | Respired Structural Litter C | gC/m^2 |
| `RESP_SOILMETC` | Respired Metabolized Soil C | gC/m^2 |
| `RESP_SOILSTRC` | Respired Structural Soil C | gC/m^2 |
| `RESP_CWDC` | Respired Coarse Woody Debris C | gC/m^2 |
| `RESP_SURFMIC` | Respired Microbial Litter C | gC/m^2 |
| `RESP_SOILMIC` | Respired Microbial Soil C | gC/m^2 |
| `RESP_SLOWC` | Respired Slow C Pool | gC/m^2 |
| `RESP_PASSIVEC` | Respired Passive C Pool | gC/m^2 |
| `CLOSS_LEAF` | Leaf C Loss | gC/m^2 |
| `CLOSS_WOOD` | Wood C Loss | gC/m^2 |
| `CLOSS_FROOT` | Fine Root C Loss | gC/m^2 |
| `CLOSS_SURFMET` | Metabolized Litter C Loss | gC/m^2 |
| `CLOSS_SURFSTR` | Structural Litter C Loss | gC/m^2 |
| `CLOSS_SOILMET` | Metabolized Structural Soil C Loss | gC/m^2 |
| `CLOSS_SOILSTR` | Structural Soil C Loss | gC/m^2 |
| `CLOSS_CWD` | Coarse Woody Debris C Loss | gC/m^2 |
| `CLOSS_SURFMIC` | Microbial Litter C Loss | gC/m^2 |
| `CLOSS_SOILMIC` | Microbial Soil C Loss | gC/m^2 |
| `CLOSS_SLOW` | Slow C Pool Loss | gC/m^2 |
| `CLOSS_PASSIVE` | Passive C Pool Loss | gC/m^2 |
| `CFLUX` | Total C Flux | gC/m^2/s |
| `CO2FLUX` | Net CO2 Flux | gC/m^2/s |
| `PET` | Potential ET | mm/s |
| `EXCESSC` | Excess C | gC/m^2/s |
| `PLAI` | Prognostic LAI | m^2/m^2 |
| `DEGDAY` | Accumulated Degree Days | C |
| `TDAYAVG` | Daily Averaged T | C |
| `STRESST` | Temperature stress fcn for leaf loss | unitless |
| `STRESSW` | Water stress fcn for leaf loss | unitless |
| `STRESSCD` | Cold+drought stress fcn for leaf loss | unitless |
| `LGROW` | Growing season index (0 or 1) | — |
| `ISEABEG` | Index for start of growing season | — |
| `NSTEPBEG` | Nstep at start of growing season | — |
| `BGTEMP` | Temperature Dependence | unitless |
| `XSCPOOL` | total excess C | g/m^2 |
| `WLIM` | water limitation used in bgmoist (atmp factor) | unitless |
| `SOILT` | Soil temperature: top 30cm | C |
| `SMOIST` | Soil moisture: top 30cm | mm3/mm3 |
| `WATOPT` | watopt for entire column | mm3/mm3 |
| `WATDRY` | watdry for entire column | mm3/mm3 |
| `LIVEFR_LEAFC` | Live Fraction Leaf C | gC/m^2 |
| `LIVEFR_WOODC` | Live Fraction Wood C | gC/m^2 |
| `LIVEFR_FROOTC` | Live Fraction Froot C | gC/m^2 |

**CLM/CLAMP** (52)

| 변수 | 설명 | 단위 |
|---|---|---|
| `GROUND` | heat flux into soil | W/m2 |
| `LATENT` | Latent Heat Flux | W/m2 |
| `SENSIBLE` | Sensible Heat Flux | W/m2 |
| `SENSIBLE_GND` | Sensible Heat Flux from Ground | W/m2 |
| `SENSIBLE_VEG` | Sensible Heat Flux from Vegetation | W/m2 |
| `REL_HUM` | Relative Humidity at 2m | kg/kg |
| `SPEC_HUM_2M` | Specific Humidity at 2m | kg/kg |
| `SPEC_HUM` | Atmospheric Specific Humidity | kg/kg |
| `RAIN` | atmospheric rain | mm/s |
| `SNOW` | atmospheric snow | mm/s |
| `BTRAN` | transpiration beta factor | unitless |
| `CANOPY_EVAPORATION` | Canopy Evaporation | mm/s |
| `DRAINAGE` | Subsurface Drainage | mm/s |
| `ET` | Evapotranspiration | mm/s |
| `INTERCEPTION` | Canopy Interception | mm/s |
| `RUNOFF` | Surface Runoff | mm/s |
| `SNOW_DEPTH` | Snow depth | mm |
| `SOIL_EVAPORATION` | Soil Evaporation | mm/s |
| `SOIL_ICE` | Soil Ice in each soil layer | kg/m2 |
| `SOIL_LIQUID` | Soil Liquid Water | kg/m2 |
| `SOIL_PSI` | Soil Water Potential | MPa |
| `TOTAL_SOIL_ICE` | Total soil ice | kg/m2 |
| `TOTAL_SOIL_LIQUID` | total soil liquid water | kg/m2 |
| `TRANSPIRATION` | Transpiration | mm/s |
| `VOL_SOIL_WATER` | Volumetric Soil Water | mm3/mm3 |
| `ALL_SKY_ALBEDO` | All-Sky Albedo | proportion |
| `BLACK_SKY_ALBEDO` | Surface Black-Sky Albedo | proportion |
| `IRDOWN` | Downward Infrared Radiation | W/m2 |
| `IRUP` | Upward Infrared Radiation | W/m2 |
| `LAISHA` | Shaded Projected Leaf Area Index | m^2/m^2 |
| `LAISUN` | Sunlit Projected Leaf Area Index | m2/m2 |
| `NETIR` | Net Infrared (longwave) Radiation | W/m2 |
| `NETRAD` | Net radiation | W/m2 |
| `REFLECT` | Total Reflected Solar Radiation | W/m2 |
| `SNOW_FRACTION` | Snow Fraction | unitless |
| `SOLAR` | Total Incident Solar Radiation | W/m2 |
| `SOLAR_AB` | Total Absorbed Solar Radiation | W/m2 |
| `SOLAR_ABG` | Solar Radiation Absorbed by Ground | W/m2 |
| `SOLAR_ABV` | Solar Rad Absorbed by Vegetation | W/m2 |
| `DEGREE_DAYS` | Accumulated degree days | K |
| `TREFMNAV` | daily minimum of average 2m temperature | K |
| `TREFMXAV` | daily maximum of average 2m temperature | K |
| `TSA2M` | 2m Air Temperature | K |
| `TSOIL` | soil temperature | K |
| `TVEG` | Vegetation Temperature | K |
| `ELAI` | exposed one-sided leaf area index | m2/m2 |
| `ESAI` | exposed one-sided stem area index | m2/m2 |
| `TLAI` | total one-sided leaf area index | m2/m2 |
| `TSAI` | total one-sided stem area index | m2/m2 |
| `PHOTOSYNTHESIS` | Photosynthesis | umol/m2s |
| `RSSHA` | shaded leaf stomatal resistance | s/m |
| `RSSUN` | Sunlit leaf stomatal resistance | s/m |

**CLM core** (75)

| 변수 | 설명 | 단위 |
|---|---|---|
| `TSA` | 2m air temperature | K |
| `PREC` | ppt: rain+snow | mm/s |
| `TOTRUNOFF` | Total Liquid Runoff | mm/s |
| `TSOI` | soil temperature | K |
| `FPSN` | photosynthesis | umol/m^2/s |
| `ELAI` | exposed one-sided leaf area index | m2/m2 |
| `ESAI` | exposed one-sided stem area index | m2/m2 |
| `TLAI` | total one-sided leaf area index | m2/m2 |
| `TSAI` | total one-sided stem area index | m2/m2 |
| `LAISUN` | Sunlit Projected Leaf Area Index | m2/m2 |
| `LAISHA` | Shaded Projected Leaf Area Index | m^2/m^2 |
| `BTRAN` | transpiration beta factor | unitless |
| `QINFL` | infiltration | mm/s |
| `QOVER` | surface runoff | mm/s |
| `QIRRIG` | — | — |
| `QRGWL` | surface runoff at glaciers (liquid only), wetlands, lakes | mm/s |
| `QDRAI` | sub-surface drainage | mm/s |
| `QINTR` | interception | mm/s |
| `QSOIL` | ground evaporation | mm/s |
| `QVEGT` | canopy transpiration | mm/s |
| `FSH` | sensible heat | W/m^2 |
| `FSH_TO_COUPLER` | sensible heat sent to coupler | W/m^2 |
| `FSH_PRECIP_CONVERSION` | SHF from conv of rain/snow atm forcing | W/m^2 |
| `FSH_RUNOFF_ICE_TO_LIQ` | SHF from conv of ice runoff to liquid | W/m^2 |
| `CPL_ENERGY_BAL` | Coupler Energy Balance (Global Area) | W/m2 |
| `SOILLIQ` | soil liquid water | kg/m^2 |
| `SOILICE` | soil ice | kg/m^2 |
| `SOILPSI` | soil water potential in each soil layer | MPa |
| `SNOWLIQ` | snow liquid water | kg/m^2 |
| `SNOWICE` | snow ice | kg/m^2 |
| `FSNO` | fraction of ground covered by snow | unitless |
| `H2OSNO` | total snow water equiv (SNOWICE + SNOWLIQ) | mm |
| `TOTSOILLIQ` | total soil liquid water | kg/m^2 |
| `TOTSOILICE` | total soil ice | kg/m^2 |
| `WA` | water in the unconfined aquifer | mm |
| `ZWT` | water table depth | m |
| `QCHARGE` | aquifer recharge rate | mm/s |
| `FCOV` | fractional area with water table at surface | unitless [0-1] |
| `CO2_PPMV` | CO2 concentration | ppmv |
| `TWS` | total water storage | mm |
| `VOLR` | river channel total water storage | m3 |
| `DSTDEP` | total dust deposition (dry+wet) from atmosphere | kg/m2/s |
| `DSTFLXT` | total surface dust emission | kg/m2/s |
| `OCDEP` | total OC deposition (dry+wet) from atmosphere | kg/m2/s |
| `BCDEP` | total BC deposition (dry+wet) from atmosphere | kg/m2/s |
| `FSDSND` | direct nir incident solar radiation | W/m^2 |
| `FSDSVD` | direct vis incident solar radiation | W/m^2 |
| `FSDSNI` | diffuse nir incident solar radiation | W/m^2 |
| `FSDSVI` | diffuse vis incident solar radiation | W/m^2 |
| `RAIN_FROM_ATM` | atmospheric rain (pre-downscaling) | mm/s |
| `SNOW_FROM_ATM` | atmospheric snow (pre-downscaling) | mm/s |
| `FLDS_NOT_DOWNSCALED` | atmospheric longwave radiation (pre-downscaling) | W/m^2 |
| `ZBOT` | atmospheric reference height | m |
| `Tair_from_atm` | atmospheric air temperature (pre-downscaling) | K |
| `Thair_from_atm` | atmospheric air potential temperature (pre-downscaling) | K |
| `QBOT_NOT_DOWNSCALED` | atmospheric specific humidity (pre-downscaling) | kg/kg |
| `PBOT_NOT_DOWNSCALED` | atm pressure of bottom layer (pre-downscaling) | Pa |
| `Rho_from_atm` | atmospheric density of bottom layer (pre-downscaling) | kg/m3 |
| `UWIND` | atmospheric uwind velocity magnitude | m/s |
| `VWIND` | atmospheric vwind velocity magnitude | m/s |
| `BCPHIDRY` | BC deposition (phidry) from atmosphere | kg/m2/s |
| `BCPHODRY` | BC deposition (phodry) from atmosphere | kg/m2/s |
| `BCPHIWET` | BC deposition (phiwet) from atmosphere | kg/m2/s |
| `OCPHIDRY` | OC deposition (phidry) from atmosphere | kg/m2/s |
| `OCPHODRY` | OC deposition (phodry) from atmosphere | kg/m2/s |
| `OCPHIWET` | OC deposition (phiwet) from atmosphere | kg/m2/s |
| `DSTWET1` | dust deposition (wet1) from atmosphere | kg/m2/s |
| `DSTDRY1` | dust deposition (dry1) from atmosphere | kg/m2/s |
| `DSTWET2` | dust deposition (wet2) from atmosphere | kg/m2/s |
| `DSTDRY2` | dust deposition (dry2) from atmosphere | kg/m2/s |
| `DSTWET3` | dust deposition (wet3) from atmosphere | kg/m2/s |
| `DSTDRY3` | dust deposition (dry3) from atmosphere | kg/m2/s |
| `DSTWET4` | dust deposition (wet4) from atmosphere | kg/m2/s |
| `DSTDRY4` | dust deposition (dry4) from atmosphere | kg/m2/s |
| `ATM_TOPO` | atmospheric surface height | m |

**CN/CLAMP** (34)

| 변수 | 설명 | 단위 |
|---|---|---|
| `AGNPP` | above ground net primary production | gC/m^2/s |
| `AR` | autotrophic respiration (MR + GR) | gC/m^2/s |
| `BGNPP` | below ground net primary production | gC/m^2/s |
| `BIOGENIC_CO` | Biogenic CO Flux | uG/m2/h |
| `CWDC` | coarse woody debris carbon | gC/m^2 |
| `CWDC_HR` | Coarse Woody Debris C Hetereotrophic respiration | gC/m2s |
| `CWDC_LOSS` | Coarse Woody Debris C Loss | gC/m2s |
| `FROOTC` | fine root carbon | gC/m^2 |
| `FROOTC_ALLOC` | Fine root C allocation | gC/m2s |
| `FROOTC_LOSS` | Fine root C Loss | gC/m2s |
| `GPP` | gross primary production | gC/m^2/s |
| `GROSS_NMIN` | gross N mineralization | gN/m^2/s |
| `HR` | total hetereotrophic respiration | gC/m^2/s |
| `ISOPRENE` | Isoprene Flux | uG/m2/h |
| `LEAFC` | leaf carbon | gC/m^2 |
| `LEAFC_ALLOC` | Leaf C Allocation | gC/m2s |
| `LEAFC_LOSS` | Leaf C Loss | gC/m2s |
| `LITTERC` | Total Litter C | gC/m2 |
| `LITTERC_HR` | Litter Hetereotrophic Respiration | gC/m2s |
| `LITTERC_LOSS` | Litter C Loss | gC/m2s |
| `MONOTERPENE` | Monoterpene Flux | uG/m2/h |
| `NEE` | net ecosys exchange of C | gC/m^2/s |
| `NEP` | net ecosystem production | gC/m^2/s |
| `NET_NMIN` | net N mineralization | gN/m^2/s |
| `NPP` | net primary production | gC/m^2/s |
| `OTHER_VOC` | Other VOC Flux | uG/m2/h |
| `OR_VOC` | Other Reactive VOC Flux | uG/m2/h |
| `SOILC` | soil organic matter C (fast pool) | gC/m2 |
| `SOILC_HR` | Soil C hetereotrophic respiration | gC/m2s |
| `SOILC_LOSS` | Soil C Loss | gC/m2s |
| `VOCFLXT` | Total VOC flux into Atmosphere | uG/m2/h |
| `WOODC` | Live+Dead Stem C | gC/m2 |
| `WOODC_ALLOC` | Wood C Allocation | gC/m2s |
| `WOODC_LOSS` | Wood C Loss | gC/m2s |

**CN (carbon-nitrogen)** (130)

| 변수 | 설명 | 단위 |
|---|---|---|
| `NEE` | net ecosys exchange of C | gC/m^2/s |
| `NEP` | net ecosystem production | gC/m^2/s |
| `NBP` | net biome production, includes fire, landuse and harvest flux | gC/m^2/s |
| `GPP` | gross primary production | gC/m^2/s |
| `CUE` | carbon use efficiency | NPP/GPP |
| `BTRAN2` | root zone soil moisture factor | unitless |
| `PSNSUN_TO_CPOOL` | GPP from Sunlit Canopy | gC/m^2/s |
| `PSNSHADE_TO_CPOOL` | GPP from Shaded Canopy | gC/m^2/s |
| `NPP` | net primary production | gC/m^2/s |
| `AGNPP` | above ground net primary production | gC/m^2/s |
| `BGNPP` | below ground net primary production | gC/m^2/s |
| `MR` | maintenance respiration | gC/m^2/s |
| `GR` | total growth respiration | gC/m^2/s |
| `AR` | autotrophic respiration (MR + GR) | gC/m^2/s |
| `LITHR` | litter hetereotrophic respiration | gC/m^2/s |
| `SOMHR` | SOM hetereotrophic respiration | gC/m^2/s |
| `HR` | total hetereotrophic respiration | gC/m^2/s |
| `RR` | root respiration (fine root MR + total root GR) | gC/m^2/s |
| `SR` | total soil respiration (HR + root resp) | gC/m^2/s |
| `ER` | total ecosystem respiration (AR + HR) | gC/m^2/s |
| `FINUNDATED` | Fractional inundated of veg col | unitless |
| `FCH4` | Gridcell surface CH4 flux | kgC/m^2/s |
| `FCH4TOCO2` | Gridcell oxidation of CH4 to CO2 | gC/m^2/s |
| `FCH4_DFSAT` | CH4 additional flux | kgC/m^2/s |
| `CH4PROD` | Gridcell total CH4 production | gC/m^2/s |
| `CH4_SURF_AERE_SAT` | aerenchyma sfc CH4 flx-inundated area | mol/m^2/s |
| `CH4_SURF_AERE_UNSAT` | aerenchyma sfc CH4 flx-non-inundated area | mol/m^2/s |
| `CH4_SURF_DIFF_SAT` | diffusive sfc CH4 flx-inundated/lake area | mol/m^2/s |
| `CH4_SURF_DIFF_UNSAT` | diffusive sfc CH4 flx-non-inundated area | mol/m^2/s |
| `CH4_SURF_EBUL_SAT` | ebullition sfc CH4 flx-inundated/lake area | mol/m^2/s |
| `CH4_SURF_EBUL_UNSAT` | ebullition sfc CH4 flx-non-inundated area | mol/m^2/s |
| `LEAFC` | leaf carbon | gC/m^2 |
| `LEAFN` | leaf nitrogen | gN/m^2 |
| `LEAFCN` | leaf carbon/nitrogen | gC/gN |
| `SOIL3C` | Soil organic matter C (slow pool) | gC/m^2 |
| `SOIL4C` | Soil organic matter C (slowest pool) | gC/m^2 |
| `FROOTC` | fine root carbon | gC/m^2 |
| `LIVESTEMC` | live stem C | gC/m^2 |
| `DEADSTEMC` | dead stem carbon | gC/m^2 |
| `LIVECROOTC` | live coarse root carbon | gC/m^2 |
| `DEADCROOTC` | dead coarse root carbon | gC/m^2 |
| `CPOOL` | temporary photosynthate C pool | gC/m^2 |
| `XSMRPOOL` | Temporary Photosynthate C Pool | gC/m^2 |
| `TOTVEGC` | total vegetation C, excluding cpool | gC/m^2 |
| `TOTVEGN` | total vegetation N | gN/m^2 |
| `TOTVEGCN` | total vegetation C/N | gC/gN |
| `CWDC` | coarse woody debris carbon | gC/m^2 |
| `CWD_C` | coarse woody debris carbon | gC/m^2 |
| `TOTLITC` | total litter carbon | gC/m^2 |
| `TOTLITC_1m` | total litter carbon to 1m depth | gC/m^2 |
| `TOTLITN` | total litter N | gN/m^2 |
| `TOTLITN_1m` | total litter N to 1m depth | gN/m^2 |
| `TOTSOMC` | total SOM carbon | gC/m^2 |
| `TOTSOMC_1m` | total SOM carbon to 1 meter depth | gC/m^2 |
| `TOTSOMN` | total soil organic matter N | gN/m^2 |
| `TOTSOMN_1m` | total soil organic matter N to 1m depth | gN/m^2 |
| `TOTECOSYSC` | total ecosystem C, incl veg but excl cpool | gC/m^2 |
| `TOTCOLC` | total column C, incl veg and cpool | gC/m^2 |
| `COL_CTRUNC` | column-level sink for C truncation | gC/m^2 |
| `PFT_CTRUNC` | pft-level sink for C truncation | gC/m^2 |
| `FPG` | fraction of potential GPP | proportion |
| `FPI` | fraction of potential immobilization | proportion |
| `TOTECOSYSN` | total ecosystem N | gN/m^2 |
| `NDEP_TO_SMINN` | nitrogen deposition | gN/m^2/s |
| `FERT` | fertilizer added | gN/m^2/s |
| `FERT_TO_SMINN` | fertilizer to soil mineral N | gN/m^2/s |
| `NFERTILIZATION` | fertilizer added | gN/m^2/s |
| `NFIX_TO_SMINN` | nitrogen fixation | gN/m^2/s |
| `NAM` | AM-associated N uptake flux | gN/m^2/s |
| `NECM` | ECM-associated N uptake flux | gN/m^2/s |
| `NFIX` | Symbiotic BNF uptake flux | gN/m^2/s |
| `NRETRANS` | Retranslocated N uptake flux | gN/m^2/s |
| `NPP_NUPTAKE` | total carbon used by N uptake in FUN | gC/m^2/s |
| `NUPTAKE_FRACTION` | NPP_NUPTAKE/(NPP_NUPTAKE+NPP) | unitless |
| `FFIX_TO_SMINN` | free living N fixation to soil mineral N | gN/m^2/s |
| `NPP_NFIX` | Symbiotic BNF uptake used C | gC/m^2/s |
| `NPP_NACTIVE` | Mycorrhizal N uptake used C | gC/m^2/s |
| `NPP_NRETRANS` | retranslocated N uptake flux | gC/m^2/s |
| `SUPPLEMENT_TO_SMINN` | supplement to mineral nitrogen | gN/m^2/s |
| `SMINN_LEACHED` | Nitrogen Leached | gN/m^2/s |
| `SMIN_NO3_LEACHED` | Soil NO3 pool loss to leaching | gN/m^2/s |
| `SMIN_NO3_RUNOFF` | Soil NO3 pool loss to runoff | gN/m^2/s |
| `SMINN` | soil mineral N | gN/m^2 |
| `SMINN_TO_NPOOL` | Mineral N to NPool | gN/m^2/s |
| `COL_NTRUNC` | column-level sink for N truncation | gN/m^2 |
| `PFT_NTRUNC` | pft-level sink for N truncation | gN/m^2 |
| `RETRANSN` | plant pool of retranslocated N | gN/m^2 |
| `RETRANSN_TO_NPOOL` | Retranslocated N to NPool | gN/m^2/s |
| `POTENTIAL_IMMOB` | Potential Immobilization | gN/m^2/s |
| `ACTUAL_IMMOB` | Actual Immobilization | gN/m^2/s |
| `GROSS_NMIN` | gross N mineralization | gN/m^2/s |
| `NET_NMIN` | net N mineralization | gN/m^2/s |
| `NDEPLOY` | total N deployed in new growth | gN/m^2/s |
| `DENIT` | Total Denitrification | gN/m^2/s |
| `SOIL3N` | soil organic matter N (slow pool) | gN/m^2 |
| `SOIL4N` | Soil organic matter N (slowest pool) | gN/m^2 |
| `COL_FIRE_CLOSS` | total column-level fire C loss | gC/m^2/s |
| `PFT_FIRE_CLOSS` | total pft-level fire C loss | gC/m^2/s |
| `COL_FIRE_NLOSS` | total column-level fire N loss | gN/m^2/s |
| `PFT_FIRE_NLOSS` | total pft-level fire N loss | gN/m^2/s |
| `FAREA_BURNED` | fractional area burned | proportion/s |
| `BAF_CROP` | fractional area burned - crop | proportion/s |
| `CWDC_HR` | Coarse Woody Debris C Hetereotrophic respiration | gC/m2s |
| `CWDC_LOSS` | Coarse Woody Debris C Loss | gC/m2s |
| `FROOTC_ALLOC` | Fine root C allocation | gC/m2s |
| `FROOTC_LOSS` | Fine root C Loss | gC/m2s |
| `LEAFC_ALLOC` | Leaf C Allocation | gC/m2s |
| `LEAFC_LOSS` | Leaf C Loss | gC/m2s |
| `LITTERC` | Total Litter C | gC/m2 |
| `LITTERC_HR` | Litter Hetereotrophic Respiration | gC/m2s |
| `LITTERC_LOSS` | Litter C Loss | gC/m2s |
| `SOILC` | soil organic matter C (fast pool) | gC/m2 |
| `SOILC_HR` | Soil C hetereotrophic respiration | gC/m2s |
| `SOILC_LOSS` | Soil C Loss | gC/m2s |
| `WOODC` | Live+Dead Stem C | gC/m2 |
| `WOODC_ALLOC` | Wood C Allocation | gC/m2s |
| `WOODC_LOSS` | Wood C Loss | gC/m2s |
| `WOOD_HARVESTC` | Wood Harvest C (to prod pools) | gC/m2s |
| `WOOD_HARVESTN` | Wood Harvest N (to prod pools) | gN/m2s |
| `TOT_WOODPRODC_LOSS` | Total C loss from wood prod pools | gC/m2s |
| `TOT_WOODPRODN_LOSS` | Total N loss from wood prod pools | gN/m2s |
| `PROD10C_LOSS` | C loss from 10-yr wood prod pool | gC/m2s |
| `PROD10N_LOSS` | N loss from 10-yr wood prod pool | gN/m2s |
| `PROD100C_LOSS` | C loss from 100-yr wood prod pool | gC/m2s |
| `PROD100N_LOSS` | N loss from 100-yr wood prod pool | gN/m2s |
| `DWT_PROD10C_GAIN` | LCC-driven addition to 10-yr wood prod pool | gC/m2s |
| `DWT_PROD10N_GAIN` | LCC-driven addition to 10-yr wood prod pool | gN/m2s |
| `DWT_PROD100C_GAIN` | LCC-driven addition to 100-yr wood prod pool | gC/m2s |
| `DWT_PROD100N_GAIN` | LCC-driven addition to 100-yr wood prod pool | gN/m2s |
| `DWT_CONV_CFLUX` | conversion C flux (immediate loss to atm) | gC/m2s |

## set2 — Horizontal contour plots of DJF/MAM/JJA/SON/ANN means

**C13 isotope** (70)

| 변수 | 설명 | 단위 |
|---|---|---|
| `C13_NEE` | C13 Net Ecosys Exchange of C | gC/m^2/s |
| `C13_NBP` | C13 net biome production, includes fire, landuse and harvest flux | gC/m^2/s |
| `C13_NEP` | C13 Net Ecosystem Production | gC/m^2/s |
| `C13_GPP` | C13 Gross Primary Production | gC/m^2/s |
| `C13_PSNSUN_TO_CPOOL` | C13 GPP from Sunlit Canopy | gC/m^2/s |
| `C13_PSNSHADE_TO_CPOOL` | C13 GPP from Shaded Canopy | gC/m^2/s |
| `C13_NPP` | C13 Net Primary Production | gC/m^2/s |
| `C13_AGNPP` | C13 Aboveground NPP | gC/m^2/s |
| `C13_BGNPP` | C13 Belowground NPP | gC/m^2/s |
| `C13_MR` | C13 Maintenance Respiration | gC/m^2/s |
| `C13_GR` | C13 Total Growth Respiration | gC/m^2/s |
| `C13_AR` | C13 Autotrophic Respiration (MR + GR) | gC/m^2/s |
| `C13_LITHR` | C13 Litter Hetereotrophic Respiration | gC/m^2/s |
| `C13_SOMHR` | C13 SOM Hetereotrophic Respiration | gC/m^2/s |
| `C13_HR` | C13 Total Hetereotrophic Respiration | gC/m^2/s |
| `C13_RR` | C13 Root Respiration (Fine Root MR + Total Root GR) | gC/m^2/s |
| `C13_SR` | C13 Totl Soil Respiration (HR + Root Resp) | gC/m^2/s |
| `C13_ER` | C13 Totl Ecosystem Respiration (AR + HR) | gC/m^2/s |
| `C13_LEAFC` | C13 Leaf Carbon | gC/m^2 |
| `C13_SOIL3C` | C13 Soil Organic Matter C (Slow Pool) | gC/m^2 |
| `C13_SOIL4C` | C13 Soil Organic Matter C (Slowest Pool) | gC/m^2 |
| `C13_FROOTC` | C13 Fine Root CC | gC/m^2 |
| `C13_LIVESTEMC` | C13 Live Stem C | gC/m^2 |
| `C13_DEADSTEMC` | C13 Dead Stem Carbon | gC/m^2 |
| `C13_LIVECROOTC` | C13 Live Coarse Root Carbon | gC/m^2 |
| `C13_DEADCROOTC` | C13 Dead Coarse Root Carbon | gC/m^2 |
| `C13_CPOOL` | C13 Temporary Photosynthate C Pool | gC/m^2 |
| `C13_TOTVEGC` | C13 Total Vegetation C, Excluding Cpool | gC/m^2 |
| `C13_CWDC` | C13 Coarse Woody Debris Carbon | gC/m^2 |
| `C13_CWD_C` | C13 Coarse Woody Debris Carbon | gC/m^2 |
| `C13_TOTLITC` | C13 Totl Litter Carbon | gC/m^2 |
| `C13_TOTSOMC` | C13 Total SOM Carbon | gC/m^2 |
| `C13_TOTECOSYSC` | C13 Totl Ecosystem C, Incl Veg But Excl Cpool | gC/m^2 |
| `C13_COL_FIRE_CLOSS` | C13 Totl Col-Level Fire C Loss | gC/m^2/s |
| `C13_PFT_FIRE_CLOSS` | C13 Totl Pft-Level Fire C Loss | gC/m^2/s |
| `C14_NEE` | C14 Net Ecosys Exchange of C | gC/m^2/s |
| `C14_NBP` | C14 net biome production, includes fire, landuse and harvest flux | gC/m^2/s |
| `C14_NEP` | C14 Net Ecosystem Production | gC/m^2/s |
| `C14_GPP` | C14 Gross Primary Production | gC/m^2/s |
| `C14_PSNSUN_TO_CPOOL` | C14 GPP from Sunlit Canopy | gC/m^2/s |
| `C14_PSNSHADE_TO_CPOOL` | C14 GPP from Shaded Canopy | gC/m^2/s |
| `C14_NPP` | C14 Net Primary Production | gC/m^2/s |
| `C14_AGNPP` | C14 Aboveground NPP | gC/m^2/s |
| `C14_BGNPP` | C14 Belowground NPP | gC/m^2/s |
| `C14_MR` | C14 Maintenance Respiration | gC/m^2/s |
| `C14_GR` | C14 Total Growth Respiration | gC/m^2/s |
| `C14_AR` | C14 Autotrophic Respiration (MR + GR) | gC/m^2/s |
| `C14_LITHR` | C14 Litter Hetereotrophic Respiration | gC/m^2/s |
| `C14_SOMHR` | C14 SOM Hetereotrophic Respiration | gC/m^2/s |
| `C14_HR` | C14 Total Hetereotrophic Respiration | gC/m^2/s |
| `C14_RR` | C14 Root Respiration (Fine Root MR + Total Root GR) | gC/m^2/s |
| `C14_SR` | C14 Totl Soil Respiration (HR + Root Resp) | gC/m^2/s |
| `C14_ER` | C14 Totl Ecosystem Respiration (AR + HR) | gC/m^2/s |
| `C14_LEAFC` | C14 Leaf Carbon | gC/m^2 |
| `C14_SOIL3C` | C14 Soil Organic Matter C (Slow Pool) | gC/m^2 |
| `C14_SOIL4C` | C14 Soil Organic Matter C (Slowest Pool) | gC/m^2 |
| `C14_FROOTC` | C14 Fine Root CC | gC/m^2 |
| `C14_LIVESTEMC` | C14 Live Stem C | gC/m^2 |
| `C14_DEADSTEMC` | C14 Dead Stem Carbon | gC/m^2 |
| `C14_LIVECROOTC` | C14 Live Coarse Root Carbon | gC/m^2 |
| `C14_DEADCROOTC` | C14 Dead Coarse Root Carbon | gC/m^2 |
| `C14_CPOOL` | C14 Temporary Photosynthate C Pool | gC/m^2 |
| `C14_TOTVEGC` | C14 Total Vegetation C, Excluding Cpool | gC/m^2 |
| `C14_CWDC` | C14 Coarse Woody Debris Carbon | gC/m^2 |
| `C14_CWD_C` | C14 Coarse Woody Debris Carbon | gC/m^2 |
| `C14_TOTLITC` | C14 Totl Litter Carbon | gC/m^2 |
| `C14_TOTSOMC` | C14 Total SOM Carbon | gC/m^2 |
| `C14_TOTECOSYSC` | C14 Totl Ecosystem C, Incl Veg But Excl Cpool | gC/m^2 |
| `C14_COL_FIRE_CLOSS` | C14 Totl Col-Level Fire C Loss | gC/m^2/s |
| `C14_PFT_FIRE_CLOSS` | C14 Totl Pft-Level Fire C Loss | gC/m^2/s |

**CASA** (55)

| 변수 | 설명 | 단위 |
|---|---|---|
| `SURFMETC` | Total Metabolized Litter C | gC/m^2 |
| `SURFSTRC` | Total Structural Litter C | gC/m^2 |
| `SOILMETC` | Total Metabolized Structural Soil C | gC/m^2 |
| `SOILSTRC` | Total Structural Soil C | gC/m^2 |
| `SURFMIC` | Total Microbial Litter C | gC/m^2 |
| `SOILMIC` | Total Microbial Soil C | gC/m^2 |
| `SLOWC` | Total Slow C Pool | gC/m^2 |
| `PASSIVEC` | Total Passive C Pool | gC/m^2 |
| `RESP_LEAFC` | Respired Leaf C | gC/m^2 |
| `RESP_WOODC` | Respired Wood C | gC/m^2 |
| `RESP_FROOTC` | Respired Fine Root C | gC/m^2 |
| `RESP_SURFMETC` | Respired Metabolized Litter C | gC/m^2 |
| `RESP_SURFSTRC` | Respired Structural Litter C | gC/m^2 |
| `RESP_SOILMETC` | Respired Metabolized Soil C | gC/m^2 |
| `RESP_SOILSTRC` | Respired Structural Soil C | gC/m^2 |
| `RESP_CWDC` | Respired Coarse Woody Debris C | gC/m^2 |
| `RESP_SURFMIC` | Respired Microbial Litter C | gC/m^2 |
| `RESP_SOILMIC` | Respired Microbial Soil C | gC/m^2 |
| `RESP_SLOWC` | Respired Slow C Pool | gC/m^2 |
| `RESP_PASSIVEC` | Respired Passive C Pool | gC/m^2 |
| `CLOSS_LEAF` | Leaf C Loss | gC/m^2 |
| `CLOSS_WOOD` | Wood C Loss | gC/m^2 |
| `CLOSS_FROOT` | Fine Root C Loss | gC/m^2 |
| `CLOSS_SURFMET` | Metabolized Litter C Loss | gC/m^2 |
| `CLOSS_SURFSTR` | Structural Litter C Loss | gC/m^2 |
| `CLOSS_SOILMET` | Metabolized Structural Soil C Loss | gC/m^2 |
| `CLOSS_SOILSTR` | Structural Soil C Loss | gC/m^2 |
| `CLOSS_CWD` | Coarse Woody Debris C Loss | gC/m^2 |
| `CLOSS_SURFMIC` | Microbial Litter C Loss | gC/m^2 |
| `CLOSS_SOILMIC` | Microbial Soil C Loss | gC/m^2 |
| `CLOSS_SLOW` | Slow C Pool Loss | gC/m^2 |
| `CLOSS_PASSIVE` | Passive C Pool Loss | gC/m^2 |
| `CFLUX` | Total C Flux | gC/m^2/s |
| `CO2FLUX` | Net CO2 Flux | gC/m^2/s |
| `PET` | Potential ET | mm/s |
| `EXCESSC` | Excess C | gC/m^2/s |
| `PLAI` | Prognostic LAI | m^2/m^2 |
| `DEGDAY` | Accumulated Degree Days | C |
| `TDAYAVG` | Daily Averaged T | C |
| `STRESST` | Temperature stress fcn for leaf loss | unitless |
| `STRESSW` | Water stress fcn for leaf loss | unitless |
| `STRESSCD` | Cold+drought stress fcn for leaf loss | unitless |
| `LGROW` | Growing season index (0 or 1) | — |
| `ISEABEG` | Index for start of growing season | — |
| `NSTEPBEG` | Nstep at start of growing season | — |
| `BGTEMP` | Temperature Dependence | unitless |
| `XSCPOOL` | total excess C | g/m^2 |
| `WLIM` | water limitation used in bgmoist (atmp factor) | unitless |
| `SOILT` | Soil temperature: top 30cm | C |
| `SMOIST` | Soil moisture: top 30cm | mm3/mm3 |
| `WATOPT` | watopt for entire column | mm3/mm3 |
| `WATDRY` | watdry for entire column | mm3/mm3 |
| `LIVEFR_LEAFC` | Live Fraction Leaf C | gC/m^2 |
| `LIVEFR_WOODC` | Live Fraction Wood C | gC/m^2 |
| `LIVEFR_FROOTC` | Live Fraction Froot C | gC/m^2 |

**CLM/CLAMP** (52)

| 변수 | 설명 | 단위 |
|---|---|---|
| `TSA2M` | 2m Air Temperature | K |
| `RAIN` | atmospheric rain | mm/s |
| `RUNOFF` | Surface Runoff | mm/s |
| `ALL_SKY_ALBEDO` | All-Sky Albedo | proportion |
| `GROUND` | heat flux into soil | W/m2 |
| `NETIR` | Net Infrared (longwave) Radiation | W/m2 |
| `NETRAD` | Net radiation | W/m2 |
| `LATENT` | Latent Heat Flux | W/m2 |
| `SENSIBLE` | Sensible Heat Flux | W/m2 |
| `SENSIBLE_GND` | Sensible Heat Flux from Ground | W/m2 |
| `SENSIBLE_VEG` | Sensible Heat Flux from Vegetation | W/m2 |
| `REL_HUM` | Relative Humidity at 2m | kg/kg |
| `SPEC_HUM_2M` | Specific Humidity at 2m | kg/kg |
| `SPEC_HUM` | Atmospheric Specific Humidity | kg/kg |
| `SNOW` | atmospheric snow | mm/s |
| `BTRAN` | transpiration beta factor | unitless |
| `CANOPY_EVAPORATION` | Canopy Evaporation | mm/s |
| `DRAINAGE` | Subsurface Drainage | mm/s |
| `ET` | Evapotranspiration | mm/s |
| `INTERCEPTION` | Canopy Interception | mm/s |
| `SNOW_DEPTH` | Snow depth | mm |
| `SOIL_EVAPORATION` | Soil Evaporation | mm/s |
| `SOIL_ICE` | Soil Ice in each soil layer | kg/m2 |
| `SOIL_LIQUID` | Soil Liquid Water | kg/m2 |
| `SOIL_PSI` | Soil Water Potential | MPa |
| `TOTAL_SOIL_ICE` | Total soil ice | kg/m2 |
| `TOTAL_SOIL_LIQUID` | total soil liquid water | kg/m2 |
| `TRANSPIRATION` | Transpiration | mm/s |
| `VOL_SOIL_WATER` | Volumetric Soil Water | mm3/mm3 |
| `BLACK_SKY_ALBEDO` | Surface Black-Sky Albedo | proportion |
| `IRDOWN` | Downward Infrared Radiation | W/m2 |
| `IRUP` | Upward Infrared Radiation | W/m2 |
| `LAISHA` | Shaded Projected Leaf Area Index | m^2/m^2 |
| `LAISUN` | Sunlit Projected Leaf Area Index | m2/m2 |
| `REFLECT` | Total Reflected Solar Radiation | W/m2 |
| `SNOW_FRACTION` | Snow Fraction | unitless |
| `SOLAR` | Total Incident Solar Radiation | W/m2 |
| `SOLAR_AB` | Total Absorbed Solar Radiation | W/m2 |
| `SOLAR_ABG` | Solar Radiation Absorbed by Ground | W/m2 |
| `SOLAR_ABV` | Solar Rad Absorbed by Vegetation | W/m2 |
| `DEGREE_DAYS` | Accumulated degree days | K |
| `TREFMNAV` | daily minimum of average 2m temperature | K |
| `TREFMXAV` | daily maximum of average 2m temperature | K |
| `TSOIL` | soil temperature | K |
| `TVEG` | Vegetation Temperature | K |
| `ELAI` | exposed one-sided leaf area index | m2/m2 |
| `ESAI` | exposed one-sided stem area index | m2/m2 |
| `TLAI` | total one-sided leaf area index | m2/m2 |
| `TSAI` | total one-sided stem area index | m2/m2 |
| `PHOTOSYNTHESIS` | Photosynthesis | umol/m2s |
| `RSSHA` | shaded leaf stomatal resistance | s/m |
| `RSSUN` | Sunlit leaf stomatal resistance | s/m |

**CLM core** (137)

| 변수 | 설명 | 단위 |
|---|---|---|
| `TSA` | 2m air temperature | K |
| `PREC` | ppt: rain+snow | mm/s |
| `ASA` | all-sky albedo:FSR/FSDS | proportion |
| `RNET` | net radiation:fsa-fira | W/m^2 |
| `LHEAT` | latent heat:FCTR+FCEV+FGEV | W/m^2 |
| `TOTRUNOFF` | Total Liquid Runoff | mm/s |
| `SNOWDP` | snow height | m |
| `FPSN` | photosynthesis | umol/m^2/s |
| `FSH` | sensible heat | W/m^2 |
| `FSH_V` | sensible heat from vegetation | W/m^2 |
| `FSH_G` | sensible heat from ground | W/m^2 |
| `FSH_TO_COUPLER` | sensible heat sent to coupler | W/m^2 |
| `FSH_PRECIP_CONVERSION` | SHF from conv of rain/snow atm forcing | W/m^2 |
| `FSH_RUNOFF_ICE_TO_LIQ` | SHF from conv of ice runoff to liquid | W/m^2 |
| `CPL_ENERGY_BAL` | Coupler Energy Balance (Global Area) | W/m2 |
| `TV` | vegetation temperature | K |
| `TG` | ground temperature | K |
| `FSA` | absorbed solar radiation | W/m^2 |
| `SABV` | solar rad absorbed by vegetation | W/m^2 |
| `SABG` | solar rad absorbed by ground | W/m^2 |
| `FSR` | reflected solar radiation | W/m^2 |
| `FIRA` | net infrared (longwave) radiation | W/m^2 |
| `FIRE` | emitted infrared (longwave) radiation | W/m^2 |
| `FCTR` | canopy transpiration | W/m^2 |
| `FCEV` | canopy evaporation | W/m^2 |
| `FGEV` | ground evaporation | W/m^2 |
| `FGR` | heat flux into snow/soil (includes snow melt) | W/m^2 |
| `FSM` | snow melt heat flux | W/m^2 |
| `FGNET` | net ground heat flux:fgr-fsm | W/m^2 |
| `TAUX` | zonal surface stress | kg/m/s^2 |
| `TAUY` | meridional surface stress | kg/m/s^2 |
| `ELAI` | exposed one-sided leaf area index | m2/m2 |
| `ESAI` | exposed one-sided stem area index | m2/m2 |
| `TLAI` | total one-sided leaf area index | m2/m2 |
| `TSAI` | total one-sided stem area index | m2/m2 |
| `LAISUN` | Sunlit Projected Leaf Area Index | m2/m2 |
| `LAISHA` | Shaded Projected Leaf Area Index | m^2/m^2 |
| `BTRAN` | transpiration beta factor | unitless |
| `H2OSNO` | total snow water equiv (SNOWICE + SNOWLIQ) | mm |
| `H2OCAN` | intercepted water | mm |
| `SNOWLIQ` | snow liquid water | kg/m^2 |
| `SNOWICE` | snow ice | kg/m^2 |
| `QINFL` | infiltration | mm/s |
| `QOVER` | surface runoff | mm/s |
| `QRGWL` | surface runoff at glaciers (liquid only), wetlands, lakes | mm/s |
| `QDRAI` | sub-surface drainage | mm/s |
| `QINTR` | interception | mm/s |
| `QDRIP` | throughfall | mm/s |
| `QSNOMELT` | snow melt | mm/s |
| `QSOIL` | ground evaporation | mm/s |
| `QVEGE` | canopy evaporation | mm/s |
| `QVEGT` | canopy transpiration | mm/s |
| `ERRSOI` | soil/lake energy conservation error | W/m^2 |
| `ERRSEB` | surface energy conservation error | W/m^2 |
| `FSNO` | fraction of ground covered by snow | unitless |
| `ERRSOL` | solar radiation conservation error | W/m^2 |
| `ERRH2O` | total water conservation error | mm |
| `RAIN` | atmospheric rain | mm/s |
| `SNOW` | atmospheric snow | mm/s |
| `TBOT` | atmospheric air temperature | K |
| `TLAKE` | lake temperature | K |
| `WIND` | atmospheric wind velocity magnitude | m/s |
| `THBOT` | atmospheric air potential temperature | K |
| `QBOT` | atmospheric specific humidity | kg/kg |
| `ZBOT` | atmospheric reference height | m |
| `FLDS` | atmospheric longwave radiation | W/m^2 |
| `FSDS` | atmospheric incident solar radiation | W/m^2 |
| `FSDSND` | direct nir incident solar radiation | W/m^2 |
| `FSDSNDLN` | direct nir incident solar radiation at local noon | W/m^2 |
| `FSDSNI` | diffuse nir incident solar radiation | W/m^2 |
| `FSDSVD` | direct vis incident solar radiation | W/m^2 |
| `FSDSVDLN` | direct vis incident solar radiation at local noon | W/m^2 |
| `FSDSVI` | diffuse vis incident solar radiation | W/m^2 |
| `FSRND` | direct nir reflected solar radiation | W/m^2 |
| `FSRNDLN` | direct nir reflected solar radiation at local noon | W/m^2 |
| `FSRNI` | diffuse nir reflected solar radiation | W/m^2 |
| `FSRVD` | direct vis reflected solar radiation | W/m^2 |
| `FSRVDLN` | direct vis reflected solar radiation at local noon | W/m^2 |
| `FSRVI` | diffuse vis reflected solar radiation | W/m^2 |
| `Q2M` | 2m specific humidity | kg/kg |
| `RH2M` | 2m relative humidity | % |
| `TREFMNAV` | daily minimum of average 2m temperature | K |
| `TREFMXAV` | daily maximum of average 2m temperature | K |
| `VBSA` | visible black-sky albedo | proportion |
| `NBSA` | near-IR black-sky albedo | proportion |
| `VWSA` | visible white-sky albedo | proportion |
| `NWSA` | near-IR white-sky albedo | proportion |
| `SOILLIQ` | soil liquid water | kg/m^2 |
| `SOILICE` | soil ice | kg/m^2 |
| `H2OSOI` | volumetric soil water | mm3/mm3 |
| `TSOI` | soil temperature | K |
| `EVAPFRAC` | LHEAT/(LHEAT+FSH) | unitless |
| `XIM` | moisture index | +/-1 |
| `P-E` | PREC-ET | mm/s |
| `WA` | water in the unconfined aquifer | mm |
| `ZWT` | water table depth | m |
| `TWS` | total water storage | mm |
| `VOLR` | river channel total water storage | m3 |
| `QCHARGE` | aquifer recharge rate | mm/s |
| `FCOV` | fractional area with water table at surface | unitless [0-1] |
| `PCO2` | partial pressure of CO2 | Pa |
| `DSTDEP` | total dust deposition (dry+wet) from atmosphere | kg/m2/s |
| `DSTFLXT` | total surface dust emission | kg/m2/s |
| `OCDEP` | total OC deposition (dry+wet) from atmosphere | kg/m2/s |
| `BCDEP` | total BC deposition (dry+wet) from atmosphere | kg/m2/s |
| `U10` | 10-m wind | m/s |
| `PCT_BSOIL_PFT` | Percent Bare Soil on Natural Veg Landunit | % |
| `PCT_TREE_PFT` | Percent Tree on Natural Veg Landunit | % |
| `PCT_GRASS_PFT` | Percent Grass on Natural Veg Landunit | % |
| `PCT_SHRUB_PFT` | Percent Shrub on Natural Veg Landunit | % |
| `PCT_CROP_PFT` | Percent Crop on Natural Veg Landunit or Gridcell (CropModel) | % |
| `ZETA` | dimensionless stability parameter | unitless |
| `RAIN_FROM_ATM` | atmospheric rain (pre-downscaling) | mm/s |
| `SNOW_FROM_ATM` | atmospheric snow (pre-downscaling) | mm/s |
| `FLDS_NOT_DOWNSCALED` | atmospheric longwave radiation (pre-downscaling) | W/m^2 |
| `Tair_from_atm` | atmospheric air temperature (pre-downscaling) | K |
| `Thair_from_atm` | atmospheric air potential temperature (pre-downscaling) | K |
| `QBOT_NOT_DOWNSCALED` | atmospheric specific humidity (pre-downscaling) | kg/kg |
| `PBOT_NOT_DOWNSCALED` | atm pressure of bottom layer (pre-downscaling) | Pa |
| `Rho_from_atm` | atmospheric density of bottom layer (pre-downscaling) | kg/m3 |
| `UWIND` | atmospheric uwind velocity magnitude | m/s |
| `VWIND` | atmospheric vwind velocity magnitude | m/s |
| `BCPHIDRY` | BC deposition (phidry) from atmosphere | kg/m2/s |
| `BCPHODRY` | BC deposition (phodry) from atmosphere | kg/m2/s |
| `BCPHIWET` | BC deposition (phiwet) from atmosphere | kg/m2/s |
| `OCPHIDRY` | OC deposition (phidry) from atmosphere | kg/m2/s |
| `OCPHODRY` | OC deposition (phodry) from atmosphere | kg/m2/s |
| `OCPHIWET` | OC deposition (phiwet) from atmosphere | kg/m2/s |
| `DSTWET1` | dust deposition (wet1) from atmosphere | kg/m2/s |
| `DSTDRY1` | dust deposition (dry1) from atmosphere | kg/m2/s |
| `DSTWET2` | dust deposition (wet2) from atmosphere | kg/m2/s |
| `DSTDRY2` | dust deposition (dry2) from atmosphere | kg/m2/s |
| `DSTWET3` | dust deposition (wet3) from atmosphere | kg/m2/s |
| `DSTDRY3` | dust deposition (dry3) from atmosphere | kg/m2/s |
| `DSTWET4` | dust deposition (wet4) from atmosphere | kg/m2/s |
| `DSTDRY4` | dust deposition (dry4) from atmosphere | kg/m2/s |
| `ATM_TOPO` | atmospheric surface height | m |

**CN/CLAMP** (34)

| 변수 | 설명 | 단위 |
|---|---|---|
| `AGNPP` | above ground net primary production | gC/m^2/s |
| `AR` | autotrophic respiration (MR + GR) | gC/m^2/s |
| `BGNPP` | below ground net primary production | gC/m^2/s |
| `BIOGENIC_CO` | Biogenic CO Flux | uG/m2/h |
| `CWDC` | coarse woody debris carbon | gC/m^2 |
| `CWDC_HR` | Coarse Woody Debris C Hetereotrophic respiration | gC/m2s |
| `CWDC_LOSS` | Coarse Woody Debris C Loss | gC/m2s |
| `FROOTC` | fine root carbon | gC/m^2 |
| `FROOTC_ALLOC` | Fine root C allocation | gC/m2s |
| `FROOTC_LOSS` | Fine root C Loss | gC/m2s |
| `GPP` | gross primary production | gC/m^2/s |
| `GROSS_NMIN` | gross N mineralization | gN/m^2/s |
| `HR` | total hetereotrophic respiration | gC/m^2/s |
| `ISOPRENE` | Isoprene Flux | uG/m2/h |
| `LEAFC` | leaf carbon | gC/m^2 |
| `LEAFC_ALLOC` | Leaf C Allocation | gC/m2s |
| `LEAFC_LOSS` | Leaf C Loss | gC/m2s |
| `LITTERC` | Total Litter C | gC/m2 |
| `LITTERC_HR` | Litter Hetereotrophic Respiration | gC/m2s |
| `LITTERC_LOSS` | Litter C Loss | gC/m2s |
| `MONOTERPENE` | Monoterpene Flux | uG/m2/h |
| `NEE` | net ecosys exchange of C | gC/m^2/s |
| `NEP` | net ecosystem production | gC/m^2/s |
| `NET_NMIN` | net N mineralization | gN/m^2/s |
| `NPP` | net primary production | gC/m^2/s |
| `OTHER_VOC` | Other VOC Flux | uG/m2/h |
| `OR_VOC` | Other Reactive VOC Flux | uG/m2/h |
| `SOILC` | soil organic matter C (fast pool) | gC/m2 |
| `SOILC_HR` | Soil C hetereotrophic respiration | gC/m2s |
| `SOILC_LOSS` | Soil C Loss | gC/m2s |
| `VOCFLXT` | Total VOC flux into Atmosphere | uG/m2/h |
| `WOODC` | Live+Dead Stem C | gC/m2 |
| `WOODC_ALLOC` | Wood C Allocation | gC/m2s |
| `WOODC_LOSS` | Wood C Loss | gC/m2s |

**CN (carbon-nitrogen)** (118)

| 변수 | 설명 | 단위 |
|---|---|---|
| `NEE` | net ecosys exchange of C | gC/m^2/s |
| `NEP` | net ecosystem production | gC/m^2/s |
| `NBP` | net biome production, includes fire, landuse and harvest flux | gC/m^2/s |
| `GPP` | gross primary production | gC/m^2/s |
| `HTOP` | canopy top height | m |
| `CUE` | carbon use efficiency | NPP/GPP |
| `BTRAN2` | root zone soil moisture factor | unitless |
| `PSNSUN_TO_CPOOL` | GPP from Sunlit Canopy | gC/m^2/s |
| `PSNSHADE_TO_CPOOL` | GPP from Shaded Canopy | gC/m^2/s |
| `NPP` | net primary production | gC/m^2/s |
| `AGNPP` | above ground net primary production | gC/m^2/s |
| `BGNPP` | below ground net primary production | gC/m^2/s |
| `MR` | maintenance respiration | gC/m^2/s |
| `GR` | total growth respiration | gC/m^2/s |
| `GRAINC` | grain C (does not equal yield) | gC/m^2 |
| `GRAINC_TO_FOOD` | grain C to food | gC/m^2/s |
| `GRAINC_TO_SEED` | grain C to seed | gC/m^2/s |
| `AR` | autotrophic respiration (MR + GR) | gC/m^2/s |
| `LITHR` | litter hetereotrophic respiration | gC/m^2/s |
| `SOMHR` | SOM hetereotrophic respiration | gC/m^2/s |
| `HR` | total hetereotrophic respiration | gC/m^2/s |
| `RR` | root respiration (fine root MR + total root GR) | gC/m^2/s |
| `SR` | total soil respiration (HR + root resp) | gC/m^2/s |
| `ER` | total ecosystem respiration (AR + HR) | gC/m^2/s |
| `FINUNDATED` | Fractional inundated of veg col | unitless |
| `FCH4` | Gridcell surface CH4 flux | kgC/m^2/s |
| `FCH4TOCO2` | Gridcell oxidation of CH4 to CO2 | gC/m^2/s |
| `FCH4_DFSAT` | CH4 additional flux | kgC/m^2/s |
| `CH4PROD` | Gridcell total CH4 production | gC/m^2/s |
| `CH4_SURF_AERE_SAT` | aerenchyma sfc CH4 flx-inundated area | mol/m^2/s |
| `CH4_SURF_AERE_UNSAT` | aerenchyma sfc CH4 flx-non-inundated area | mol/m^2/s |
| `CH4_SURF_DIFF_SAT` | diffusive sfc CH4 flx-inundated/lake area | mol/m^2/s |
| `CH4_SURF_DIFF_UNSAT` | diffusive sfc CH4 flx-non-inundated area | mol/m^2/s |
| `CH4_SURF_EBUL_SAT` | ebullition sfc CH4 flx-inundated/lake area | mol/m^2/s |
| `CH4_SURF_EBUL_UNSAT` | ebullition sfc CH4 flx-non-inundated area | mol/m^2/s |
| `LEAFC` | leaf carbon | gC/m^2 |
| `LEAFN` | leaf nitrogen | gN/m^2 |
| `LEAFCN` | leaf carbon/nitrogen | gC/gN |
| `FROOTC` | fine root carbon | gC/m^2 |
| `LIVESTEMC` | live stem C | gC/m^2 |
| `DEADSTEMC` | dead stem carbon | gC/m^2 |
| `LIVECROOTC` | live coarse root carbon | gC/m^2 |
| `DEADCROOTC` | dead coarse root carbon | gC/m^2 |
| `CPOOL` | temporary photosynthate C pool | gC/m^2 |
| `SOIL3C` | Soil organic matter C (slow pool) | gC/m^2 |
| `SOIL4C` | Soil organic matter C (slowest pool) | gC/m^2 |
| `XSMRPOOL` | Temporary Photosynthate C Pool | gC/m^2 |
| `TOTVEGC` | total vegetation C, excluding cpool | gC/m^2 |
| `TOTVEGN` | total vegetation N | gN/m^2 |
| `TOTVEGCN` | total vegetation C/N | gC/gN |
| `CWDC` | coarse woody debris carbon | gC/m^2 |
| `CWD_C` | coarse woody debris carbon | gC/m^2 |
| `TOTLITC` | total litter carbon | gC/m^2 |
| `TOTLITC_1m` | total litter carbon to 1m depth | gC/m^2 |
| `TOTSOMC` | total SOM carbon | gC/m^2 |
| `TOTSOMC_1m` | total SOM carbon to 1 meter depth | gC/m^2 |
| `TOTLITN` | total litter N | gN/m^2 |
| `TOTLITN_1m` | total litter N to 1m depth | gN/m^2 |
| `TOTSOMN` | total soil organic matter N | gN/m^2 |
| `TOTSOMN_1m` | total soil organic matter N to 1m depth | gN/m^2 |
| `TOTECOSYSC` | total ecosystem C, incl veg but excl cpool | gC/m^2 |
| `TOTCOLC` | total column C, incl veg and cpool | gC/m^2 |
| `FPG` | fraction of potential GPP | proportion |
| `FPI` | fraction of potential immobilization | proportion |
| `NDEP_TO_SMINN` | nitrogen deposition | gN/m^2/s |
| `FERT` | fertilizer added | gN/m^2/s |
| `FERT_TO_SMINN` | fertilizer to soil mineral N | gN/m^2/s |
| `NFERTILIZATION` | fertilizer added | gN/m^2/s |
| `POTENTIAL_IMMOB` | Potential Immobilization | gN/m^2/s |
| `ACTUAL_IMMOB` | Actual Immobilization | gN/m^2/s |
| `GROSS_NMIN` | gross N mineralization | gN/m^2/s |
| `NET_NMIN` | net N mineralization | gN/m^2/s |
| `NDEPLOY` | total N deployed in new growth | gN/m^2/s |
| `RETRANSN_TO_NPOOL` | Retranslocated N to NPool | gN/m^2/s |
| `SMINN_TO_NPOOL` | Mineral N to NPool | gN/m^2/s |
| `DENIT` | Total Denitrification | gN/m^2/s |
| `SOIL3N` | soil organic matter N (slow pool) | gN/m^2 |
| `SOIL4N` | Soil organic matter N (slowest pool) | gN/m^2 |
| `NFIX_TO_SMINN` | nitrogen fixation | gN/m^2/s |
| `NAM` | AM-associated N uptake flux | gN/m^2/s |
| `NECM` | ECM-associated N uptake flux | gN/m^2/s |
| `NFIX` | Symbiotic BNF uptake flux | gN/m^2/s |
| `NRETRANS` | Retranslocated N uptake flux | gN/m^2/s |
| `NPP_NUPTAKE` | total carbon used by N uptake in FUN | gC/m^2/s |
| `NUPTAKE_FRACTION` | NPP_NUPTAKE/(NPP_NUPTAKE+NPP) | unitless |
| `FFIX_TO_SMINN` | free living N fixation to soil mineral N | gN/m^2/s |
| `NPP_NFIX` | Symbiotic BNF uptake used C | gC/m^2/s |
| `NPP_NACTIVE` | Mycorrhizal N uptake used C | gC/m^2/s |
| `NPP_NRETRANS` | retranslocated N uptake flux | gC/m^2/s |
| `SUPPLEMENT_TO_SMINN` | supplement to mineral nitrogen | gN/m^2/s |
| `SMINN_LEACHED` | Nitrogen Leached | gN/m^2/s |
| `SMIN_NO3_LEACHED` | Soil NO3 pool loss to leaching | gN/m^2/s |
| `SMIN_NO3_RUNOFF` | Soil NO3 pool loss to runoff | gN/m^2/s |
| `SMINN` | soil mineral N | gN/m^2 |
| `RETRANSN` | plant pool of retranslocated N | gN/m^2 |
| `COL_FIRE_CLOSS` | total column-level fire C loss | gC/m^2/s |
| `PFT_FIRE_CLOSS` | total pft-level fire C loss | gC/m^2/s |
| `COL_FIRE_NLOSS` | total column-level fire N loss | gN/m^2/s |
| `PFT_FIRE_NLOSS` | total pft-level fire N loss | gN/m^2/s |
| `FAREA_BURNED` | fractional area burned | proportion/s |
| `BAF_CROP` | fractional area burned - crop | proportion/s |
| `CWDC_HR` | Coarse Woody Debris C Hetereotrophic respiration | gC/m2s |
| `CWDC_LOSS` | Coarse Woody Debris C Loss | gC/m2s |
| `FROOTC_ALLOC` | Fine root C allocation | gC/m2s |
| `FROOTC_LOSS` | Fine root C Loss | gC/m2s |
| `LEAFC_ALLOC` | Leaf C Allocation | gC/m2s |
| `LEAFC_LOSS` | Leaf C Loss | gC/m2s |
| `LITTERC` | Total Litter C | gC/m2 |
| `LITTERC_HR` | Litter Hetereotrophic Respiration | gC/m2s |
| `LITTERC_LOSS` | Litter C Loss | gC/m2s |
| `SOILC` | soil organic matter C (fast pool) | gC/m2 |
| `SOILC_HR` | Soil C hetereotrophic respiration | gC/m2s |
| `SOILC_LOSS` | Soil C Loss | gC/m2s |
| `WOODC` | Live+Dead Stem C | gC/m2 |
| `WOODC_ALLOC` | Wood C Allocation | gC/m2s |
| `WOODC_LOSS` | Wood C Loss | gC/m2s |
| `ALTMAX` | maximum annual active layer thickness | m |
| `LNFM` | lightning frequency | counts/km^2/hr |

## set3 — Monthly climatology, regional (air T, precip, runoff, snow depth, radiative+turbulent fluxes)

**Albedo** (5)

| 변수 | 설명 | 단위 |
|---|---|---|
| `VBSA` | visible black-sky albedo | proportion |
| `NBSA` | near-IR black-sky albedo | proportion |
| `VWSA` | visible white-sky albedo | proportion |
| `NWSA` | near-IR white-sky albedo | proportion |
| `ASA` | all-sky albedo:FSR/FSDS | proportion |

**CLAMP fluxes** (6)

| 변수 | 설명 | 단위 |
|---|---|---|
| `NEE` | net ecosys exchange of C | gC/m^2/s |
| `GPP` | gross primary production | gC/m^2/s |
| `NPP` | net primary production | gC/m^2/s |
| `AR` | autotrophic respiration (MR + GR) | gC/m^2/s |
| `HR` | total hetereotrophic respiration | gC/m^2/s |
| `NEP` | net ecosystem production | gC/m^2/s |

**C/N fluxes** (10)

| 변수 | 설명 | 단위 |
|---|---|---|
| `NEE` | net ecosys exchange of C | gC/m^2/s |
| `GPP` | gross primary production | gC/m^2/s |
| `NPP` | net primary production | gC/m^2/s |
| `AR` | autotrophic respiration (MR + GR) | gC/m^2/s |
| `HR` | total hetereotrophic respiration | gC/m^2/s |
| `ER` | total ecosystem respiration (AR + HR) | gC/m^2/s |
| `FCH4` | Gridcell surface CH4 flux | kgC/m^2/s |
| `SMINN_LEACHED` | Nitrogen Leached | gN/m^2/s |
| `SMIN_NO3_LEACHED` | Soil NO3 pool loss to leaching | gN/m^2/s |
| `SMIN_NO3_RUNOFF` | Soil NO3 pool loss to runoff | gN/m^2/s |

**C/N land fluxes** (8)

| 변수 | 설명 | 단위 |
|---|---|---|
| `TSA` | 2m air temperature | K |
| `PREC` | ppt: rain+snow | mm/s |
| `TOTRUNOFF` | Total Liquid Runoff | mm/s |
| `SNOWDP` | snow height | m |
| `LHEAT` | latent heat:FCTR+FCEV+FGEV | W/m^2 |
| `GPP` | gross primary production | gC/m^2/s |
| `TLAI` | total one-sided leaf area index | m2/m2 |
| `TOTSOILLIQICE` | soil moisture storage (liq+ice) | kg/m^2 |

**Fire fluxes** (6)

| 변수 | 설명 | 단위 |
|---|---|---|
| `COL_FIRE_CLOSS` | total column-level fire C loss | gC/m^2/s |
| `COL_FIRE_NLOSS` | total column-level fire N loss | gN/m^2/s |
| `PFT_FIRE_CLOSS` | total pft-level fire C loss | gC/m^2/s |
| `PFT_FIRE_NLOSS` | total pft-level fire N loss | gN/m^2/s |
| `FAREA_BURNED` | fractional area burned | proportion/s |
| `BAF_CROP` | fractional area burned - crop | proportion/s |

**Hydrology** (5)

| 변수 | 설명 | 단위 |
|---|---|---|
| `WA` | water in the unconfined aquifer | mm |
| `ZWT` | water table depth | m |
| `QCHARGE` | aquifer recharge rate | mm/s |
| `FCOV` | fractional area with water table at surface | unitless [0-1] |
| `TWS` | total water storage | mm |

**Land fluxes** (8)

| 변수 | 설명 | 단위 |
|---|---|---|
| `TSA` | 2m air temperature | K |
| `PREC` | ppt: rain+snow | mm/s |
| `TOTRUNOFF` | Total Liquid Runoff | mm/s |
| `SNOWDP` | snow height | m |
| `LHEAT` | latent heat:FCTR+FCEV+FGEV | W/m^2 |
| `FPSN` | photosynthesis | umol/m^2/s |
| `TLAI` | total one-sided leaf area index | m2/m2 |
| `TOTSOILLIQICE` | soil moisture storage (liq+ice) | kg/m^2 |

**Moisture+energy fluxes** (3)

| 변수 | 설명 | 단위 |
|---|---|---|
| `PREC` | ppt: rain+snow | mm/s |
| `RNET` | net radiation:fsa-fira | W/m^2 |
| `ET` | Evapotranspiration | mm/s |

**Radiative fluxes** (7)

| 변수 | 설명 | 단위 |
|---|---|---|
| `FSDS` | atmospheric incident solar radiation | W/m^2 |
| `ALBEDO` | all-sky albedo:FSR/FSDS | proportion |
| `FSA` | absorbed solar radiation | W/m^2 |
| `FLDS` | atmospheric longwave radiation | W/m^2 |
| `FIRE` | emitted infrared (longwave) radiation | W/m^2 |
| `FIRA` | net infrared (longwave) radiation | W/m^2 |
| `RNET` | net radiation:fsa-fira | W/m^2 |

**Snow** (3)

| 변수 | 설명 | 단위 |
|---|---|---|
| `SNOWDP` | snow height | m |
| `FSNO` | fraction of ground covered by snow | unitless |
| `H2OSNO` | total snow water equiv (SNOWICE + SNOWLIQ) | mm |

**Turbulent fluxes** (9)

| 변수 | 설명 | 단위 |
|---|---|---|
| `RNET` | net radiation:fsa-fira | W/m^2 |
| `FSH` | sensible heat | W/m^2 |
| `LHEAT` | latent heat:FCTR+FCEV+FGEV | W/m^2 |
| `FCTR` | canopy transpiration | W/m^2 |
| `FCEV` | canopy evaporation | W/m^2 |
| `FGEV` | ground evaporation | W/m^2 |
| `FGR` | heat flux into snow/soil (includes snow melt) | W/m^2 |
| `BTRAN` | transpiration beta factor | unitless |
| `EVAPFRAC` | LHEAT/(LHEAT+FSH) | unitless |

## set5 — Tables of annual means

**C13 isotope** (74)

| 변수 | 설명 | 단위 |
|---|---|---|
| `C13_NEE` | C13 Net Ecosys Exchange of C | gC/m^2/s |
| `C13_NBP` | C13 net biome production, includes fire, landuse and harvest flux | gC/m^2/s |
| `C13_NEP` | C13 Net Ecosystem Production | gC/m^2/s |
| `C13_GPP` | C13 Gross Primary Production | gC/m^2/s |
| `C13_PSNSUN_TO_CPOOL` | C13 GPP from Sunlit Canopy | gC/m^2/s |
| `C13_PSNSHADE_TO_CPOOL` | C13 GPP from Shaded Canopy | gC/m^2/s |
| `C13_NPP` | C13 Net Primary Production | gC/m^2/s |
| `C13_AGNPP` | C13 Aboveground NPP | gC/m^2/s |
| `C13_BGNPP` | C13 Belowground NPP | gC/m^2/s |
| `C13_MR` | C13 Maintenance Respiration | gC/m^2/s |
| `C13_GR` | C13 Total Growth Respiration | gC/m^2/s |
| `C13_AR` | C13 Autotrophic Respiration (MR + GR) | gC/m^2/s |
| `C13_LITHR` | C13 Litter Hetereotrophic Respiration | gC/m^2/s |
| `C13_SOMHR` | C13 SOM Hetereotrophic Respiration | gC/m^2/s |
| `C13_HR` | C13 Total Hetereotrophic Respiration | gC/m^2/s |
| `C13_RR` | C13 Root Respiration (Fine Root MR + Total Root GR) | gC/m^2/s |
| `C13_SR` | C13 Totl Soil Respiration (HR + Root Resp) | gC/m^2/s |
| `C13_ER` | C13 Totl Ecosystem Respiration (AR + HR) | gC/m^2/s |
| `C13_LEAFC` | C13 Leaf Carbon | gC/m^2 |
| `C13_SOIL3C` | C13 Soil Organic Matter C (Slow Pool) | gC/m^2 |
| `C13_SOIL4C` | C13 Soil Organic Matter C (Slowest Pool) | gC/m^2 |
| `C13_FROOTC` | C13 Fine Root CC | gC/m^2 |
| `C13_LIVESTEMC` | C13 Live Stem C | gC/m^2 |
| `C13_DEADSTEMC` | C13 Dead Stem Carbon | gC/m^2 |
| `C13_LIVECROOTC` | C13 Live Coarse Root Carbon | gC/m^2 |
| `C13_DEADCROOTC` | C13 Dead Coarse Root Carbon | gC/m^2 |
| `C13_CPOOL` | C13 Temporary Photosynthate C Pool | gC/m^2 |
| `C13_TOTVEGC` | C13 Total Vegetation C, Excluding Cpool | gC/m^2 |
| `C13_CWDC` | C13 Coarse Woody Debris Carbon | gC/m^2 |
| `C13_CWD_C` | C13 Coarse Woody Debris Carbon | gC/m^2 |
| `C13_TOTLITC` | C13 Totl Litter Carbon | gC/m^2 |
| `C13_TOTSOMC` | C13 Total SOM Carbon | gC/m^2 |
| `C13_TOTECOSYSC` | C13 Totl Ecosystem C, Incl Veg But Excl Cpool | gC/m^2 |
| `C13_COL_CTRUNC` | C13 Column-Level Sink for C Truncation | gC/m^2 |
| `C13_PFT_CTRUNC` | C13 Pft-Level Sink for C Truncation | gC/m^2 |
| `C13_COL_FIRE_CLOSS` | C13 Totl Col-Level Fire C Loss | gC/m^2/s |
| `C13_PFT_FIRE_CLOSS` | C13 Totl Pft-Level Fire C Loss | gC/m^2/s |
| `C14_NEE` | C14 Net Ecosys Exchange of C | gC/m^2/s |
| `C14_NBP` | C14 net biome production, includes fire, landuse and harvest flux | gC/m^2/s |
| `C14_NEP` | C14 Net Ecosystem Production | gC/m^2/s |
| `C14_GPP` | C14 Gross Primary Production | gC/m^2/s |
| `C14_PSNSUN_TO_CPOOL` | C14 GPP from Sunlit Canopy | gC/m^2/s |
| `C14_PSNSHADE_TO_CPOOL` | C14 GPP from Shaded Canopy | gC/m^2/s |
| `C14_NPP` | C14 Net Primary Production | gC/m^2/s |
| `C14_AGNPP` | C14 Aboveground NPP | gC/m^2/s |
| `C14_BGNPP` | C14 Belowground NPP | gC/m^2/s |
| `C14_MR` | C14 Maintenance Respiration | gC/m^2/s |
| `C14_GR` | C14 Total Growth Respiration | gC/m^2/s |
| `C14_AR` | C14 Autotrophic Respiration (MR + GR) | gC/m^2/s |
| `C14_LITHR` | C14 Litter Hetereotrophic Respiration | gC/m^2/s |
| `C14_SOMHR` | C14 SOM Hetereotrophic Respiration | gC/m^2/s |
| `C14_HR` | C14 Total Hetereotrophic Respiration | gC/m^2/s |
| `C14_RR` | C14 Root Respiration (Fine Root MR + Total Root GR) | gC/m^2/s |
| `C14_SR` | C14 Totl Soil Respiration (HR + Root Resp) | gC/m^2/s |
| `C14_ER` | C14 Totl Ecosystem Respiration (AR + HR) | gC/m^2/s |
| `C14_LEAFC` | C14 Leaf Carbon | gC/m^2 |
| `C14_SOIL3C` | C14 Soil Organic Matter C (Slow Pool) | gC/m^2 |
| `C14_SOIL4C` | C14 Soil Organic Matter C (Slowest Pool) | gC/m^2 |
| `C14_FROOTC` | C14 Fine Root CC | gC/m^2 |
| `C14_LIVESTEMC` | C14 Live Stem C | gC/m^2 |
| `C14_DEADSTEMC` | C14 Dead Stem Carbon | gC/m^2 |
| `C14_LIVECROOTC` | C14 Live Coarse Root Carbon | gC/m^2 |
| `C14_DEADCROOTC` | C14 Dead Coarse Root Carbon | gC/m^2 |
| `C14_CPOOL` | C14 Temporary Photosynthate C Pool | gC/m^2 |
| `C14_TOTVEGC` | C14 Total Vegetation C, Excluding Cpool | gC/m^2 |
| `C14_CWDC` | C14 Coarse Woody Debris Carbon | gC/m^2 |
| `C14_CWD_C` | C14 Coarse Woody Debris Carbon | gC/m^2 |
| `C14_TOTLITC` | C14 Totl Litter Carbon | gC/m^2 |
| `C14_TOTSOMC` | C14 Total SOM Carbon | gC/m^2 |
| `C14_TOTECOSYSC` | C14 Totl Ecosystem C, Incl Veg But Excl Cpool | gC/m^2 |
| `C14_COL_CTRUNC` | C14 Column-Level Sink for C Truncation | gC/m^2 |
| `C14_PFT_CTRUNC` | C14 Pft-Level Sink for C Truncation | gC/m^2 |
| `C14_COL_FIRE_CLOSS` | C14 Totl Col-Level Fire C Loss | gC/m^2/s |
| `C14_PFT_FIRE_CLOSS` | C14 Totl Pft-Level Fire C Loss | gC/m^2/s |

**CASA** (55)

| 변수 | 설명 | 단위 |
|---|---|---|
| `SURFMETC` | Total Metabolized Litter C | gC/m^2 |
| `SURFSTRC` | Total Structural Litter C | gC/m^2 |
| `SOILMETC` | Total Metabolized Structural Soil C | gC/m^2 |
| `SOILSTRC` | Total Structural Soil C | gC/m^2 |
| `SURFMIC` | Total Microbial Litter C | gC/m^2 |
| `SOILMIC` | Total Microbial Soil C | gC/m^2 |
| `SLOWC` | Total Slow C Pool | gC/m^2 |
| `PASSIVEC` | Total Passive C Pool | gC/m^2 |
| `RESP_LEAFC` | Respired Leaf C | gC/m^2 |
| `RESP_WOODC` | Respired Wood C | gC/m^2 |
| `RESP_FROOTC` | Respired Fine Root C | gC/m^2 |
| `RESP_SURFMETC` | Respired Metabolized Litter C | gC/m^2 |
| `RESP_SURFSTRC` | Respired Structural Litter C | gC/m^2 |
| `RESP_SOILMETC` | Respired Metabolized Soil C | gC/m^2 |
| `RESP_SOILSTRC` | Respired Structural Soil C | gC/m^2 |
| `RESP_CWDC` | Respired Coarse Woody Debris C | gC/m^2 |
| `RESP_SURFMIC` | Respired Microbial Litter C | gC/m^2 |
| `RESP_SOILMIC` | Respired Microbial Soil C | gC/m^2 |
| `RESP_SLOWC` | Respired Slow C Pool | gC/m^2 |
| `RESP_PASSIVEC` | Respired Passive C Pool | gC/m^2 |
| `CLOSS_LEAF` | Leaf C Loss | gC/m^2 |
| `CLOSS_WOOD` | Wood C Loss | gC/m^2 |
| `CLOSS_FROOT` | Fine Root C Loss | gC/m^2 |
| `CLOSS_SURFMET` | Metabolized Litter C Loss | gC/m^2 |
| `CLOSS_SURFSTR` | Structural Litter C Loss | gC/m^2 |
| `CLOSS_SOILMET` | Metabolized Structural Soil C Loss | gC/m^2 |
| `CLOSS_SOILSTR` | Structural Soil C Loss | gC/m^2 |
| `CLOSS_CWD` | Coarse Woody Debris C Loss | gC/m^2 |
| `CLOSS_SURFMIC` | Microbial Litter C Loss | gC/m^2 |
| `CLOSS_SOILMIC` | Microbial Soil C Loss | gC/m^2 |
| `CLOSS_SLOW` | Slow C Pool Loss | gC/m^2 |
| `CLOSS_PASSIVE` | Passive C Pool Loss | gC/m^2 |
| `CFLUX` | Total C Flux | gC/m^2/s |
| `CO2FLUX` | Net CO2 Flux | gC/m^2/s |
| `PET` | Potential ET | mm/s |
| `EXCESSC` | Excess C | gC/m^2/s |
| `PLAI` | Prognostic LAI | m^2/m^2 |
| `DEGDAY` | Accumulated Degree Days | C |
| `TDAYAVG` | Daily Averaged T | C |
| `STRESST` | Temperature stress fcn for leaf loss | unitless |
| `STRESSW` | Water stress fcn for leaf loss | unitless |
| `STRESSCD` | Cold+drought stress fcn for leaf loss | unitless |
| `LGROW` | Growing season index (0 or 1) | — |
| `ISEABEG` | Index for start of growing season | — |
| `NSTEPBEG` | Nstep at start of growing season | — |
| `BGTEMP` | Temperature Dependence | unitless |
| `XSCPOOL` | total excess C | g/m^2 |
| `WLIM` | water limitation used in bgmoist (atmp factor) | unitless |
| `SOILT` | Soil temperature: top 30cm | C |
| `SMOIST` | Soil moisture: top 30cm | mm3/mm3 |
| `WATOPT` | watopt for entire column | mm3/mm3 |
| `WATDRY` | watdry for entire column | mm3/mm3 |
| `LIVEFR_LEAFC` | Live Fraction Leaf C | gC/m^2 |
| `LIVEFR_WOODC` | Live Fraction Wood C | gC/m^2 |
| `LIVEFR_FROOTC` | Live Fraction Froot C | gC/m^2 |

**CLM/CLAMP** (52)

| 변수 | 설명 | 단위 |
|---|---|---|
| `GROUND` | heat flux into soil | W/m2 |
| `LATENT` | Latent Heat Flux | W/m2 |
| `SENSIBLE` | Sensible Heat Flux | W/m2 |
| `SENSIBLE_GND` | Sensible Heat Flux from Ground | W/m2 |
| `SENSIBLE_VEG` | Sensible Heat Flux from Vegetation | W/m2 |
| `REL_HUM` | Relative Humidity at 2m | kg/kg |
| `SPEC_HUM_2M` | Specific Humidity at 2m | kg/kg |
| `SPEC_HUM` | Atmospheric Specific Humidity | kg/kg |
| `RAIN` | atmospheric rain | mm/s |
| `SNOW` | atmospheric snow | mm/s |
| `BTRAN` | transpiration beta factor | unitless |
| `CANOPY_EVAPORATION` | Canopy Evaporation | mm/s |
| `DRAINAGE` | Subsurface Drainage | mm/s |
| `ET` | Evapotranspiration | mm/s |
| `INTERCEPTION` | Canopy Interception | mm/s |
| `RUNOFF` | Surface Runoff | mm/s |
| `SNOW_DEPTH` | Snow depth | mm |
| `SOIL_EVAPORATION` | Soil Evaporation | mm/s |
| `SOIL_ICE` | Soil Ice in each soil layer | kg/m2 |
| `SOIL_LIQUID` | Soil Liquid Water | kg/m2 |
| `SOIL_PSI` | Soil Water Potential | MPa |
| `TOTAL_SOIL_ICE` | Total soil ice | kg/m2 |
| `TOTAL_SOIL_LIQUID` | total soil liquid water | kg/m2 |
| `TRANSPIRATION` | Transpiration | mm/s |
| `VOL_SOIL_WATER` | Volumetric Soil Water | mm3/mm3 |
| `ALL_SKY_ALBEDO` | All-Sky Albedo | proportion |
| `BLACK_SKY_ALBEDO` | Surface Black-Sky Albedo | proportion |
| `IRDOWN` | Downward Infrared Radiation | W/m2 |
| `IRUP` | Upward Infrared Radiation | W/m2 |
| `LAISHA` | Shaded Projected Leaf Area Index | m^2/m^2 |
| `LAISUN` | Sunlit Projected Leaf Area Index | m2/m2 |
| `NETIR` | Net Infrared (longwave) Radiation | W/m2 |
| `NETRAD` | Net radiation | W/m2 |
| `REFLECT` | Total Reflected Solar Radiation | W/m2 |
| `SNOW_FRACTION` | Snow Fraction | unitless |
| `SOLAR` | Total Incident Solar Radiation | W/m2 |
| `SOLAR_AB` | Total Absorbed Solar Radiation | W/m2 |
| `SOLAR_ABG` | Solar Radiation Absorbed by Ground | W/m2 |
| `SOLAR_ABV` | Solar Rad Absorbed by Vegetation | W/m2 |
| `DEGREE_DAYS` | Accumulated degree days | K |
| `TREFMNAV` | daily minimum of average 2m temperature | K |
| `TREFMXAV` | daily maximum of average 2m temperature | K |
| `TSA2M` | 2m Air Temperature | K |
| `TSOIL` | soil temperature | K |
| `TVEG` | Vegetation Temperature | K |
| `ELAI` | exposed one-sided leaf area index | m2/m2 |
| `ESAI` | exposed one-sided stem area index | m2/m2 |
| `TLAI` | total one-sided leaf area index | m2/m2 |
| `TSAI` | total one-sided stem area index | m2/m2 |
| `PHOTOSYNTHESIS` | Photosynthesis | umol/m2s |
| `RSSHA` | shaded leaf stomatal resistance | s/m |
| `RSSUN` | Sunlit leaf stomatal resistance | s/m |

**CLM core** (48)

| 변수 | 설명 | 단위 |
|---|---|---|
| `TSA` | 2m air temperature | K |
| `PREC` | ppt: rain+snow | mm/s |
| `RAIN` | atmospheric rain | mm/s |
| `SNOW` | atmospheric snow | mm/s |
| `SNOWDP` | snow height | m |
| `FSNO` | fraction of ground covered by snow | unitless |
| `H2OSNO` | total snow water equiv (SNOWICE + SNOWLIQ) | mm |
| `VBSA` | visible black-sky albedo | proportion |
| `NBSA` | near-IR black-sky albedo | proportion |
| `VWSA` | visible white-sky albedo | proportion |
| `NWSA` | near-IR white-sky albedo | proportion |
| `RNET` | net radiation:fsa-fira | W/m^2 |
| `LHEAT` | latent heat:FCTR+FCEV+FGEV | W/m^2 |
| `FSH` | sensible heat | W/m^2 |
| `FSH_TO_COUPLER` | sensible heat sent to coupler | W/m^2 |
| `FSH_PRECIP_CONVERSION` | SHF from conv of rain/snow atm forcing | W/m^2 |
| `FSH_RUNOFF_ICE_TO_LIQ` | SHF from conv of ice runoff to liquid | W/m^2 |
| `CPL_ENERGY_BAL` | Coupler Energy Balance (Global Area) | W/m2 |
| `FSDS` | atmospheric incident solar radiation | W/m^2 |
| `FSA` | absorbed solar radiation | W/m^2 |
| `FLDS` | atmospheric longwave radiation | W/m^2 |
| `FIRE` | emitted infrared (longwave) radiation | W/m^2 |
| `FCTR` | canopy transpiration | W/m^2 |
| `FCEV` | canopy evaporation | W/m^2 |
| `FGEV` | ground evaporation | W/m^2 |
| `FGR` | heat flux into snow/soil (includes snow melt) | W/m^2 |
| `FSM` | snow melt heat flux | W/m^2 |
| `TLAI` | total one-sided leaf area index | m2/m2 |
| `TSAI` | total one-sided stem area index | m2/m2 |
| `LAISUN` | Sunlit Projected Leaf Area Index | m2/m2 |
| `LAISHA` | Shaded Projected Leaf Area Index | m^2/m^2 |
| `FPSN` | photosynthesis | umol/m^2/s |
| `ET` | Evapotranspiration | mm/s |
| `QOVER` | surface runoff | mm/s |
| `QIRRIG` | — | — |
| `QDRAI` | sub-surface drainage | mm/s |
| `QRGWL` | surface runoff at glaciers (liquid only), wetlands, lakes | mm/s |
| `WA` | water in the unconfined aquifer | mm |
| `ZWT` | water table depth | m |
| `TWS` | total water storage | mm |
| `VOLR` | river channel total water storage | m3 |
| `QCHARGE` | aquifer recharge rate | mm/s |
| `FCOV` | fractional area with water table at surface | unitless [0-1] |
| `CO2_PPMV` | CO2 concentration | ppmv |
| `DSTDEP` | total dust deposition (dry+wet) from atmosphere | kg/m2/s |
| `DSTFLXT` | total surface dust emission | kg/m2/s |
| `OCDEP` | total OC deposition (dry+wet) from atmosphere | kg/m2/s |
| `BCDEP` | total BC deposition (dry+wet) from atmosphere | kg/m2/s |

**CN/CLAMP** (34)

| 변수 | 설명 | 단위 |
|---|---|---|
| `AGNPP` | above ground net primary production | gC/m^2/s |
| `AR` | autotrophic respiration (MR + GR) | gC/m^2/s |
| `BGNPP` | below ground net primary production | gC/m^2/s |
| `BIOGENIC_CO` | Biogenic CO Flux | uG/m2/h |
| `CWDC` | coarse woody debris carbon | gC/m^2 |
| `CWDC_HR` | Coarse Woody Debris C Hetereotrophic respiration | gC/m2s |
| `CWDC_LOSS` | Coarse Woody Debris C Loss | gC/m2s |
| `FROOTC` | fine root carbon | gC/m^2 |
| `FROOTC_ALLOC` | Fine root C allocation | gC/m2s |
| `FROOTC_LOSS` | Fine root C Loss | gC/m2s |
| `GPP` | gross primary production | gC/m^2/s |
| `GROSS_NMIN` | gross N mineralization | gN/m^2/s |
| `HR` | total hetereotrophic respiration | gC/m^2/s |
| `ISOPRENE` | Isoprene Flux | uG/m2/h |
| `LEAFC` | leaf carbon | gC/m^2 |
| `LEAFC_ALLOC` | Leaf C Allocation | gC/m2s |
| `LEAFC_LOSS` | Leaf C Loss | gC/m2s |
| `LITTERC` | Total Litter C | gC/m2 |
| `LITTERC_HR` | Litter Hetereotrophic Respiration | gC/m2s |
| `LITTERC_LOSS` | Litter C Loss | gC/m2s |
| `MONOTERPENE` | Monoterpene Flux | uG/m2/h |
| `NEE` | net ecosys exchange of C | gC/m^2/s |
| `NEP` | net ecosystem production | gC/m^2/s |
| `NET_NMIN` | net N mineralization | gN/m^2/s |
| `NPP` | net primary production | gC/m^2/s |
| `OTHER_VOC` | Other VOC Flux | uG/m2/h |
| `OR_VOC` | Other Reactive VOC Flux | uG/m2/h |
| `SOILC` | soil organic matter C (fast pool) | gC/m2 |
| `SOILC_HR` | Soil C hetereotrophic respiration | gC/m2s |
| `SOILC_LOSS` | Soil C Loss | gC/m2s |
| `VOCFLXT` | Total VOC flux into Atmosphere | uG/m2/h |
| `WOODC` | Live+Dead Stem C | gC/m2 |
| `WOODC_ALLOC` | Wood C Allocation | gC/m2s |
| `WOODC_LOSS` | Wood C Loss | gC/m2s |

**CN (carbon-nitrogen)** (111)

| 변수 | 설명 | 단위 |
|---|---|---|
| `NEE` | net ecosys exchange of C | gC/m^2/s |
| `NEP` | net ecosystem production | gC/m^2/s |
| `NBP` | net biome production, includes fire, landuse and harvest flux | gC/m^2/s |
| `GPP` | gross primary production | gC/m^2/s |
| `CUE` | carbon use efficiency | NPP/GPP |
| `PSNSUN_TO_CPOOL` | GPP from Sunlit Canopy | gC/m^2/s |
| `PSNSHADE_TO_CPOOL` | GPP from Shaded Canopy | gC/m^2/s |
| `NPP` | net primary production | gC/m^2/s |
| `AGNPP` | above ground net primary production | gC/m^2/s |
| `BGNPP` | below ground net primary production | gC/m^2/s |
| `MR` | maintenance respiration | gC/m^2/s |
| `GR` | total growth respiration | gC/m^2/s |
| `AR` | autotrophic respiration (MR + GR) | gC/m^2/s |
| `LITHR` | litter hetereotrophic respiration | gC/m^2/s |
| `SOMHR` | SOM hetereotrophic respiration | gC/m^2/s |
| `HR` | total hetereotrophic respiration | gC/m^2/s |
| `RR` | root respiration (fine root MR + total root GR) | gC/m^2/s |
| `SR` | total soil respiration (HR + root resp) | gC/m^2/s |
| `ER` | total ecosystem respiration (AR + HR) | gC/m^2/s |
| `FINUNDATED` | Fractional inundated of veg col | unitless |
| `FCH4` | Gridcell surface CH4 flux | kgC/m^2/s |
| `FCH4TOCO2` | Gridcell oxidation of CH4 to CO2 | gC/m^2/s |
| `FCH4_DFSAT` | CH4 additional flux | kgC/m^2/s |
| `CH4PROD` | Gridcell total CH4 production | gC/m^2/s |
| `CH4_SURF_AERE_SAT` | aerenchyma sfc CH4 flx-inundated area | mol/m^2/s |
| `CH4_SURF_AERE_UNSAT` | aerenchyma sfc CH4 flx-non-inundated area | mol/m^2/s |
| `CH4_SURF_DIFF_SAT` | diffusive sfc CH4 flx-inundated/lake area | mol/m^2/s |
| `CH4_SURF_DIFF_UNSAT` | diffusive sfc CH4 flx-non-inundated area | mol/m^2/s |
| `CH4_SURF_EBUL_SAT` | ebullition sfc CH4 flx-inundated/lake area | mol/m^2/s |
| `CH4_SURF_EBUL_UNSAT` | ebullition sfc CH4 flx-non-inundated area | mol/m^2/s |
| `LEAFC` | leaf carbon | gC/m^2 |
| `XSMRPOOL` | Temporary Photosynthate C Pool | gC/m^2 |
| `SOIL3C` | Soil organic matter C (slow pool) | gC/m^2 |
| `SOIL4C` | Soil organic matter C (slowest pool) | gC/m^2 |
| `FROOTC` | fine root carbon | gC/m^2 |
| `LIVESTEMC` | live stem C | gC/m^2 |
| `DEADSTEMC` | dead stem carbon | gC/m^2 |
| `LIVECROOTC` | live coarse root carbon | gC/m^2 |
| `DEADCROOTC` | dead coarse root carbon | gC/m^2 |
| `CPOOL` | temporary photosynthate C pool | gC/m^2 |
| `TOTVEGC` | total vegetation C, excluding cpool | gC/m^2 |
| `CWDC` | coarse woody debris carbon | gC/m^2 |
| `CWD_C` | coarse woody debris carbon | gC/m^2 |
| `TOTLITC` | total litter carbon | gC/m^2 |
| `TOTLITC_1m` | total litter carbon to 1m depth | gC/m^2 |
| `TOTSOMC` | total SOM carbon | gC/m^2 |
| `TOTSOMC_1m` | total SOM carbon to 1 meter depth | gC/m^2 |
| `TOTLITN` | total litter N | gN/m^2 |
| `TOTLITN_1m` | total litter N to 1m depth | gN/m^2 |
| `TOTSOMN` | total soil organic matter N | gN/m^2 |
| `TOTSOMN_1m` | total soil organic matter N to 1m depth | gN/m^2 |
| `TOTECOSYSC` | total ecosystem C, incl veg but excl cpool | gC/m^2 |
| `TOTCOLC` | total column C, incl veg and cpool | gC/m^2 |
| `FPG` | fraction of potential GPP | proportion |
| `FPI` | fraction of potential immobilization | proportion |
| `NDEP_TO_SMINN` | nitrogen deposition | gN/m^2/s |
| `FERT` | fertilizer added | gN/m^2/s |
| `FERT_TO_SMINN` | fertilizer to soil mineral N | gN/m^2/s |
| `NFERTILIZATION` | fertilizer added | gN/m^2/s |
| `POTENTIAL_IMMOB` | Potential Immobilization | gN/m^2/s |
| `ACTUAL_IMMOB` | Actual Immobilization | gN/m^2/s |
| `GROSS_NMIN` | gross N mineralization | gN/m^2/s |
| `NET_NMIN` | net N mineralization | gN/m^2/s |
| `NDEPLOY` | total N deployed in new growth | gN/m^2/s |
| `RETRANSN_TO_NPOOL` | Retranslocated N to NPool | gN/m^2/s |
| `SMINN_TO_NPOOL` | Mineral N to NPool | gN/m^2/s |
| `DENIT` | Total Denitrification | gN/m^2/s |
| `SOIL3N` | soil organic matter N (slow pool) | gN/m^2 |
| `SOIL4N` | Soil organic matter N (slowest pool) | gN/m^2 |
| `NFIX_TO_SMINN` | nitrogen fixation | gN/m^2/s |
| `NAM` | AM-associated N uptake flux | gN/m^2/s |
| `NECM` | ECM-associated N uptake flux | gN/m^2/s |
| `NFIX` | Symbiotic BNF uptake flux | gN/m^2/s |
| `NRETRANS` | Retranslocated N uptake flux | gN/m^2/s |
| `NPP_NUPTAKE` | total carbon used by N uptake in FUN | gC/m^2/s |
| `NUPTAKE_FRACTION` | NPP_NUPTAKE/(NPP_NUPTAKE+NPP) | unitless |
| `FFIX_TO_SMINN` | free living N fixation to soil mineral N | gN/m^2/s |
| `NPP_NFIX` | Symbiotic BNF uptake used C | gC/m^2/s |
| `NPP_NACTIVE` | Mycorrhizal N uptake used C | gC/m^2/s |
| `NPP_NRETRANS` | retranslocated N uptake flux | gC/m^2/s |
| `SUPPLEMENT_TO_SMINN` | supplement to mineral nitrogen | gN/m^2/s |
| `SMINN_LEACHED` | Nitrogen Leached | gN/m^2/s |
| `SMIN_NO3_LEACHED` | Soil NO3 pool loss to leaching | gN/m^2/s |
| `SMIN_NO3_RUNOFF` | Soil NO3 pool loss to runoff | gN/m^2/s |
| `SMINN` | soil mineral N | gN/m^2 |
| `RETRANSN` | plant pool of retranslocated N | gN/m^2 |
| `COL_CTRUNC` | column-level sink for C truncation | gC/m^2 |
| `PFT_CTRUNC` | pft-level sink for C truncation | gC/m^2 |
| `COL_NTRUNC` | column-level sink for N truncation | gN/m^2 |
| `PFT_NTRUNC` | pft-level sink for N truncation | gN/m^2 |
| `COL_FIRE_CLOSS` | total column-level fire C loss | gC/m^2/s |
| `PFT_FIRE_CLOSS` | total pft-level fire C loss | gC/m^2/s |
| `COL_FIRE_NLOSS` | total column-level fire N loss | gN/m^2/s |
| `PFT_FIRE_NLOSS` | total pft-level fire N loss | gN/m^2/s |
| `FAREA_BURNED` | fractional area burned | proportion/s |
| `BAF_CROP` | fractional area burned - crop | proportion/s |
| `CWDC_HR` | Coarse Woody Debris C Hetereotrophic respiration | gC/m2s |
| `CWDC_LOSS` | Coarse Woody Debris C Loss | gC/m2s |
| `FROOTC_ALLOC` | Fine root C allocation | gC/m2s |
| `FROOTC_LOSS` | Fine root C Loss | gC/m2s |
| `LEAFC_ALLOC` | Leaf C Allocation | gC/m2s |
| `LEAFC_LOSS` | Leaf C Loss | gC/m2s |
| `LITTERC` | Total Litter C | gC/m2 |
| `LITTERC_HR` | Litter Hetereotrophic Respiration | gC/m2s |
| `LITTERC_LOSS` | Litter C Loss | gC/m2s |
| `SOILC` | soil organic matter C (fast pool) | gC/m2 |
| `SOILC_HR` | Soil C hetereotrophic respiration | gC/m2s |
| `SOILC_LOSS` | Soil C Loss | gC/m2s |
| `WOODC` | Live+Dead Stem C | gC/m2 |
| `WOODC_ALLOC` | Wood C Allocation | gC/m2s |
| `WOODC_LOSS` | Wood C Loss | gC/m2s |

**Hydrology (regional)** (6)

| 변수 | 설명 | 단위 |
|---|---|---|
| `PREC` | ppt: rain+snow | mm/s |
| `QVEGE` | canopy evaporation | mm/s |
| `QVEGEP` | canopy evap:QVEGE/(RAIN+SNOW)*100 | % |
| `QVEGT` | canopy transpiration | mm/s |
| `QSOIL` | ground evaporation | mm/s |
| `TOTRUNOFF` | Total Liquid Runoff | mm/s |

## set6 — Regional annual trends

**Carbon stocks** (8)

| 변수 | 설명 | 단위 |
|---|---|---|
| `TOTECOSYSC` | total ecosystem C, incl veg but excl cpool | gC/m^2 |
| `TOTSOMC_1m` | total SOM carbon to 1 meter depth | gC/m^2 |
| `TOTVEGC` | total vegetation C, excluding cpool | gC/m^2 |
| `TOTLITC_1m` | total litter carbon to 1m depth | gC/m^2 |
| `CWDC` | coarse woody debris carbon | gC/m^2 |
| `LAND_USE_FLUX` | total C emitted from land cover conversion and wood product pools | gC/m^2/s |
| `LEAFCN` | leaf carbon/nitrogen | gC/gN |
| `TOTVEGCN` | total vegetation C/N | gC/gN |

**CLAMP fluxes** (6)

| 변수 | 설명 | 단위 |
|---|---|---|
| `NEE` | net ecosys exchange of C | gC/m^2/s |
| `GPP` | gross primary production | gC/m^2/s |
| `NPP` | net primary production | gC/m^2/s |
| `AR` | autotrophic respiration (MR + GR) | gC/m^2/s |
| `HR` | total hetereotrophic respiration | gC/m^2/s |
| `NEP` | net ecosystem production | gC/m^2/s |

**C/N fluxes** (10)

| 변수 | 설명 | 단위 |
|---|---|---|
| `NEE` | net ecosys exchange of C | gC/m^2/s |
| `GPP` | gross primary production | gC/m^2/s |
| `NPP` | net primary production | gC/m^2/s |
| `AR` | autotrophic respiration (MR + GR) | gC/m^2/s |
| `HR` | total hetereotrophic respiration | gC/m^2/s |
| `ER` | total ecosystem respiration (AR + HR) | gC/m^2/s |
| `FCH4` | Gridcell surface CH4 flux | kgC/m^2/s |
| `CUE` | carbon use efficiency | NPP/GPP |
| `SMIN_NO3_LEACHED` | Soil NO3 pool loss to leaching | gN/m^2/s |
| `NUPTAKE_FRACTION` | NPP_NUPTAKE/(NPP_NUPTAKE+NPP) | unitless |

**Fire fluxes** (6)

| 변수 | 설명 | 단위 |
|---|---|---|
| `COL_FIRE_CLOSS` | total column-level fire C loss | gC/m^2/s |
| `COL_FIRE_NLOSS` | total column-level fire N loss | gN/m^2/s |
| `PFT_FIRE_CLOSS` | total pft-level fire C loss | gC/m^2/s |
| `PFT_FIRE_NLOSS` | total pft-level fire N loss | gN/m^2/s |
| `FAREA_BURNED` | fractional area burned | proportion/s |
| `BAF_CROP` | fractional area burned - crop | proportion/s |

**Hydrology** (6)

| 변수 | 설명 | 단위 |
|---|---|---|
| `WA` | water in the unconfined aquifer | mm |
| `ZWT` | water table depth | m |
| `QCHARGE` | aquifer recharge rate | mm/s |
| `FCOV` | fractional area with water table at surface | unitless [0-1] |
| `TWS` | total water storage | mm |
| `VOLR` | river channel total water storage | m3 |

**Land fluxes** (4)

| 변수 | 설명 | 단위 |
|---|---|---|
| `TSA` | 2m air temperature | K |
| `PREC` | ppt: rain+snow | mm/s |
| `TOTRUNOFF` | Total Liquid Runoff | mm/s |
| `SNOWDP` | snow height | m |

**Radiative fluxes** (8)

| 변수 | 설명 | 단위 |
|---|---|---|
| `FSDS` | atmospheric incident solar radiation | W/m^2 |
| `ALBEDO` | all-sky albedo:FSR/FSDS | proportion |
| `FSA` | absorbed solar radiation | W/m^2 |
| `FLDS` | atmospheric longwave radiation | W/m^2 |
| `FIRE` | emitted infrared (longwave) radiation | W/m^2 |
| `FIRA` | net infrared (longwave) radiation | W/m^2 |
| `RNET` | net radiation:fsa-fira | W/m^2 |
| `FSNO` | fraction of ground covered by snow | unitless |

**Turbulent fluxes** (9)

| 변수 | 설명 | 단위 |
|---|---|---|
| `RNET` | net radiation:fsa-fira | W/m^2 |
| `FSH` | sensible heat | W/m^2 |
| `LHEAT` | latent heat:FCTR+FCEV+FGEV | W/m^2 |
| `FCTR` | canopy transpiration | W/m^2 |
| `FCEV` | canopy evaporation | W/m^2 |
| `FGEV` | ground evaporation | W/m^2 |
| `FGR` | heat flux into snow/soil (includes snow melt) | W/m^2 |
| `BTRAN` | transpiration beta factor | unitless |
| `TLAI` | total one-sided leaf area index | m2/m2 |

## set8 — Ocean/Land/Atmosphere CO2 exchange; annual cycle / zonal / trends

**Annual cycle** (8)

| 변수 | 설명 | 단위 |
|---|---|---|
| `CO2` | CO2 concentration | kgCO2/kgDryAir |
| `CO2_LND` | CO2 Land-Atm Concentration | kgCO2/kgDryAir |
| `CO2_OCN` | CO2 Ocn-Atm Concentration | kgCO2/kgDryAir |
| `CO2_FFF` | CO2 Fossil Fuel Concentration | kgCO2/kgDryAir |
| `SFCO2` | CO2 Surface Flux | kgCO2/m2/s |
| `SFCO2_FFF` | CO2 Fossil Fuel Surface Flux | kgCO2/m2/s |
| `SFCO2_OCN` | CO2 Ocean Surface Flux | kgCO2/m2/s |
| `SFCO2_LND` | CO2 Land Surface Flux | kgCO2/m2/s |

**Annual cycle (land)** (1)

| 변수 | 설명 | 단위 |
|---|---|---|
| `NEE` | net ecosys exchange of C | gC/m^2/s |

**Contours** (8)

| 변수 | 설명 | 단위 |
|---|---|---|
| `CO2` | CO2 concentration | kgCO2/kgDryAir |
| `CO2_LND` | CO2 Land-Atm Concentration | kgCO2/kgDryAir |
| `CO2_OCN` | CO2 Ocn-Atm Concentration | kgCO2/kgDryAir |
| `CO2_FFF` | CO2 Fossil Fuel Concentration | kgCO2/kgDryAir |
| `SFCO2` | CO2 Surface Flux | kgCO2/m2/s |
| `SFCO2_FFF` | CO2 Fossil Fuel Surface Flux | kgCO2/m2/s |
| `SFCO2_OCN` | CO2 Ocean Surface Flux | kgCO2/m2/s |
| `SFCO2_LND` | CO2 Land Surface Flux | kgCO2/m2/s |

**Contours (DJF-JJA)** (8)

| 변수 | 설명 | 단위 |
|---|---|---|
| `CO2` | CO2 concentration | kgCO2/kgDryAir |
| `CO2_LND` | CO2 Land-Atm Concentration | kgCO2/kgDryAir |
| `CO2_OCN` | CO2 Ocn-Atm Concentration | kgCO2/kgDryAir |
| `CO2_FFF` | CO2 Fossil Fuel Concentration | kgCO2/kgDryAir |
| `SFCO2` | CO2 Surface Flux | kgCO2/m2/s |
| `SFCO2_FFF` | CO2 Fossil Fuel Surface Flux | kgCO2/m2/s |
| `SFCO2_OCN` | CO2 Ocean Surface Flux | kgCO2/m2/s |
| `SFCO2_LND` | CO2 Land Surface Flux | kgCO2/m2/s |

**Trends** (8)

| 변수 | 설명 | 단위 |
|---|---|---|
| `CO2` | CO2 concentration | kgCO2/kgDryAir |
| `CO2_LND` | CO2 Land-Atm Concentration | kgCO2/kgDryAir |
| `CO2_OCN` | CO2 Ocn-Atm Concentration | kgCO2/kgDryAir |
| `CO2_FFF` | CO2 Fossil Fuel Concentration | kgCO2/kgDryAir |
| `SFCO2` | CO2 Surface Flux | kgCO2/m2/s |
| `SFCO2_FFF` | CO2 Fossil Fuel Surface Flux | kgCO2/m2/s |
| `SFCO2_OCN` | CO2 Ocean Surface Flux | kgCO2/m2/s |
| `SFCO2_LND` | CO2 Land Surface Flux | kgCO2/m2/s |

**Zonal means** (8)

| 변수 | 설명 | 단위 |
|---|---|---|
| `CO2` | CO2 concentration | kgCO2/kgDryAir |
| `CO2_LND` | CO2 Land-Atm Concentration | kgCO2/kgDryAir |
| `CO2_OCN` | CO2 Ocn-Atm Concentration | kgCO2/kgDryAir |
| `CO2_FFF` | CO2 Fossil Fuel Concentration | kgCO2/kgDryAir |
| `SFCO2` | CO2 Surface Flux | kgCO2/m2/s |
| `SFCO2_FFF` | CO2 Fossil Fuel Surface Flux | kgCO2/m2/s |
| `SFCO2_OCN` | CO2 Ocean Surface Flux | kgCO2/m2/s |
| `SFCO2_LND` | CO2 Land Surface Flux | kgCO2/m2/s |

**Zonal means (land)** (1)

| 변수 | 설명 | 단위 |
|---|---|---|
| `NEE` | net ecosys exchange of C | gC/m^2/s |

## set10 — Seasonal mean contours zoomed on the Greenland ice sheet

**CLM core** (52)

| 변수 | 설명 | 단위 |
|---|---|---|
| `TSA` | 2m air temperature | K |
| `PREC` | ppt: rain+snow | mm/s |
| `ASA` | all-sky albedo:FSR/FSDS | proportion |
| `RNET` | net radiation:fsa-fira | W/m^2 |
| `LHEAT` | latent heat:FCTR+FCEV+FGEV | W/m^2 |
| `TOTRUNOFF` | Total Liquid Runoff | mm/s |
| `QOVER` | surface runoff | mm/s |
| `QRGWL` | surface runoff at glaciers (liquid only), wetlands, lakes | mm/s |
| `QRUNOFF_RAIN_TO_SNOW_CONVERSION` | liquid runoff from rain-to-snow conversion when this conversion leads to immediate runoff | mm/s |
| `QDRAI` | sub-surface drainage | mm/s |
| `QFLX_LIQ_DYNBAL` | liq dynamic land cover change conversion runoff flux | mm/s |
| `QFLX_ICE_DYNBAL` | ice dynamic land cover change conversion runoff flux | mm/s |
| `QRUNOFF_ICE` | total liquid runoff not incl correction for LULCC (ice landunits only) | mm/s |
| `SNOWDP` | snow height | m |
| `FSH` | sensible heat | W/m^2 |
| `FSH_TO_COUPLER` | sensible heat sent to coupler | W/m^2 |
| `FSH_PRECIP_CONVERSION` | SHF from conv of rain/snow atm forcing | W/m^2 |
| `FSH_RUNOFF_ICE_TO_LIQ` | SHF from conv of ice runoff to liquid | W/m^2 |
| `TV` | vegetation temperature | K |
| `TG` | ground temperature | K |
| `FSA` | absorbed solar radiation | W/m^2 |
| `FSR` | reflected solar radiation | W/m^2 |
| `FIRA` | net infrared (longwave) radiation | W/m^2 |
| `FIRE` | emitted infrared (longwave) radiation | W/m^2 |
| `FGR` | heat flux into snow/soil (includes snow melt) | W/m^2 |
| `FSM` | snow melt heat flux | W/m^2 |
| `H2OSNO` | total snow water equiv (SNOWICE + SNOWLIQ) | mm |
| `H2OSNO_ICE` | total snow water equiv (SNOWICE + SNOWLIQ) over glacier units | mm |
| `QSNOMELT` | snow melt | mm/s |
| `QSNOMELT_ICE` | snow melt over glacier units | mm/s |
| `QSNOFRZ` | column-integrated snow freezing rate | mm/s |
| `QSNOFRZ_ICE` | column-integrated snow freezing rate (ice landunits only) | mm/s |
| `QSOIL` | ground evaporation | mm/s |
| `QSOIL_ICE` | ground evaporation over glacier units | mm/s |
| `QICE_FRZ` | ice growth | mm/s |
| `QICE_MELT` | ice melt | mm/s |
| `QICE` | ice growth/melt | mm/s |
| `FSNO` | fraction of ground covered by snow | unitless |
| `RAIN` | atmospheric rain | mm/s |
| `SNOW` | atmospheric snow | mm/s |
| `RAIN_REPARTITIONED` | atmospheric rain after repartitioning | mm/s |
| `SNOW_REPARTITIONED` | atmospheric snow after repartitioning | mm/s |
| `P-E` | PREC-ET | mm/s |
| `WIND` | atmospheric wind velocity magnitude | m/s |
| `FLDS` | atmospheric longwave radiation | W/m^2 |
| `FSDS` | atmospheric incident solar radiation | W/m^2 |
| `Q2M` | 2m specific humidity | kg/kg |
| `RH2M` | 2m relative humidity | % |
| `TSOI` | soil temperature | K |
| `TWS` | total water storage | mm |
| `U10` | 10-m wind | m/s |
| `PBOT` | atm pressure of bottom layer | Pa |

## set11 — Seasonal mean contours zoomed on the Antarctic ice sheet

**CLM core** (52)

| 변수 | 설명 | 단위 |
|---|---|---|
| `TSA` | 2m air temperature | K |
| `PREC` | ppt: rain+snow | mm/s |
| `ASA` | all-sky albedo:FSR/FSDS | proportion |
| `RNET` | net radiation:fsa-fira | W/m^2 |
| `LHEAT` | latent heat:FCTR+FCEV+FGEV | W/m^2 |
| `TOTRUNOFF` | Total Liquid Runoff | mm/s |
| `QOVER` | surface runoff | mm/s |
| `QRGWL` | surface runoff at glaciers (liquid only), wetlands, lakes | mm/s |
| `QRUNOFF_RAIN_TO_SNOW_CONVERSION` | liquid runoff from rain-to-snow conversion when this conversion leads to immediate runoff | mm/s |
| `QDRAI` | sub-surface drainage | mm/s |
| `QFLX_LIQ_DYNBAL` | liq dynamic land cover change conversion runoff flux | mm/s |
| `QFLX_ICE_DYNBAL` | ice dynamic land cover change conversion runoff flux | mm/s |
| `QRUNOFF_ICE` | total liquid runoff not incl correction for LULCC (ice landunits only) | mm/s |
| `SNOWDP` | snow height | m |
| `FSH` | sensible heat | W/m^2 |
| `FSH_TO_COUPLER` | sensible heat sent to coupler | W/m^2 |
| `FSH_PRECIP_CONVERSION` | SHF from conv of rain/snow atm forcing | W/m^2 |
| `FSH_RUNOFF_ICE_TO_LIQ` | SHF from conv of ice runoff to liquid | W/m^2 |
| `TV` | vegetation temperature | K |
| `TG` | ground temperature | K |
| `FSA` | absorbed solar radiation | W/m^2 |
| `FSR` | reflected solar radiation | W/m^2 |
| `FIRA` | net infrared (longwave) radiation | W/m^2 |
| `FIRE` | emitted infrared (longwave) radiation | W/m^2 |
| `FGR` | heat flux into snow/soil (includes snow melt) | W/m^2 |
| `FSM` | snow melt heat flux | W/m^2 |
| `H2OSNO` | total snow water equiv (SNOWICE + SNOWLIQ) | mm |
| `H2OSNO_ICE` | total snow water equiv (SNOWICE + SNOWLIQ) over glacier units | mm |
| `QSNOMELT` | snow melt | mm/s |
| `QSNOMELT_ICE` | snow melt over glacier units | mm/s |
| `QSNOFRZ` | column-integrated snow freezing rate | mm/s |
| `QSNOFRZ_ICE` | column-integrated snow freezing rate (ice landunits only) | mm/s |
| `QSOIL` | ground evaporation | mm/s |
| `QSOIL_ICE` | ground evaporation over glacier units | mm/s |
| `QICE_FRZ` | ice growth | mm/s |
| `QICE_MELT` | ice melt | mm/s |
| `QICE` | ice growth/melt | mm/s |
| `FSNO` | fraction of ground covered by snow | unitless |
| `RAIN` | atmospheric rain | mm/s |
| `SNOW` | atmospheric snow | mm/s |
| `RAIN_REPARTITIONED` | atmospheric rain after repartitioning | mm/s |
| `SNOW_REPARTITIONED` | atmospheric snow after repartitioning | mm/s |
| `P-E` | PREC-ET | mm/s |
| `WIND` | atmospheric wind velocity magnitude | m/s |
| `FLDS` | atmospheric longwave radiation | W/m^2 |
| `FSDS` | atmospheric incident solar radiation | W/m^2 |
| `Q2M` | 2m specific humidity | kg/kg |
| `RH2M` | 2m relative humidity | % |
| `TSOI` | soil temperature | K |
| `TWS` | total water storage | mm |
| `U10` | 10-m wind | m/s |
| `PBOT` | atm pressure of bottom layer | Pa |

