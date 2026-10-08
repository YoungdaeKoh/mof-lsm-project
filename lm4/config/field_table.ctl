# specific humidity for moist runs
 "TRACER", "atmos_mod", "sphum"
           "longname", "specific humidity"
           "units", "kg/kg"
           "profile_type", "fixed", "surface_value=3.e-6" /
# prognostic cloud scheme tracers
  "TRACER", "atmos_mod", "liq_wat"
            "longname", "cloud liquid specific humidity"
            "units", "kg/kg" /
  "TRACER", "atmos_mod", "ice_wat"
            "longname", "cloud ice water specific humidity"
            "units", "kg/kg" /
# begin  adding tracers for MG2 microphysics
  "TRACER", "atmos_mod", "rainwat"
            "longname", "rain water specific humidity"
            "units", "kg/kg" /
  "TRACER", "atmos_mod", "snowwat"
            "longname", "snow water specific humidity"
            "units", "kg/kg" /
  "TRACER", "atmos_mod", "graupel"
            "longname", "graupel water specific humidity"
            "units", "kg/kg" /
  "TRACER", "atmos_mod", "liq_drp"
            "longname", "cloud droplet"
            "units", "none" /
  "TRACER", "atmos_mod", "ice_num"
            "longname", "cloud ice number specific humidity"
            "units", "#/kg" /
  "TRACER", "atmos_mod", "rain_num"
            "longname", "rain number specific humidity"
            "units", "#/kg" /
  "TRACER", "atmos_mod", "snow_num"
            "longname", "snow number specific humidity"
            "units", "#/kg" /
# end adding tracers for MG2 microphysics
  "TRACER", "atmos_mod", "cld_amt"
            "longname", "cloud fraction"
            "units", "none" /
# required by LM3
  "TRACER", "land_mod", "sphum"
           "longname",     "specific humidity"
            "units",        "kg/kg" /
 "TRACER", "land_mod",     "dust1"
           "longname",     "dust1 tracer"
           "units",        "mmr" /
 "TRACER", "land_mod",     "dust2"
           "longname",     "dust2 tracer"
           "units",        "mmr" /
 "TRACER", "land_mod",     "dust3"
           "longname",     "dust3 tracer"
           "units",        "mmr" /
 "TRACER", "land_mod",     "dust4"
           "longname",     "dust4 tracer"
           "units",        "mmr" /
 "TRACER", "land_mod",     "dust5"
           "longname",     "dust5 tracer"
           "units",        "mmr" /
  "TRACER", "land_mod",     "co2"
           "longname",     "carbon dioxide"
           "units",        "kg/kg" /
# land field table needed for any coupler flux exchange
# otherwise the model crashes in flux_exchange
"TRACER", "land_mod","nh4"
          "longname","nh4"
          "dry_deposition","aerosol"
	  "units","vmr"/
"TRACER", "land_mod","nh3"
          "longname","nh3"
          "dry_deposition","gas","reactivity=0.,alpha=1."
	  "units","vmr"/
#alpha is taken from Zhang(2002) when possible.
#Otherwise use effective solubility relative to H2*(SO2)
  "TRACER", "land_mod",     "so2"
            "longname",     "so2 tracer"
            "dry_deposition","gas","reactivity=0.0, alpha=1"
            "units",        "vmr" /
  "TRACER", "land_mod",     "hno3"
            "longname",     "hno3 tracer"
            "dry_deposition","gas","reactivity=1., alpha=1.e5"
            "units",        "vmr" /
#H2O2 - use higher parameters based on Nguyen (PNAS)	    
  "TRACER", "land_mod",     "h2o2"
            "longname",     "h2o2 tracer"
            "dry_deposition","gas","reactivity=1., alpha=1.e5"
            "units",        "vmr" /
#H2 is a special case
  "TRACER", "land_mod",     "h2"
            "longname",     "h2 tracer"
            "dry_deposition","gas_bertagni","reactivity=0.0, alpha=0.,scale_stom=0."
            "units",        "vmr" /
  "TRACER", "land_mod",     "o3"
            "longname",     "o3 tracer"
            "dry_deposition","gas","reactivity=1., alpha=0.,a_RH=1."
            "units",        "vmr" /
  "TRACER", "land_mod",     "so4"
            "longname",     "so4 tracer"
            "dry_deposition","aerosol"
            "units",        "vmr" /
  "TRACER", "land_mod",     "soa"
            "longname",     "soa tracer"
            "dry_deposition","aerosol"
            "units",        "mmr" /
  "TRACER", "land_mod",     "bcphob"
            "longname",     "bcphob tracer"
            "dry_deposition","aerosol"
            "units",        "mmr" /
  "TRACER", "land_mod",     "bcphil"
            "longname",     "bcphil tracer"
            "dry_deposition","aerosol"
            "units",        "mmr" /
  "TRACER", "land_mod",     "omphob"
            "longname",     "omphob tracer"
            "dry_deposition","aerosol"
            "units",        "mmr" /
  "TRACER", "land_mod",     "omphil"
            "longname",     "omphil tracer"
            "dry_deposition","aerosol"
            "units",        "mmr" /
#H_cp = 9.7e-6
#  "TRACER", "land_mod",     "co"
#            "longname",     "co tracer"
#            "dry_deposition","gas","reactivity=0.0, alpha=9.8e-9"
#            "units",        "vmr" /
  "TRACER", "land_mod",     "ch2o"
            "longname",     "ch2o tracer"
            "dry_deposition","gas","reactivity=0.2, alpha=0.8"
            "units",        "vmr" /
  "TRACER", "land_mod",     "no2"
            "longname",     "no2 tracer"
            "dry_deposition","gas","reactivity=0.8, alpha=0."
            "units",        "vmr" /
  "TRACER", "land_mod",     "ho2no2"
            "longname",     "ho2no2 tracer"
            "dry_deposition","gas","reactivity=0., alpha=4e-4"
            "units",        "vmr" /
#TREAT LIKE HNO3
  "TRACER", "land_mod",     "n2o5"
            "longname",     "n2o5 tracer"
            "dry_deposition","gas","reactivity=1., alpha=1e5"
            "units",        "vmr" /
#Use Zhang for reactivity	    
  "TRACER", "land_mod",     "ch3ooh"
            "longname",     "ch3ooh tracer"
            "dry_deposition","gas","reactivity=0.8, alpha=0.003"
            "units",        "vmr" /
#Following Wu et al. (2012)	    
  "TRACER", "land_mod",     "pan"
            "longname",     "pan tracer"
            "dry_deposition","gas","reactivity=2, alpha=0."
            "units",        "vmr" /
#Scaled from PAN 	    
  "TRACER", "land_mod",     "mpan"
            "longname",     "mpan tracer"
            "dry_deposition","gas","reactivity=1, alpha=0."
            "units",        "vmr" /
  "TRACER", "land_mod",     "ch3coch3"
            "longname",     "ch3coch3 tracer"
            "dry_deposition","gas","reactivity=0., alpha=1."
            "units",        "vmr" /
  "TRACER", "land_mod",     "ch3oh"
            "longname",     "ch3oh tracer"
            "dry_deposition","gas","reactivity=0.1, alpha=0.6"
            "units",        "vmr" /
  "TRACER", "land_mod",     "c2h5oh"
            "longname",     "c2h5oh tracer"
            "dry_deposition","gas","reactivity=0.0, alpha=0.6"
            "units",        "vmr" /
#H = 3.9e2 mol/m3/Pa	    
  "TRACER", "land_mod",     "glyald"
            "longname",     "glyald tracer"
            "dry_deposition","gas","reactivity=0.0, alpha=0.4"
            "units",        "vmr" /
#H = 77 mol/m3/Pa	    
  "TRACER", "land_mod",     "hyac"
            "longname",     "hyac tracer"
            "dry_deposition","gas","reactivity=0.0, alpha=0.08"
            "units",        "vmr" /
  "TRACER", "land_mod",     "isopooh"
            "longname",     "isopooh tracer"
            "dry_deposition","gas","reactivity=0.0, alpha=700"
            "units",        "vmr" /
  "TRACER", "land_mod",     "dms"
            "longname",     "dms tracer"
            "dry_deposition","gas","reactivity=0.0, alpha=0.54e-5"
            "units",        "vmr" /
#TREAT LIKE HNO3	    
  "TRACER", "land_mod",     "nh4no3"
            "longname",     "nh4no3 tracer"
            "dry_deposition","gas","mw=63e-3, reactivity=1., alpha=1.e5"
            "units",        "vmr" /
#FOR now ignore the following:
#  "TRACER", "land_mod",     "hcl"
#            "longname",     "hcl tracer"
#            "dry_deposition","gas","mw=36.5e-3, reactivity=1., alpha=1.e5"
#            "units",        "vmr" /
#  "TRACER", "land_mod",     "hobr"
#            "longname",     "hobr tracer"
#            "dry_deposition","gas","mw=97e-3, reactivity=1., alpha=0.061"
#            "units",        "vmr" /
#  "TRACER", "land_mod",     "hbr"
#            "longname",     "hbr tracer"
#            "dry_deposition","gas","mw=81e-3, reactivity=1., alpha=1e5"
#            "units",        "vmr" /
#  "TRACER", "land_mod",     "brono2"
#            "longname",     "brono2 tracer"
#            "dry_deposition","gas","mw=142e-3, reactivity=1., alpha=1e5"
#            "units",        "vmr" /
#Based on Zhang (2002). 
  "TRACER", "land_mod",     "atooh"
            "longname",     "atooh tracer"
            "dry_deposition","gas","reactivity=1., alpha=0.1"
            "units",        "vmr" /
#H = 4.1e3 mol/m3/Pa	    
  "TRACER", "land_mod",     "glyx"
            "longname",     "glyx tracer"
            "dry_deposition","gas","reactivity=1., alpha=4.2"
            "units",        "vmr" /
  "TRACER", "land_mod",     "iepox"
            "longname",     "iepox tracer"
            "dry_deposition","gas","reactivity=0., alpha=700"
            "units",        "vmr" /
  "TRACER", "land_mod",     "isopnb"
            "longname",     "isopnb tracer"
            "dry_deposition","gas","reactivity=1., alpha=0.17"
            "units",        "vmr" /
  "TRACER", "land_mod",     "macrn"
            "longname",     "macrn tracer"
            "dry_deposition","gas","reactivity=1., alpha=0.17"
            "units",        "vmr" /
  "TRACER", "land_mod",     "mgly"
            "longname",     "mgly tracer"
            "dry_deposition","gas","reactivity=1., alpha=0.0355"
            "units",        "vmr" /
  "TRACER", "land_mod",     "mvkn"
            "longname",     "mvkn tracer"
            "dry_deposition","gas","reactivity=1., alpha=0.17"
            "units",        "vmr" /
  "TRACER", "land_mod",     "r4n2"
            "longname",     "r4n2 tracer"
            "dry_deposition","gas","reactivity=1., alpha=0.17"
            "units",        "vmr" /
  "TRACER", "land_mod",     "o3s"
            "longname",     "o3s tracer"
            "dry_deposition","gas","reactivity=1., alpha=0."
            "units",        "vmr" /
  "TRACER", "land_mod",     "o3s_e90"
            "longname",     "o3s_e90 tracer"
            "dry_deposition","gas","reactivity=1., alpha=0."
            "units",        "vmr" /
#Henry's law are in M/Pa
# atm chem
 "TRACER", "atmos_mod", "SOA"
           "longname", "SOA tracer"
           "units", "mmr"
           "convection", "all"
           "chem_param","aerosol","frac_pm1=0.89,frac_pm25=0.96,frac_pm10=1."
           "profile_type","fixed","surface_value=1.e-32"
           "dry_deposition","williams_wind_driven land:dynamic","surfr=400.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.33, frac_incloud_uw=0.44, frac_incloud_snow=0., alphar=0.001, alphas=0.001"
           "radiative_param", "online", "name_in_rad_mod=omphilic, name_in_clim_mod=organic_carbon" /
#
 "TRACER", "atmos_mod", "dust1"
           "longname", "dust1 tracer"
           "units", "mmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=0.1e-6, rb=1.0e-6, dustref=0.75e-6, dustden=2500.0"
           "emission", "lm3", "source_fraction=0.05"
           "convection", "all"
           "dry_deposition","williams_wind_driven","surfr=200.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.2, frac_incloud_uw=0.3, frac_incloud_snow=0.05, alphar=0.001, alphas=0.001"
           "chem_param","aerosol","frac_pm1=0.444,frac_pm25=1.,frac_pm10=1."
           "radiative_param", "online", "name_in_rad_mod=dust1, name_in_clim_mod=small_dust"/
 "TRACER", "atmos_mod", "dust2"
           "longname", "dust2 tracer"
           "units", "mmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=1.0e-6, rb=2.0e-6, dustref=1.5e-6, dustden=2650.0"
           "emission", "lm3", "source_fraction=0.15"
           "convection", "all"
           "dry_deposition","williams_wind_driven","surfr=100.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.2, frac_incloud_uw=0.3, frac_incloud_snow=0.05, alphar=0.001, alphas=0.001"
           "chem_param","aerosol","frac_pm1=0.,frac_pm25=0.25,frac_pm10=1."
           "radiative_param", "online", "name_in_rad_mod=dust2, name_in_clim_mod=large_dust"/
 "TRACER", "atmos_mod", "dust3"
           "longname", "dust3 tracer"
           "units", "mmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=2.0e-6, rb=3.0e-6, dustref=2.5e-6, dustden=2650.0"
           "emission", "lm3", "source_fraction=0.3"
           "convection", "all"
           "dry_deposition","williams_wind_driven","surfr=100.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.2, frac_incloud_uw=0.3, frac_incloud_snow=0.05, alphar=0.001, alphas=0.001"
           "chem_param","aerosol","frac_pm1=0.,frac_pm25=0.,frac_pm10=1."
           "radiative_param", "online", "name_in_rad_mod=dust3, name_in_clim_mod=large_dust"/
 "TRACER", "atmos_mod", "dust4"
           "longname", "dust4 tracer"
           "units", "mmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=3.0e-6, rb=6.0e-6, dustref=4.5e-6, dustden=2650.0"
           "emission", "lm3", "source_fraction=0.27"
           "convection", "all"
           "dry_deposition","williams_wind_driven","surfr=100.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.2, frac_incloud_uw=0.3, frac_incloud_snow=0.05, alphar=0.001, alphas=0.001"
           "chem_param","aerosol","frac_pm1=0.,frac_pm25=0.,frac_pm10=0.667"
           "radiative_param", "online", "name_in_rad_mod=dust4, name_in_clim_mod=large_dust"/
 "TRACER", "atmos_mod", "dust5"
           "longname", "dust5 tracer"
           "units", "mmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=6.0e-6, rb=10.0e-6, dustref=8e-6, dustden=2650.0"
           "emission", "lm3", "source_fraction=0.23"
           "convection", "all"
           "dry_deposition","williams_wind_driven","surfr=100.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.2, frac_incloud_uw=0.3, frac_incloud_snow=0.05, alphar=0.001, alphas=0.001"
           "chem_param","aerosol","frac_pm1=0.,frac_pm25=0.,frac_pm10=0."
           "radiative_param", "online", "name_in_rad_mod=dust5, name_in_clim_mod=large_dust"/
#
"tracer","atmos_mod","so4"
"longname","SO4"
"units", "VMR"
"profile_type","fixed","surface_value=1.e-20"
"emissions", "file"
"wet_deposition","aerosol_below","frac_incloud=0.33, frac_incloud_uw=0.44, frac_incloud_snowh=0.11, frac_incloud_snow=0., alphar=0.001, alphas=0.001"
"dry_deposition","williams_wind_driven land:dynamic","surfr=400.,icer=1000."	
"convection", "all"
"radiative_param", "online", "name_in_rad_mod=so4, name_in_clim_mod=sulfate, scale_factor=3.31"
"cmip","cmip6","cmip_name=sulfate,cmip_longname=sulfate,cmip_longname2=SO4"
"chem_param","aerosol","mw=96.,frac_pm1=0.9,frac_pm25=0.97,frac_pm10=1."
/
#
 "TRACER", "atmos_mod", "ssalt1"
           "longname", "ssalt 1 tracer"
           "units", "mmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=0.1e-6, rb=0.5e-6, ssaltref=0.3e-6, ssaltden=2200.0"
           "convection", "all"
           "scheme", "Gong",
           "chem_param","aerosol","frac_pm1=1.0,frac_pm25=1.0,frac_pm10=1."
           "dry_deposition","williams_wind_driven","surfr=400.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.33, frac_incloud_uw=0.44, alphar=0.001, alphas=0.001"
           "radiative_param", "online", "name_in_rad_mod=seasalt1, name_in_clim_mod=sea_salt"/
 "TRACER", "atmos_mod", "ssalt2"
           "longname", "ssalt 2 tracer"
           "units", "mmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=0.5e-6, rb=1.0e-6, ssaltref=0.75e-6, ssaltden=2200.0"
           "convection", "all"
           "scheme", "Gong",
           "chem_param","aerosol","frac_pm1=0.0,frac_pm25=1.0,frac_pm10=1."
           "dry_deposition","williams_wind_driven","surfr=200.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.33, frac_incloud_uw=0.44, alphar=0.001, alphas=0.001"
           "radiative_param", "online", "name_in_rad_mod=seasalt2, name_in_clim_mod=sea_salt"/
 "TRACER", "atmos_mod", "ssalt3"
           "longname", "ssalt 3 tracer"
           "units", "mmr"
           "scheme", "Gong",
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=1.0e-6, rb=2.5e-6, ssaltref=1.75e-6, ssaltden=2200.0"
           "convection", "all"
           "chem_param","aerosol","frac_pm1=0.0,frac_pm25=0.167,frac_pm10=1."
           "dry_deposition","williams_wind_driven","surfr=40.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.44, frac_incloud_uw=0.55, alphar=0.001, alphas=0.001"
           "radiative_param", "online", "name_in_rad_mod=seasalt3, name_in_clim_mod=sea_salt"/
 "TRACER", "atmos_mod", "ssalt4"
           "longname", "ssalt 4 tracer"
           "units", "mmr"
           "scheme", "Gong",
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=2.5e-6, rb=5.0e-6, ssaltref=3.75e-6, ssaltden=2200.0"
           "convection", "all"
           "chem_param","aerosol","frac_pm1=0.0,frac_pm25=0.,frac_pm10=1."
           "dry_deposition","williams_wind_driven","surfr=1.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.44, frac_incloud_uw=0.55, alphar=0.001, alphas=0.001"
           "radiative_param", "online", "name_in_rad_mod=seasalt4, name_in_clim_mod=sea_salt"/
 "TRACER", "atmos_mod", "ssalt5"
           "longname", "ssalt 5 tracer"
           "units", "mmr"
           "scheme", "Gong",
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=5.0e-6, rb=10.0e-6, ssaltref=7.5e-6, ssaltden=2200.0"
           "convection", "all"
           "chem_param","aerosol","frac_pm1=0.0,frac_pm25=0.,frac_pm10=0."
           "dry_deposition","williams_wind_driven","surfr=0.1,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.44, frac_incloud_uw=0.55, alphar=0.001, alphas=0.001"
           "radiative_param", "online", "name_in_rad_mod=seasalt5, name_in_clim_mod=sea_salt"/
#
 "TRACER", "atmos_mod", "bcphob"
           "longname", "bcphob tracer"
           "units", "mmr"
           "profile_type","fixed","surface_value=1.e-32"
           "convection", "all"
           "chem_param","aerosol","frac_pm1=0.981,frac_pm25=0.995,frac_pm10=1."
           "dry_deposition","williams_wind_driven land:dynamic","surfr=400.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0., alphar=0.001, alphas=0.001"
           "radiative_param", "online", "name_in_rad_mod=bcphobic, name_in_clim_mod=black_carbon"/
 "TRACER", "atmos_mod", "bcphil"
           "longname", "bcphil tracer"
           "units", "mmr"
           "profile_type","fixed","surface_value=1.e-32"
           "convection", "all"
           "chem_param","aerosol","frac_pm1=0.981,frac_pm25=0.995,frac_pm10=1."
           "dry_deposition","williams_wind_driven land:dynamic","surfr=400.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.33, frac_incloud_uw=0.44, frac_incloud_snow=0., alphar=0.001, alphas=0.001"
           "radiative_param", "online", "name_in_rad_mod=bcphilic, name_in_clim_mod=black_carbon"/
 "TRACER", "atmos_mod", "omphob"
           "longname", "omphob tracer"
           "units", "mmr"
           "profile_type","fixed","surface_value=1.e-32"
           "convection", "all"
           "chem_param","aerosol","frac_pm1=0.89,frac_pm25=0.960,frac_pm10=1."
           "dry_deposition","williams_wind_driven land:dynamic","surfr=400.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0., alphar=0.001, alphas=0.001"
           "radiative_param", "online", "name_in_rad_mod=omphobic, name_in_clim_mod=organic_carbon"/
 "TRACER", "atmos_mod", "omphil"
           "longname", "omphil tracer"
           "units", "mmr"
           "profile_type","fixed","surface_value=1.e-32"
           "convection", "all"
           "chem_param","aerosol","frac_pm1=0.89,frac_pm25=0.960,frac_pm10=1."
            "dry_deposition","williams_wind_driven land:dynamic","surfr=400.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.33, frac_incloud_uw=0.44, frac_incloud_snow=0., alphar=0.001, alphas=0.001"
           "radiative_param", "online", "name_in_rad_mod=omphilic, name_in_clim_mod=organic_carbon"/
#
"tracer","atmos_mod","radon"
"longname","radon-222"
"units","VMR*1E21"
"profile_type","fixed","surface_value=0.0E+00"
"convection","all"
/
"tracer","atmos_mod","co"
"longname","CO"
"cmip","cmip6","cmip_name=carbon_monoxide"
"units","VMR"
"emissions", "file"
"emissions2dbb", "file"
"dry_deposition", "file"
"init_conc", "file"
"convection","all"
/
"tracer","atmos_mod","ch2o"
"longname","CH2O"
"cmip","cmip6","cmip_name=Formaldehyde,cmip_longname=Formaldehyde"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"emissions", "file"
"emissions2dbb", "file"
"wet_deposition","henry_below_noice","henry=3.2e-2,dependence=7100."
"dry_deposition", "file land:dynamic"
"convection","all"
"chem_param","gas","mw=30."
/
"tracer","atmos_mod","oh"
          "longname","OH"
          "cmip","cmip6","cmip_name=hydroxyl_radical"
          "units","VMR"
          "tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","o3"
"longname","O3"
"cmip","cmip6","cmip_name=ozone,cmip_longname=Ozone"
"units","VMR"
"chem_param","gas","mw=48."
"dry_deposition","file land:dynamic","diurnal=yes"
"init_conc","file"
"convection","all"
/
"tracer","atmos_mod","o"
"longname","O"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","o1d"
"longname","O1D"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","n2o"
"longname","N2O"
"units","VMR"
"cmip","cmip6","cmip_name=nitrous_oxide"
"init_conc","file"
"convection","all"
"lower_bound","file","file=n2o_gblannualdata,factor=1.e-9"
/
"tracer","atmos_mod","n"
"longname","N"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","no"
"longname","NO"
"units","VMR"
"cmip","cmip6","cmip_name=nitrogen_oxide"
"chem_param","gas","nb_N_ox=1,mw=30."
"emissions","file"
"emissions2dbb", "file"
"dry_deposition","file"
"init_conc","file"
"aircraft_emis","file","name=no"
"convection","all"
/
"tracer","atmos_mod","no2"
"longname","NO2"
"units","VMR"
"cmip","cmip6","cmip_name=nitrogen_dioxide"
"chem_param","gas","nb_N_ox=1,mw=46."
"emissions","none"
"dry_deposition","file land:dynamic"
"init_conc","file"
"convection","all"
/
"tracer","atmos_mod","no3"
"longname","NO3"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"convection","all"
/
"tracer","atmos_mod","hno3"
"longname","HNO3"
"units","VMR"
"cmip","cmip6","cmip_name=nitric_acid"
"chem_param","gas","nb_N_ox=1,mw=63."
"wet_deposition","henry_below","henry=3.19e6,dependence=8700."
"dry_deposition","file land:dynamic"
"init_conc","file"
"convection","all"
/
"tracer","atmos_mod","ho2no2"
"longname","HO2NO2"
"units","VMR"
"chem_param","gas","nb_N_ox=1,mw=79."
"dry_deposition","file land:dynamic","name=hno4"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=3.9e-4,dependence=8400."
"convection","all"
"chem_param","gas","mw=79."
/
"tracer","atmos_mod","n2o5"
"longname","N2O5"
"units","VMR"
"chem_param","gas","nb_N_ox=2,mw=108."
"init_conc","file"
"dry_deposition","file land:dynamic"
"convection","all"
"chem_param","gas","mw=108."
/
"tracer","atmos_mod","ch4"
"longname","CH4"
"units","VMR"
"cmip","cmip6","cmip_name=methane"
"dry_deposition","file"
"init_conc","file"
"convection","all"
"lower_bound","file","file_nc=ch4_2d_CMIP7.nc,factor=1.e-9,dry=yes"
/
"tracer","atmos_mod","ch3o2"
"longname","CH3O2"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","ch3ooh"
"longname","CH3OOH"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=0.003,dependence=7500."
"dry_deposition","file land:dynamic"
"convection","all"
"chem_param","gas","mw=48."
/
"tracer","atmos_mod","ho2"
"longname","HO2"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","h2o2"
"longname","H2O2"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=8.6e-1,dependence=7300."
"dry_deposition","file land:dynamic"
"convection","all"
"chem_param","mw=34."
/
"tracer","atmos_mod","c3h6"
"longname","C3H6"
"units","VMR"
"cmip","cmip6","cmip_name=ethene"
"profile_type","fixed","surface_value=1.e-20"
"emissions","file"
"emissions2dbb","file"
"convection","all"
/
"tracer","atmos_mod","isop"
"longname","isoprene(C5H8)"
"units","VMR"
"cmip","cmip6","cmip_name=isoprene,cmip_longname=Isoprene"
"profile_type","fixed","surface_value=1.e-20"
"emissions","file","name=isoprene"
"emissions2dbb","file","name=isoprene"
"xactive_emissions","yes"
"convection","all"
/
"tracer","atmos_mod","po2"
"longname","PO2(C3H6OHO2)"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","ch3cho"
"longname","CH3CHO"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=1.3e-4,dependence=5900."
"convection","all"
/
"tracer","atmos_mod","pooh"
"longname","POOH(C3H6OHOOH)"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","ch3co3"
"longname","CH3CO3"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","ch3coooh"
"longname","CH3COOOH"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","pan"
"longname","PAN(CH3CO3NO2)"
"cmip","cmip6","cmip_name=peroxyacetyl_nitrate"
"units","VMR"
"chem_param","gas","nb_N_ox=1,mw=121."
"dry_deposition","file land:dynamic"
"init_conc","file"
"convection","all"
/
"tracer","atmos_mod","c2h6"
"longname","C2H6"
"cmip","cmip6","cmip_name=ethane"
"units","VMR"
"emissions", "file"
"emissions2dbb","file"
"init_conc","file"
"convection","all"
/
"tracer","atmos_mod","c2h4"
"longname","C2H4"
"units","VMR"
"cmip","cmip6","cmip_name=ethene"
"profile_type","fixed","surface_value=1.e-20"
"emissions", "file"
"emissions2dbb", "file"
"convection","all"
/
"tracer","atmos_mod","c4h10"
"longname","C4H10"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"emissions","file"
"emissions2dbb","file"
"convection","all"
/
"tracer","atmos_mod","mpan"
"longname","MPAN(CH2CCH3CO3NO2)"
"chem_param","gas","mw=147.,nb_N_ox=1"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"dry_deposition","file land:dynamic","name=pmn"
"convection","all"
/
"tracer","atmos_mod","isopo2"
"longname","ISOPO2(HOCH2COOCH3CHCH2)"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","mvk"
"longname","MVK(CH2CHCOCH3)"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=2.07e-4,dependence=7800."
"convection","all"
/
"tracer","atmos_mod","macr"
"longname","MACR(CH2CCH3CHO)"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=4.24e-5,dependence=5300."
"convection","all"
/
"tracer","atmos_mod","macro2"
"longname","MACRO2(CH3COCHO2CH2OH)"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","macrooh"
"longname","MACROOH(CH3COCHOOHCH2OH)"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","c2h5o2"
"longname","C2H5O2"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","c2h5ooh"
"longname","C2H5OOH"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","c10h16"
"longname","C10H16"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"emissions","file","name=terpenes"
"emissions2dbb","file","name=terpenes"
"xactive_emissions","yes"
"convection","all"
/
"tracer","atmos_mod","c3h8"
"longname","C3H8"
"units","VMR"
"cmip","cmip6","cmip_name=propane"
"profile_type","fixed","surface_value=1.e-20"
"emissions","file"
"emissions2dbb","file"
"convection","all"
/
"tracer","atmos_mod","c3h7o2"
"longname","C3H7O2"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","c3h7ooh"
"longname","C3H7OOH"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","ch3coch3"
"longname","CH3COCH3"
"units","VMR"
"cmip","cmip6","cmip_name=acetone"
"emissions","file","name=acet"
"emissions2dbb","file","name=acet"
"dry_deposition","file land:dynamic"
"init_conc","file"
"convection","all"
"chem_param","gas","mw=58."
/
"tracer","atmos_mod","ch3oh"
"longname","CH3OH"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"emissions", "file"
"emissions2dbb", "file"
"wet_deposition","henry_below_noice","henry=2.e-3,dependence=5500."
"dry_deposition", "file land:dynamic", "name=ch3ooh"
"convection","all"
"chem_param","gas","mw=32."
/
"tracer","atmos_mod","c2h5oh"
"longname","C2H5OH"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"emissions", "file"
"emissions2dbb", "file"
"wet_deposition","henry_below_noice","henry=1.9e-3,dependence=6400."
"dry_deposition", "file land:dynamic", "name=ch3ooh"
"convection","all"
"chem_param","gas","mw=46."
/
"tracer","atmos_mod","glyald"
"longname","GLYALD(HOCH2CHO)"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=0.039,dependence=4600."
"dry_deposition", "file land:dynamic", "name=glyc"
"convection","all"
"chem_param","gas","mw=60."
/
"tracer","atmos_mod","hyac"
"longname","HYAC(CH3COCH2OH)"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=0.077"
"dry_deposition", "file land:dynamic", "name=hac"
"convection","all"
"chem_param","gas","mw=74."
/
"tracer","atmos_mod","eo2"
"longname","EO2(HOCH2CH2O2)"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","eo"
"longname","EO2(HOCH2CH2O)"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","isopooh"
"longname","ISOPOOH(HOCH2COOHCH3CHCH2)"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=691.,dependence=0"
"dry_deposition","file land:dynamic","name=rip"
"convection","all"
"chem_param","gas","mw=118."
/
"tracer","atmos_mod","h2"
"longname","H2"
"chem_param","gas","mw=2.016"
"units","VMR"
"emissions", "file"
"emissions2dbb","file"
"profile_type","fixed","surface_value=1.e-20"
"dry_deposition","file land:dynamic","name=h2,file=vd_optimized_2010_soilC.nc"
"convection","all"
/
"tracer","atmos_mod","so2"
"longname","SO2"
"cmip","cmip6","cmip_name=sulfur_dioxide"
"chem_param","gas","mw=64."
"units","VMR"
"emissions", "file"
"emissions2dbb", "file"
"emissions3d", "file","file=emissions3d.SO2.2000.v4plev.nc"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice_so2","henry=1.49e-2,dependence=5080."
"dry_deposition","file land:dynamic","name=so2"
"aircraft_emis","file"
"convection","all"
/
"tracer","atmos_mod","dms"
"longname","DMS"
"cmip","cmip6","cmip_name=dimethyl_sulfide"
"units","VMR"
"xactive_emissions", "yes"
"profile_type","fixed","surface_value=1.e-20"
"dry_deposition","fixed land:dynamic","land=0.11e-2, sea=0.09e-2"
"wet_deposition","henry_below","henry=5.3e-6, dependence=3500"
"convection","all"
"chem_param","gas","mw=62.14"
/
"tracer","atmos_mod","nh3"
"longname","NH3"
"cmip","cmip6","cmip_name=ammonia"
"units","VMR"
"emissions", "file"
"emissions2dbb", "file"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=3.3d1,dependence=4.1d3"
"dry_deposition","file land:dynamic"
"convection","all"
"chem_param","gas","mw=17.,nb_N_red=1"
/
"tracer","atmos_mod","nh4no3"
"longname","NH4NO3"
"units","VMR"
"cmip","cmip6","cmip_name=nitrate,cmip_longname=nitrate,cmip_longname2=NO3"
"chem_param","aerosol","mw=62,nb_N_ox=1,frac_pm1=0.877,frac_pm25=0.954,frac_pm10=1."
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","aerosol_below","frac_incloud=0.33, frac_incloud_uw=0.44, frac_incloud_snowh=0.11, frac_incloud_snow=0.,alphar=0.001, alphas=0.001"
"dry_deposition","file land:dynamic","name=hno3"
"convection","all"
"radiative_param", "online", "name_in_rad_mod=nitrate, name_in_clim_mod=nitrate, scale_factor=2.14"
/
"tracer","atmos_mod","nh4"
"longname","NH4"
"units","VMR"
"cmip","cmip6","cmip_name=ammonium,cmip_longname=ammonium,cmip_longname2=NH4"
"chem_param","aerosol","mw=18,nb_N_red=1,frac_pm1=0.92,frac_pm25=0.973,frac_pm10=1."
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","aerosol_below","frac_incloud=0.33, frac_incloud_uw=0.44, frac_incloud_snowh=0.11, frac_incloud_snow=0.,alphar=0.001, alphas=0.001"
"dry_deposition","williams_wind_driven land:dynamic","surfr=400.,icer=1000."
"convection","all"
/
"tracer","atmos_mod","hcl"
"longname","HCl"
"cmip","cmip6","cmip_name=hydrogen_chloride"
"units","VMR"
"wet_deposition","henry_below_noice","henry=3.19e6,dependence=8700."
"dry_deposition","file","name=hno3"
"init_conc", "file"
"convection","all"
/
"tracer","atmos_mod","hocl"
"longname","HOCl"
"units","VMR"
"init_conc", "file"
"convection","all"
/
"tracer","atmos_mod","clono2"
"longname","ClONO2"
"chem_param","gas","nb_N_ox=1"
"units","VMR"
"init_conc", "file"
"convection","all"
/
"tracer","atmos_mod","cl"
"longname","Cl"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"convection","all"
/
"tracer","atmos_mod","clo"
"longname","ClO"
"units","VMR"
"init_conc", "file"
"convection","all"
/
"tracer","atmos_mod","cl2o2"
"longname","Cl2O2"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"convection","all"
/
"tracer","atmos_mod","cl2"
"longname","Cl2"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"convection","all"
/
"tracer","atmos_mod","hobr"
"longname","HOBr"
"units","VMR"
"init_conc", "file"
"dry_deposition","file"
"convection","all"
/
"tracer","atmos_mod","hbr"
"longname","HBr"
"units","VMR"
"wet_deposition","henry_below_noice","henry=3.19e6,dependence=8700."
"dry_deposition","file"
"init_conc", "file"
"convection","all"
/
"tracer","atmos_mod","brono2"
"longname","BrONO2"
"chem_param","gas","mw=14.,nb_N_ox=1"
"units","VMR"
"init_conc", "file"
"dry_deposition","file","brno3"
"convection","all"
/
"tracer","atmos_mod","br"
"longname","Br"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"convection","all"
/
"tracer","atmos_mod","bro"
"longname","bro"
"units","VMR"
"init_conc", "file"
"convection","all"
/
"tracer","atmos_mod","brcl"
"longname","BrCl"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"convection","all"
/
"tracer","atmos_mod","h"
"longname","H"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","age"
"longname","age of air"
"units","years"
"profile_type","fixed","surface_value=0.0E+00"
"init_conc", "file", "file=tracerIC.19800101.v2.nc"
"convection","all"
"adjust_mass", "false"
/
"tracer", "atmos_mod", "Extinction"
"longname", "Extinction for band 4 centred at 1 micron"
"tracer_type","diagnostic"
"units", "1/m"
/
"tracer","atmos_mod","NOy"
"longname","NOy"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","Cly"
"longname","Cly"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","Bry"
"longname","Bry"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","LCH4"
"longname","CH4 loss via OH"
"units","VMR/s"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","ATO2"
"longname","ATO2(CH3C(O)CH2O2)"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","ATOOH"
"longname","ATOOH(CH3C(O)CH2OOH)"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=1.14e-1,dependence=6300."
"dry_deposition","file land:dynamic","name=ch3ooh"
"convection","all"
"chem_param","gas","mw=90."
/
"tracer","atmos_mod","GLYX"
"longname","CHOCHO"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=4.1,dependence=7500."
"dry_deposition","file land:dynamic","name=h2o2"
"convection","all"
"chem_param","gas","mw=58."
/
"tracer","atmos_mod","IEPOX"
"longname","isoprene epoxide"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=790.,dependence=0."
"dry_deposition","file land:dynamic","name=h2o2"
"convection","all"
"chem_param","gas","mw=118."
/
"tracer","atmos_mod","IEPOXOO"
"longname","IEPOXOO"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","ISN1"
"longname","ISN1"
"chem_param","gas","nb_N_ox=1"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","INO2"
"longname","INO2"
"chem_param","gas","nb_N_ox=1"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","ISNOOA"
"longname","ISNOOA"
"chem_param","gas","nb_N_ox=1"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","INPN"
"longname","O2NOCH2C(OOH)(CH3)CH=CH2"
"chem_param","gas","nb_N_ox=1"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","ISOPNB"
"longname","HOCH2C(CH3)=CHCH2ONO2"
"chem_param","gas","mw=147.,nb_N_ox=1"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=1.7e-1,dependence=9200."
"dry_deposition","file land:dynamic","name=isopnb"
"convection","all"
/
"tracer","atmos_mod","ISOPNBO2"
"longname","HOC5H7(OH)(O2)ONO2"
"chem_param","gas","nb_N_ox=1"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","MACRN"
"longname","HOCH2C(ONO2)(CH3)CHO"
"chem_param","gas","mw=149.,nb_N_ox=1"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=1.7e-1,dependence=9200."
"dry_deposition","file land:dynamic","name=hno3"
"convection","all"
/
"tracer","atmos_mod","MACRNO2"
"longname","MACRNO2"
"chem_param","gas","nb_N_ox=1"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","MAO3"
"longname","CH2=C(CH3)C(O)OO"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","MAOP"
"longname","CH2=C(CH3)C(O)OOH"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","MAOPO2"
"longname","MAOPO2"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","MEK"
"longname","RC(O)R"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","MGLY"
"longname","CH3COCHO"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=0.035,dependence=7500."
"dry_deposition","file land:dynamic","name=h2o2"
"convection","all"
"chem_param","gas","mw=72."
/
"tracer","atmos_mod","MVKN"
"longname","HOCH2CH(ONO2)C(O)CH3"
"chem_param","gas","mw=149.,nb_N_ox=1"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=1.7e-1,dependence=9200."
"dry_deposition","file land:dynamic","name=hno3"
"convection","all"
/
"tracer","atmos_mod","MVKO2"
"longname","HOCH2CH(O2)C(O)CH3"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","MVKOOH"
"longname","HOCH2CH(OOH)C(O)CH3"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","R4N1"
"longname","RO2fromR4N2"
"chem_param","gas","mw=14.,nb_N_ox=1"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=2.1e0,dependence=8700."
"dry_deposition","file","name=hno3"
"convection","all"
/
"tracer","atmos_mod","R4N2"
"longname","O2NOCH2CH(OO)CH3"
"chem_param","gas","mw=14.,nb_N_ox=1"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"wet_deposition","henry_below_noice","henry=0.17,dependence=9200."
"dry_deposition","file land:dynamic","name=hno3"
"convection","all"
"chem_param","gas","mw=149."
/
"tracer","atmos_mod","RCHO"
"longname","RCHO"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","ROH"
"longname","ROH"
"units","VMR"
"tracer_type","diagnostic"
"profile_type","fixed","surface_value=1.e-20"
/
"tracer","atmos_mod","o3s"
"longname","O3S"
"units","VMR"
"dry_deposition","file land:dynamic","name=o3,diurnal=yes"
"profile_type","fixed","surface_value=1.e-20"
"convection","all"
"chem_param","gas","mw=48."
/
 "TRACER", "atmos_mod", "HNO3_D1"
           "longname", "HNO3_D1 tracer"
           "units", "vmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=0.1e-6, rb=1.0e-6, dustref=0.75e-6, dustden=2500.0"
           #"emission", "prescribed", "source_fraction=0.1"
           "convection", "all"
           "dry_deposition","williams_wind_driven","surfr=200.,icer=1000."
	   "wet_deposition","aerosol_below","frac_incloud=0.2, frac_incloud_uw=0.3, frac_incloud_snow=0.05, alphar=0.001, alphas=0.001"
	   "chem_param","aerosol","mw=62,nb_N_ox=1,frac_pm1=0.,frac_pm25=0.,frac_pm10=0."
/
 "TRACER", "atmos_mod", "HNO3_D2"
           "longname", "HNO3_D2 tracer"
           "units", "vmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=1.0e-6, rb=2.0e-6, dustref=1.5e-6, dustden=2650.0"
           #"emission", "prescribed", "source_fraction=0.225"
           "convection", "all"
           "dry_deposition","williams_wind_driven","surfr=100.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.2, frac_incloud_uw=0.3, frac_incloud_snow=0.05, alphar=0.001, alphas=0.001"
	   "chem_param","aerosol","mw=62,nb_N_ox=1,frac_pm1=0.,frac_pm25=0.,frac_pm10=0."
/
 "TRACER", "atmos_mod", "HNO3_D3"
           "longname", "HNO3_D3 tracer"
           "units", "vmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=2.0e-6, rb=3.0e-6, dustref=2.5e-6, dustden=2650.0"
           #"emission", "prescribed", "source_fraction=0.225"
           "convection", "all"
           "dry_deposition","williams_wind_driven","surfr=100.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.2, frac_incloud_uw=0.3, frac_incloud_snow=0.05, alphar=0.001, alphas=0.001"
	   "chem_param","aerosol","mw=62,nb_N_ox=1,frac_pm1=0.,frac_pm25=0.,frac_pm10=0."
/
 "TRACER", "atmos_mod", "HNO3_D4"
           "longname", "HNO3_D4 tracer"
           "units", "vmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=3.0e-6, rb=6.0e-6, dustref=4.5e-6, dustden=2650.0"
           #"emission", "prescribed", "source_fraction=0.225"
           "convection", "all"
           "dry_deposition","williams_wind_driven","surfr=100.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.2, frac_incloud_uw=0.3, frac_incloud_snow=0.05, alphar=0.001, alphas=0.001"
	   "chem_param","aerosol","mw=62,nb_N_ox=1,frac_pm1=0.,frac_pm25=0.,frac_pm10=0."
/
 "TRACER", "atmos_mod", "HNO3_D5"
           "longname", "HNO3_D5 tracer"
           "units", "vmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=6.0e-6, rb=10.0e-6, dustref=8e-6, dustden=2650.0"
           #"emission", "prescribed", "source_fraction=0.225"
           "convection", "all"
           "dry_deposition","williams_wind_driven","surfr=100.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.2, frac_incloud_uw=0.3, frac_incloud_snow=0.05, alphar=0.001, alphas=0.001"
	   "chem_param","aerosol","mw=62,nb_N_ox=1,frac_pm1=0.,frac_pm25=0.,frac_pm10=0."
/
 "TRACER", "atmos_mod", "SO4_D1"
           "longname", "SO4_D1 tracer"
           "units", "vmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=0.1e-6, rb=1.0e-6, dustref=0.75e-6, dustden=2500.0"
           #"emission", "prescribed", "source_fraction=0.1"
           "convection", "all"
           "dry_deposition","williams_wind_driven","surfr=200.,icer=1000."
	   "wet_deposition","aerosol_below","frac_incloud=0.2, frac_incloud_uw=0.3, frac_incloud_snow=0.05, alphar=0.001, alphas=0.001"
/
 "TRACER", "atmos_mod", "SO4_D2"
           "longname", "SO4_D2 tracer"
           "units", "vmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=1.0e-6, rb=2.0e-6, dustref=1.5e-6, dustden=2650.0"
           #"emission", "prescribed", "source_fraction=0.225"
           "convection", "all"
           "dry_deposition","williams_wind_driven","surfr=100.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.2, frac_incloud_uw=0.3, frac_incloud_snow=0.05, alphar=0.001, alphas=0.001"
/
 "TRACER", "atmos_mod", "SO4_D3"
           "longname", "SO4_D3 tracer"
           "units", "vmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=2.0e-6, rb=3.0e-6, dustref=2.5e-6, dustden=2650.0"
           #"emission", "prescribed", "source_fraction=0.225"
           "convection", "all"
           "dry_deposition","williams_wind_driven","surfr=100.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.2, frac_incloud_uw=0.3, frac_incloud_snow=0.05, alphar=0.001, alphas=0.001"
/
 "TRACER", "atmos_mod", "SO4_D4"
           "longname", "SO4_D4 tracer"
           "units", "vmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=3.0e-6, rb=6.0e-6, dustref=4.5e-6, dustden=2650.0"
           #"emission", "prescribed", "source_fraction=0.225"
           "convection", "all"
           "dry_deposition","williams_wind_driven","surfr=100.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.2, frac_incloud_uw=0.3, frac_incloud_snow=0.05, alphar=0.001, alphas=0.001"
/
 "TRACER", "atmos_mod", "SO4_D5"
           "longname", "SO4_D5 tracer"
           "units", "vmr"
           "profile_type","fixed","surface_value=1.e-32"
           "parameters", "all", "ra=6.0e-6, rb=10.0e-6, dustref=8e-6, dustden=2650.0"
           #"emission", "prescribed", "source_fraction=0.225"
           "convection", "all"
           "dry_deposition","williams_wind_driven","surfr=100.,icer=1000."
           "wet_deposition","aerosol_below","frac_incloud=0.2, frac_incloud_uw=0.3, frac_incloud_snow=0.05, alphar=0.001, alphas=0.001"
/
# Tagged O3S_E90
"tracer","atmos_mod","e90"
"longname","E90"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"convection","all"
"emissions","file","file=emissions.e90.surface.1x1.nc"
/
"tracer","atmos_mod","o3s_e90"
"longname","O3S_E90"
"cmip","cmip6","cmip_name=ozone,cmip_longname=Ozone"
"units","VMR"
"chem_param","gas","mw=48."
"dry_deposition","file land:dynamic","name=o3,diurnal=yes"
"profile_type","fixed","surface_value=1.e-20"
"convection",   "all"
/
"tracer","atmos_mod","aoanh"
"longname","Northern Hemisphere tracer"
"units","years"
"profile_type","fixed","surface_value=1.e-20"
"convection",   "all"
"adjust_mass", "false"
/
"tracer","atmos_mod","nh50"
"longname","Northern Hemisphere tracer"
"cmip","cmip6","cmip_name=artificial_tracer_with_fixed_lifetime"
"units","VMR"
"profile_type","fixed","surface_value=1.e-20"
"convection",   "all"
/
####.................................................
### ESM atmos co2 field table for CMIP6 Jan 1 1850
## jgj 2016/11/29
# CO2 tracer
## Note: atm transport and land model expect moist mmr.
##       set co2 units: kg/kg  (mass mixing ratio) for both atm and lnd field table entries.
##       convert atm IC field table entry from dry vmr value to **dry** mmr
## Note: for atm cold start from constant co2 value, instead of using field table to initialize co2,
##       create atmos_tracers.res.nc with co2 moist mmr values
##       WTMAIR = 2.896440E+01 WTMCO2   =  44.00995
##       CMIP6 Jan 1 1850 co2 = 284.262e-6
#
 "TRACER", "atmos_mod",    "co2"
           "longname",     "carbon dioxide"
           "units",        "kg/kg"
           "cmip","cmip6","cmip_name=carbon_dioxide"
           "chem_param","gas","mw=44."
           "convection",   "all"
           "lower_bound","file","file=co2_gblannualdata,factor=1.e-9"
###.................................................
### COBALT field table for initializing tracers
## jgj 2013/01/23 updated for COBALT
## jgj 2018/05/09 updated for GLODAP v2 and regridded COBALT history file
"namelists","ocean_mod","generic_cobalt/*global*"
/
"namelists","ocean_mod","generic_cobalt"
enforce_src_info = t
pcmlim_aclm_ndi_requires_src_info = f
pcmlim_aclm_nlg_requires_src_info = f
pcmlim_aclm_nmd_requires_src_info = f
pcmlim_aclm_nsm_requires_src_info = f
pcmlim_aclm_ndi_requires_restart = f
pcmlim_aclm_nlg_requires_restart = f
pcmlim_aclm_nmd_requires_restart = f
pcmlim_aclm_nsm_requires_restart = f
pdet_fast_requires_src_info = f
ndet_fast_requires_src_info = f
pdet_fast_btf_requires_src_info = f
ndet_fast_btf_requires_src_info = f
pdet_fast_requires_restart = f
ndet_fast_requires_restart = f
pdet_fast_btf_requires_restart = f
ndet_fast_btf_requires_restart = f

#
# JGJ 2015/07/28
# field table entries for initialization of cobalt tracers
# all unit conversions will be specified in the code based on
# valid src_var_unit and internal model unit.
# If field table src_var_unit does not match valid src_var_unit
# in code, model will give fatal error.
# valid src_var_units:
#    NO3, PO4, SiO4    : micromoles_per_liter
#    O2                : milliliters_per_liter
#    DIC, ALK          : micromoles_per_kg
#    all other fields  : none
# valid src_var_record : 0-12, where 0 is Annual, 1-12 for Jan-Dec
# 2015/10/05: Use annual data for WOA13 N, P, Si, O2 since monthly data does not extend to depth
# airsea and ice_ocean fluxes are handled by coupler, so are initialized in COBALT.
#
# 2015/09/28 jgj updated to provide valid_min, valid_max for tracers to ensure
# tracers remain positive after interpolation
# note that values of valid_min and valid_max are in model units not src_units
# currently only alk, dic and htotal have both a valid_min and valid_max
# specified in field_table, but valid_max is ignored for now by code.
# as of 2015/10/06 src_var_record and src_var_gridspec are not yet implemented
#
# 2015/10/14 change valid_min for alk and dic to 0 since land values get filled with valid_min
#            also remove valid_max for alk and dic
#
#------------------------------------------------------------------------------------------------
#
# NO3 from WOA2013  (/archive/mdteam/obs/NOAA-NODC/WOA13/v1.00a/woa13_all_n_annual_01.nc)
# min = 0, max = 65.08 from input dataset
# divide by 1035e3 to convert from umol/l to mol/kg
no3_src_file = INPUT/woa13_all_n_annual_01.nc
no3_src_var_name = n_an
no3_src_var_unit = micromoles_per_liter
no3_dest_var_name =  no3
no3_dest_var_unit = mol kg-1
no3_src_var_record = 1
no3_src_var_gridspec = NONE
no3_valid_min = 0.0
#
# O2 from WOA2013  (/archive/mdteam/obs/NOAA-NODC/WOA13/v1.00a/woa13_all_o_annual_01.nc)
# min = 0, max = 15.44 from input dataset
# multiply by (1000/22391.6)/1035 to convert from ml/l to mol/kg
o2_src_file = INPUT/woa13_all_o_annual_01.nc
o2_src_var_name = o_an
o2_src_var_unit = milliliters_per_liter
o2_dest_var_name =  o2
o2_dest_var_unit = mol kg-1
o2_src_var_record = 1
o2_src_var_gridspec = NONE
o2_valid_min = 0.0
#
# PO4 from WOA2013  (/archive/mdteam/obs/NOAA-NODC/WOA13/v1.00a/woa13_all_p_annual_01.nc)
# min = 0, max = 9.757 from input dataset
# divide by 1035e3 to convert from umol/l to mol/kg
po4_src_file = INPUT/woa13_all_p_annual_01.nc
po4_src_var_name = p_an
po4_src_var_unit = micromoles_per_liter
po4_dest_var_name =  po4
po4_dest_var_unit = mol kg-1
po4_src_var_record = 1
po4_src_var_gridspec = NONE
po4_valid_min = 0.0
#
# SIO4 from WOA2013  (/archive/mdteam/obs/NOAA-NODC/WOA13/v1.00a/woa13_all_i_annual_01.nc)
# min = 0, max = 267.3 from input dataset
# divide by 1035e3 to convert from umol/l to mol/kg
sio4_src_file = INPUT/woa13_all_i_annual_01.nc
sio4_src_var_name = i_an
sio4_src_var_unit = micromoles_per_liter
sio4_dest_var_name =  sio4
sio4_dest_var_unit = mol kg-1
sio4_src_var_record = 1
sio4_src_var_gridspec = NONE
sio4_valid_min = 0.0
#
# Alkalinity from GLODAPv2  (/lustre/f2/pdata/gfdl/cmip6/datasets/ESM4/OBGC/GLODAPv2/GLODAPv2.2016b.oi-filled.20180322.nc)
# divide by 1e6 to convert from umol/kg to mol/kg
alk_src_file = INPUT/GLODAPv2.2016b.oi-filled.20180322.nc
alk_src_var_name = TAlk
alk_src_var_unit = micromoles_per_kg
alk_dest_var_name =  alk
alk_dest_var_unit = mol kg-1
alk_src_var_record = 1
alk_src_var_gridspec = NONE
alk_valid_min = 0.0
#
# Preind DIC from GLODAPv2  (/lustre/f2/pdata/gfdl/cmip6/datasets/ESM4/OBGC/GLODAPv2/GLODAPv2.2016b.oi-filled.20180322.nc)
# divide by 1e6 to convert from umol/kg to mol/kg
dic_src_file = INPUT/GLODAPv2.2016b.oi-filled.20180322.nc
dic_src_var_name = PI_TCO2
dic_src_var_unit = micromoles_per_kg
dic_dest_var_name =  dic
dic_dest_var_unit = mol kg-1
dic_src_var_record = 1
dic_src_var_gridspec = NONE
dic_valid_min = 0.0
#
# additional tracers from ESM4p-COBALT Preindustrial Control history file 
# no unit conversion necessary
cadet_arag_src_file = INPUT/init_ocean_cobalt.res.nc
cadet_arag_src_var_name = cadet_arag
cadet_arag_src_var_unit = none
cadet_arag_dest_var_name =  cadet_arag
cadet_arag_dest_var_unit = mol kg-1
cadet_arag_src_var_record = 1
cadet_arag_src_var_gridspec = NONE
cadet_arag_valid_min = 0.0
#
cadet_calc_src_file = INPUT/init_ocean_cobalt.res.nc
cadet_calc_src_var_name = cadet_calc
cadet_calc_src_var_unit = none
cadet_calc_dest_var_name =  cadet_calc
cadet_calc_dest_var_unit = mol kg-1
cadet_calc_src_var_record = 1
cadet_calc_src_var_gridspec = NONE
cadet_calc_valid_min = 0.0
#
# NOTE: CASED = 0 at all K except K=1 from input dataset
cased_src_file = INPUT/init_ocean_cobalt.res.nc
cased_src_var_name = cased
cased_src_var_unit = none
cased_dest_var_name =  cased
cased_dest_var_unit = mol kg-1
cased_src_var_record = 1
cased_src_var_gridspec = NONE
cased_valid_min = 0.0
#
chl_src_file = INPUT/init_ocean_cobalt.res.nc
chl_src_var_name = chl
chl_src_var_unit = none
chl_dest_var_name =  chl
chl_dest_var_unit = mol kg-1
chl_src_var_record = 1
chl_src_var_gridspec = NONE
chl_valid_min = 0.0
#
co3_ion_src_file = INPUT/init_ocean_cobalt.res.nc
co3_ion_src_var_name = co3_ion
co3_ion_src_var_unit = none
co3_ion_dest_var_name =  co3_ion
co3_ion_dest_var_unit = mol kg-1
co3_ion_src_var_record = 1
co3_ion_src_var_gridspec = NONE
co3_ion_valid_min = 0.0
#
fed_src_file = INPUT/init_ocean_cobalt.res.nc
fed_src_var_name = fed
fed_src_var_unit = none
fed_dest_var_name =  fed
fed_dest_var_unit = mol kg-1
fed_src_var_record = 1
fed_src_var_gridspec = NONE
fed_valid_min = 0.0
#
fedi_src_file = INPUT/init_ocean_cobalt.res.nc
fedi_src_var_name = fedi
fedi_src_var_unit = none
fedi_dest_var_name =  fedi
fedi_dest_var_unit = mol kg-1
fedi_src_var_record = 1
fedi_src_var_gridspec = NONE
fedi_valid_min = 0.0
#
felg_src_file = INPUT/init_ocean_cobalt.res.nc
felg_src_var_name = felg
felg_src_var_unit = none
felg_dest_var_name =  felg
felg_dest_var_unit = mol kg-1
felg_src_var_record = 1
felg_src_var_gridspec = NONE
felg_valid_min = 0.0
#
femd_src_file = INPUT/init_ocean_cobalt.res.nc
femd_src_var_name = femd
femd_src_var_unit = none
femd_dest_var_name =  femd
femd_dest_var_unit = mol kg-1
femd_src_var_record = 1
femd_src_var_gridspec = NONE
femd_valid_min = 0.0
#
fesm_src_file = INPUT/init_ocean_cobalt.res.nc
fesm_src_var_name = fesm
fesm_src_var_unit = none
fesm_dest_var_name =  fesm
fesm_dest_var_unit = mol kg-1
fesm_src_var_record = 1
fesm_src_var_gridspec = NONE
fesm_valid_min = 0.0
#
htotal_src_file = INPUT/init_ocean_cobalt.res.nc
htotal_src_var_name = htotal
htotal_src_var_unit = none
htotal_dest_var_name =  htotal
htotal_dest_var_unit = mol kg-1
htotal_src_var_record = 1
htotal_src_var_gridspec = NONE
htotal_valid_min = 3.981E-09
htotal_valid_max = 1.259E-08
# All irr_mem variables are zero everywhere.
irr_aclm_src_file = INPUT/init_ocean_cobalt.res.nc
irr_aclm_src_var_name = irr_mem
irr_aclm_src_var_unit = none
irr_aclm_dest_var_name =  irr_mem
irr_aclm_dest_var_unit = mol kg-1
irr_aclm_src_var_record = 1
irr_aclm_src_var_gridspec = NONE
irr_aclm_valid_min = 0.0
#
irr_mem_dp_src_file = INPUT/init_ocean_cobalt.res.nc
irr_mem_dp_src_var_name = irr_mem
irr_mem_dp_src_var_unit = none
irr_mem_dp_dest_var_name =  irr_mem
irr_mem_dp_dest_var_unit = mol kg-1
irr_mem_dp_src_var_record = 1
irr_mem_dp_src_var_gridspec = NONE
irr_mem_dp_valid_min = 0.0
#
irr_aclm_sfc_src_file = INPUT/init_ocean_cobalt.res.nc
irr_aclm_sfc_src_var_name = irr_mem
irr_aclm_sfc_src_var_unit = none
irr_aclm_sfc_dest_var_name =  irr_mem
irr_aclm_sfc_dest_var_unit = mol kg-1
irr_aclm_sfc_src_var_record = 1
irr_aclm_sfc_src_var_gridspec = NONE
irr_aclm_sfc_valid_min = 0.0
#
irr_aclm_z_src_file = INPUT/init_ocean_cobalt.res.nc
irr_aclm_z_src_var_name = irr_mem
irr_aclm_z_src_var_unit = none
irr_aclm_z_dest_var_name =  irr_mem
irr_aclm_z_dest_var_unit = mol kg-1
irr_aclm_z_src_var_record = 1
irr_aclm_z_src_var_gridspec = NONE
irr_aclm_z_valid_min = 0.0
#
ldon_src_file = INPUT/init_ocean_cobalt.res.nc
ldon_src_var_name = ldon
ldon_src_var_unit = none
ldon_dest_var_name =  ldon
ldon_dest_var_unit = mol kg-1
ldon_src_var_record = 1
ldon_src_var_gridspec = NONE
ldon_valid_min = 0.0
#
ldop_src_file = INPUT/init_ocean_cobalt.res.nc
ldop_src_var_name = ldop
ldop_src_var_unit = none
ldop_dest_var_name =  ldop
ldop_dest_var_unit = mol kg-1
ldop_src_var_record = 1
ldop_src_var_gridspec = NONE
ldop_valid_min = 0.0
#
lith_src_file = INPUT/init_ocean_cobalt.res.nc
lith_src_var_name = lith
lith_src_var_unit = none
lith_dest_var_name =  lith
lith_dest_var_unit = mol kg-1
lith_src_var_record = 1
lith_src_var_gridspec = NONE
lith_valid_min = 0.0
#
nh4_src_file = INPUT/init_ocean_cobalt.res.nc
nh4_src_var_name = nh4
nh4_src_var_unit = none
nh4_dest_var_name =  nh4
nh4_dest_var_unit = mol kg-1
nh4_src_var_record = 1
nh4_src_var_gridspec = NONE
nh4_valid_min = 0.0
#
nbact_src_file = INPUT/init_ocean_cobalt.res.nc
nbact_src_var_name = nbact
nbact_src_var_unit = none
nbact_dest_var_name =  nbact
nbact_dest_var_unit = mol kg-1
nbact_src_var_record = 1
nbact_src_var_gridspec = NONE
nbact_valid_min = 0.0
#
ndi_src_file = INPUT/init_ocean_cobalt.res.nc
ndi_src_var_name = ndi
ndi_src_var_unit = none
ndi_dest_var_name =  ndi
ndi_dest_var_unit = mol kg-1
ndi_src_var_record = 1
ndi_src_var_gridspec = NONE
ndi_valid_min = 0.0
#
nlg_src_file = INPUT/init_ocean_cobalt.res.nc
nlg_src_var_name = nlg
nlg_src_var_unit = none
nlg_dest_var_name =  nlg
nlg_dest_var_unit = mol kg-1
nlg_src_var_record = 1
nlg_src_var_gridspec = NONE
nlg_valid_min = 0.0
#
nmd_src_file = INPUT/init_ocean_cobalt.res.nc
nmd_src_var_name = nmd
nmd_src_var_unit = none
nmd_dest_var_name =  nmd
nmd_dest_var_unit = mol kg-1
nmd_src_var_record = 1
nmd_src_var_gridspec = NONE
nmd_valid_min = 0.0
#
nsm_src_file = INPUT/init_ocean_cobalt.res.nc
nsm_src_var_name = nsm
nsm_src_var_unit = none
nsm_dest_var_name =  nsm
nsm_dest_var_unit = mol kg-1
nsm_src_var_record = 1
nsm_src_var_gridspec = NONE
nsm_valid_min = 0.0
#
nlgz_src_file = INPUT/init_ocean_cobalt.res.nc
nlgz_src_var_name = nlgz
nlgz_src_var_unit = none
nlgz_dest_var_name =  nlgz
nlgz_dest_var_unit = mol kg-1
nlgz_src_var_record = 1
nlgz_src_var_gridspec = NONE
nlgz_valid_min = 0.0
#
nmdz_src_file = INPUT/init_ocean_cobalt.res.nc
nmdz_src_var_name = nmdz
nmdz_src_var_unit = none
nmdz_dest_var_name =  nmdz
nmdz_dest_var_unit = mol kg-1
nmdz_src_var_record = 1
nmdz_src_var_gridspec = NONE
nmdz_valid_min = 0.0
#
nsmz_src_file = INPUT/init_ocean_cobalt.res.nc
nsmz_src_var_name = nsmz
nsmz_src_var_unit = none
nsmz_dest_var_name =  nsmz
nsmz_dest_var_unit = mol kg-1
nsmz_src_var_record = 1
nsmz_src_var_gridspec = NONE
nsmz_valid_min = 0.0
#
pdi_src_file = INPUT/init_ocean_cobalt.res.nc
pdi_src_var_name = pdi
pdi_src_var_unit = none
pdi_dest_var_name =  pdi
pdi_dest_var_unit = mol kg-1
pdi_src_var_record = 1
pdi_src_var_gridspec = NONE
pdi_valid_min = 0.0
#
plg_src_file = INPUT/init_ocean_cobalt.res.nc
plg_src_var_name = plg
plg_src_var_unit = none
plg_dest_var_name =  plg
plg_dest_var_unit = mol kg-1
plg_src_var_record = 1
plg_src_var_gridspec = NONE
plg_valid_min = 0.0
#
pmd_src_file = INPUT/init_ocean_cobalt.res.nc
pmd_src_var_name = pmd
pmd_src_var_unit = none
pmd_dest_var_name =  pmd
pmd_dest_var_unit = mol kg-1
pmd_src_var_record = 1
pmd_src_var_gridspec = NONE
pmd_valid_min = 0.0
#
psm_src_file = INPUT/init_ocean_cobalt.res.nc
psm_src_var_name = psm
psm_src_var_unit = none
psm_dest_var_name =  psm
psm_dest_var_unit = mol kg-1
psm_src_var_record = 1
psm_src_var_gridspec = NONE
psm_valid_min = 0.0
#
fedet_src_file = INPUT/init_ocean_cobalt.res.nc
fedet_src_var_name = fedet
fedet_src_var_unit = none
fedet_dest_var_name =  fedet
fedet_dest_var_unit = mol kg-1
fedet_src_var_record = 1
fedet_src_var_gridspec = NONE
fedet_valid_min = 0.0
#
lithdet_src_file = INPUT/init_ocean_cobalt.res.nc
lithdet_src_var_name = lithdet
lithdet_src_var_unit = none
lithdet_dest_var_name =  lithdet
lithdet_dest_var_unit = mol kg-1
lithdet_src_var_record = 1
lithdet_src_var_gridspec = NONE
lithdet_valid_min = 0.0
#
ndet_src_file = INPUT/init_ocean_cobalt.res.nc
ndet_src_var_name = ndet
ndet_src_var_unit = none
ndet_dest_var_name =  ndet
ndet_dest_var_unit = mol kg-1
ndet_src_var_record = 1
ndet_src_var_gridspec = NONE
ndet_valid_min = 0.0
#
pdet_src_file = INPUT/init_ocean_cobalt.res.nc
pdet_src_var_name = pdet
pdet_src_var_unit = none
pdet_dest_var_name =  pdet
pdet_dest_var_unit = mol kg-1
pdet_src_var_record = 1
pdet_src_var_gridspec = NONE
pdet_valid_min = 0.0
#
sidet_src_file = INPUT/init_ocean_cobalt.res.nc
sidet_src_var_name = sidet
sidet_src_var_unit = none
sidet_dest_var_name =  sidet
sidet_dest_var_unit = mol kg-1
sidet_src_var_record = 1
sidet_src_var_gridspec = NONE
sidet_valid_min = 0.0
#
silg_src_file = INPUT/init_ocean_cobalt.res.nc
silg_src_var_name = silg
silg_src_var_unit = none
silg_dest_var_name =  silg
silg_dest_var_unit = mol kg-1 
silg_src_var_record = 1
silg_src_var_gridspec = NONE
silg_valid_min = 0.0
#
simd_src_file = INPUT/init_ocean_cobalt.res.nc
simd_src_var_name = simd
simd_src_var_unit = none
simd_dest_var_name =  simd
simd_dest_var_unit = mol kg-1
simd_src_var_record = 1
simd_src_var_gridspec = NONE
simd_valid_min = 0.0
#
sldon_src_file = INPUT/init_ocean_cobalt.res.nc
sldon_src_var_name = sldon
sldon_src_var_unit = none
sldon_dest_var_name =  sldon
sldon_dest_var_unit = mol kg-1
sldon_src_var_record = 1
sldon_src_var_gridspec = NONE
sldon_valid_min = 0.0
#
sldop_src_file = INPUT/init_ocean_cobalt.res.nc
sldop_src_var_name = sldop
sldop_src_var_unit = none
sldop_dest_var_name =  sldop
sldop_dest_var_unit = mol kg-1
sldop_src_var_record = 1
sldop_src_var_gridspec = NONE
sldop_valid_min = 0.0
#
srdon_src_file = INPUT/init_ocean_cobalt.res.nc
srdon_src_var_name = srdon
srdon_src_var_unit = none
srdon_dest_var_name =  srdon
srdon_dest_var_unit = mol kg-1
srdon_src_var_record = 1
srdon_src_var_gridspec = NONE
srdon_valid_min = 0.0
#
srdop_src_file = INPUT/init_ocean_cobalt.res.nc
srdop_src_var_name = srdop
srdop_src_var_unit = none
srdop_dest_var_name =  srdop
srdop_dest_var_unit = mol kg-1
srdop_src_var_record = 1
srdop_src_var_gridspec = NONE
srdop_valid_min = 0.0
#
cadet_arag_btf_src_file = INPUT/init_ocean_cobalt.res.nc
cadet_arag_btf_src_var_name = cadet_arag_btf
cadet_arag_btf_src_var_unit = none
cadet_arag_btf_dest_var_name =  cadet_arag_btf
cadet_arag_btf_dest_var_unit = mol kg-1
cadet_arag_btf_src_var_record = 1
cadet_arag_btf_src_var_gridspec = NONE
cadet_arag_btf_valid_min = 0.0
#
cadet_calc_btf_src_file = INPUT/init_ocean_cobalt.res.nc
cadet_calc_btf_src_var_name = cadet_calc_btf
cadet_calc_btf_src_var_unit = none
cadet_calc_btf_dest_var_name =  cadet_calc_btf
cadet_calc_btf_dest_var_unit = mol kg-1
cadet_calc_btf_src_var_record = 1
cadet_calc_btf_src_var_gridspec = NONE
cadet_calc_btf_valid_min = 0.0
#
lithdet_btf_src_file = INPUT/init_ocean_cobalt.res.nc
lithdet_btf_src_var_name = lithdet_btf
lithdet_btf_src_var_unit = none
lithdet_btf_dest_var_name =  lithdet_btf
lithdet_btf_dest_var_unit = mol kg-1
lithdet_btf_src_var_record = 1
lithdet_btf_src_var_gridspec = NONE
lithdet_btf_valid_min = 0.0
#
ndet_btf_src_file = INPUT/init_ocean_cobalt.res.nc
ndet_btf_src_var_name = ndet_btf
ndet_btf_src_var_unit = none
ndet_btf_dest_var_name =  ndet_btf
ndet_btf_dest_var_unit = mol kg-1
ndet_btf_src_var_record = 1
ndet_btf_src_var_gridspec = NONE
ndet_btf_valid_min = 0.0
#
pdet_btf_src_file = INPUT/init_ocean_cobalt.res.nc
pdet_btf_src_var_name = pdet_btf
pdet_btf_src_var_unit = none
pdet_btf_dest_var_name =  pdet_btf
pdet_btf_dest_var_unit = mol kg-1
pdet_btf_src_var_record = 1
pdet_btf_src_var_gridspec = NONE
pdet_btf_valid_min = 0.0
#
sidet_btf_src_file = INPUT/init_ocean_cobalt.res.nc
sidet_btf_src_var_name = sidet_btf
sidet_btf_src_var_unit = none
sidet_btf_dest_var_name =  sidet_btf
sidet_btf_dest_var_unit = mol kg-1
sidet_btf_src_var_record = 1
sidet_btf_src_var_gridspec = NONE
sidet_btf_valid_min = 0.0
#
mu_mem_ndi_src_file = INPUT/init_ocean_cobalt.res.nc
mu_mem_ndi_src_var_name = mu_mem_ndi
mu_mem_ndi_src_var_unit = none
mu_mem_ndi_dest_var_name =  mu_mem_ndi
mu_mem_ndi_dest_var_unit = mol kg-1
mu_mem_ndi_src_var_record = 1
mu_mem_ndi_src_var_gridspec = NONE
mu_mem_ndi_valid_min = 0.0
#
mu_mem_nlg_src_file = INPUT/init_ocean_cobalt.res.nc
mu_mem_nlg_src_var_name = mu_mem_nlg
mu_mem_nlg_src_var_unit = none
mu_mem_nlg_dest_var_name =  mu_mem_nlg
mu_mem_nlg_dest_var_unit = mol kg-1
mu_mem_nlg_src_var_record = 1
mu_mem_nlg_src_var_gridspec = NONE
mu_mem_nlg_valid_min = 0.0
#
mu_mem_nmd_src_file = INPUT/init_ocean_cobalt.res.nc
mu_mem_nmd_src_var_name = mu_mem_nmd
mu_mem_nmd_src_var_unit = none
mu_mem_nmd_dest_var_name =  mu_mem_nmd
mu_mem_nmd_dest_var_unit = mol kg-1
mu_mem_nmd_src_var_record = 1
mu_mem_nmd_src_var_gridspec = NONE
mu_mem_nmd_valid_min = 0.0
#
mu_mem_nsm_src_file = INPUT/init_ocean_cobalt.res.nc
mu_mem_nsm_src_var_name = mu_mem_nsm
mu_mem_nsm_src_var_unit = none
mu_mem_nsm_dest_var_name =  mu_mem_nsm
mu_mem_nsm_dest_var_unit = mol kg-1
mu_mem_nsm_src_var_record = 1
mu_mem_nsm_src_var_gridspec = NONE
mu_mem_nsm_valid_min = 0.0
#
fedet_btf_src_file = INPUT/init_ocean_cobalt.res.nc
fedet_btf_src_var_name = fedet_btf
fedet_btf_src_var_unit = none
fedet_btf_dest_var_name =  fedet_btf
fedet_btf_dest_var_unit = mol kg-1
fedet_btf_src_var_record = 1
fedet_btf_src_var_gridspec = NONE
fedet_btf_valid_min = 0.0
#
ndi_btf_src_file = INPUT/init_ocean_cobalt.res.nc
ndi_btf_src_var_name = ndet_btf
ndi_btf_src_var_unit = none
ndi_btf_dest_var_name =  ndet_btf
ndi_btf_dest_var_unit = mol kg-1
ndi_btf_src_var_record = 1
ndi_btf_src_var_gridspec = NONE
ndi_btf_valid_min = 0.0
#
# all _btf variables are zero everywhere,
# so new _btf variables can be sourced from any existing.
pdi_btf_src_file = INPUT/init_ocean_cobalt.res.nc
pdi_btf_src_var_name = ndet_btf
pdi_btf_src_var_unit = none
pdi_btf_dest_var_name =  pdi_btf
pdi_btf_dest_var_unit = mol kg-1
pdi_btf_src_var_record = 1
pdi_btf_src_var_gridspec = NONE
pdi_btf_valid_min = 0.0
#
nsm_btf_src_file = INPUT/init_ocean_cobalt.res.nc
nsm_btf_src_var_name = ndet_btf
nsm_btf_src_var_unit = none
nsm_btf_dest_var_name =  ndet_btf
nsm_btf_dest_var_unit = mol kg-1
nsm_btf_src_var_record = 1
nsm_btf_src_var_gridspec = NONE
nsm_btf_valid_min = 0.0
#
psm_btf_src_file = INPUT/init_ocean_cobalt.res.nc
psm_btf_src_var_name = ndet_btf
psm_btf_src_var_unit = none
psm_btf_dest_var_name =  pdi_btf
psm_btf_dest_var_unit = mol kg-1
psm_btf_src_var_record = 1
psm_btf_src_var_gridspec = NONE
psm_btf_valid_min = 0.0
#
nmd_btf_src_file = INPUT/init_ocean_cobalt.res.nc
nmd_btf_src_var_name = ndet_btf
nmd_btf_src_var_unit = none
nmd_btf_dest_var_name =  ndet_btf
nmd_btf_dest_var_unit = mol kg-1
nmd_btf_src_var_record = 1
nmd_btf_src_var_gridspec = NONE
nmd_btf_valid_min = 0.0
#
pmd_btf_src_file = INPUT/init_ocean_cobalt.res.nc
pmd_btf_src_var_name = ndet_btf
pmd_btf_src_var_unit = none
pmd_btf_dest_var_name =  pmd_btf
pmd_btf_dest_var_unit = mol kg-1
pmd_btf_src_var_record = 1
pmd_btf_src_var_gridspec = NONE
pmd_btf_valid_min = 0.0
#
nlg_btf_src_file = INPUT/init_ocean_cobalt.res.nc
nlg_btf_src_var_name = ndet_btf
nlg_btf_src_var_unit = none
nlg_btf_dest_var_name =  ndet_btf
nlg_btf_dest_var_unit = mol kg-1
nlg_btf_src_var_record = 1
nlg_btf_src_var_gridspec = NONE
nlg_btf_valid_min = 0.0
#
plg_btf_src_file = INPUT/init_ocean_cobalt.res.nc
plg_btf_src_var_name = ndet_btf
plg_btf_src_var_unit = none
plg_btf_dest_var_name =  plg_btf
plg_btf_dest_var_unit = mol kg-1
plg_btf_src_var_record = 1
plg_btf_src_var_gridspec = NONE
plg_btf_valid_min = 0.0
#
fedi_btf_src_file = INPUT/init_ocean_cobalt.res.nc
fedi_btf_src_var_name = fedet_btf
fedi_btf_src_var_unit = none
fedi_btf_dest_var_name =  fedet_btf
fedi_btf_dest_var_unit = mol kg-1
fedi_btf_src_var_record = 1
fedi_btf_src_var_gridspec = NONE
fedi_btf_valid_min = 0.0
#
fesm_btf_src_file = INPUT/init_ocean_cobalt.res.nc
fesm_btf_src_var_name = fedet_btf
fesm_btf_src_var_unit = none
fesm_btf_dest_var_name =  fedet_btf
fesm_btf_dest_var_unit = mol kg-1
fesm_btf_src_var_record = 1
fesm_btf_src_var_gridspec = NONE
fesm_btf_valid_min = 0.0
#
femd_btf_src_file = INPUT/init_ocean_cobalt.res.nc
femd_btf_src_var_name = fedet_btf
femd_btf_src_var_unit = none
femd_btf_dest_var_name =  fedet_btf
femd_btf_dest_var_unit = mol kg-1
femd_btf_src_var_record = 1
femd_btf_src_var_gridspec = NONE
femd_btf_valid_min = 0.0
#
felg_btf_src_file = INPUT/init_ocean_cobalt.res.nc
felg_btf_src_var_name = fedet_btf
felg_btf_src_var_unit = none
felg_btf_dest_var_name =  fedet_btf
felg_btf_dest_var_unit = mol kg-1
felg_btf_src_var_record = 1
felg_btf_src_var_gridspec = NONE
felg_btf_valid_min = 0.0
#
simd_btf_src_file = INPUT/init_ocean_cobalt.res.nc
simd_btf_src_var_name = sidet_btf
simd_btf_src_var_unit = none
simd_btf_dest_var_name =  sidet_btf
simd_btf_dest_var_unit = mol kg-1
simd_btf_src_var_record = 1
simd_btf_src_var_gridspec = NONE
simd_btf_valid_min = 0.0
#
silg_btf_src_file = INPUT/init_ocean_cobalt.res.nc
silg_btf_src_var_name = sidet_btf
silg_btf_src_var_unit = none
silg_btf_dest_var_name =  sidet_btf
silg_btf_dest_var_unit = mol kg-1
silg_btf_src_var_record = 1
silg_btf_src_var_gridspec = NONE
silg_btf_valid_min = 0.0
#f1p-> required for cobalt new schemes + nh3 ocean/atm exchange
# min = 0,  max = 1. from input dataset
nh3_src_file = INPUT/init_ocean_cobalt_nh3.res.nc
nh3_src_var_name = nh3
nh3_src_var_unit = none
nh3_dest_var_name = nh3
nh3_dest_var_unit = mol kg-1
nh3_src_var_record = 1
nh3_src_var_gridspec = NONE
nh3_valid_min = 0.0
#
/
###........................................
# species parameters
"species", "land_mod", "default"
    csc_lai = 0.3
    dat_snow_crit = 1e7
    froot_live_c2n = 45.0
    sapwood_c2n    = 250.0
    leaf_C_retrans_frac = 0.24
    root_C_retrans_frac = 0.24
    root_N_retrans_frac = 0.2
    root_exudate_N_frac = 0.001
    dynamic_root_exudation = F
    N_fixation_rate = 4.2
    root_NH4_uptake_rate = 0.1
    root_NO3_uptake_rate = 0.1
    N_stress_root_factor = 0.0
    k_nitrate_root_uptake = 5e-3
    k_ammonium_root_uptake = 5e-3
    c2n_mycorrhizae = 10.0
    myc_N_to_plant_rate = 250.0
    myc_growth_rate = 0.3
    kM_myc_growth = 1.0e-4
    tau_nsc_exudate = 0.0
    understory_lai_factor = 0.25
    fsc_liv = 0.8, fsc_froot = 0.8, fsc_wood = 0.2
/
 "species", "land_mod", "prioria"
    long_name = prioria
    alpha_leaf =  0.5
    alpha_root = 0.8
    alpha_wood = 0.5e-01
    beta_root = 1.25
    beta_vleaf = 0.0
    beta_sapwood = 0.1e-02
    srl =    43900.0
    root_r =   0.12e-03
    LMA =   0.35e-01
    m_cond =    7.0
    Vmax =   0.3e-04
    gamma_resp =   0.10e-01
    alpha_phot = 0.04
    leaf_age_tau =    0.0
    cnst_crit_phen =   0.3
    dat_height =    19.5
    dat_root_density =    4.9
    dat_root_zeta =   0.25813
    dat_rs_min =    43.6
    allometry_type = HML
    alphaHT = 60.97697
    thetaHT = 0.8631476
    gammaHT = 0.6841742
    alphaCA = 243.7808
    thetaCA = 1.18162
    alphaBM = 0.559
    phiCSA = 0.841
    maturalage =    5.0
    seedling_height = 0.5
    prob_e =   0.4
    mortrate_d_c =   0.01429
    mortrate_d_u =   0.02301
    rho_wood =   215.95
    LAImax =   6.0
    phiRL =   1.4
    root_exudate_frac = 0.075
    Kxam = 3.0,     dx = -3.0, cx = 1.5
    Klam = 3.0E-01, dl = -3.0, cl = 1.5
    psi_tlp = -2.5
    root_perm  = 5.0e-7
    branch_wood_frac = 0.1525
    leaf_refl = 0.1, 0.45
    ROS_max = 0.22
    CC_leaf =  0.7,  CC_stem =  0.15, CC_litter =  0.5
    F_scorch_height = 0.1487
    LMA_understory_factor = 1.0, Vmax_understory_factor = 1.0, Resp_understory_factor = 1.0
    Tmin_mort = 278.16
    use_light_saber = F
    leaf_N_retrans_frac = 0.6
    r_cus = 2500.
    r_cuo = 6000.
    r_cuo_wet = 400.
    A_aer     = 5e-3
    gamma_aer = 0.58
    alpha_aer = 0.6
 /
# species parameters
"species", "land_mod", "picea"
    long_name = picea
    alpha_leaf =  0.120000000
    alpha_root = 0.5
    alpha_wood = 0.5e-01
    beta_root = 1.25
    beta_vleaf = 0.0
    beta_sapwood = 0.1e-02
    srl =    43900.0
    root_r =   0.12e-03
    LMA =   0.1
    m_cond =    7.0
    Vmax =   0.21e-04
    gamma_resp =   0.30e-01
    alpha_phot = 0.04
    growth_resp = 0.333
    NSC2targetbl = 4.0
    leaf_age_tau =    0.0
    cnst_crit_phen =   0.3
    dat_height =    19.5
    dat_root_density =    4.9
    dat_root_zeta =   0.25813
    dat_rs_min =    43.6
    allometry_type = HML
    alphaHT = 29.82898
    thetaHT = 1.45212
    gammaHT = 0.10951
    alphaCA = 111.059
    thetaCA = 1.57985
    alphaBM = 0.414
    phiCSA = 0.5364167
    maturalage =    5.0
    seedling_height = 0.5
    prob_e =   0.4
    mortrate_d_c =   0.01429
    mortrate_d_u =   0.81e-01
    rho_wood =  185.0
#   laimax was changed to its original value
    LAImax =  5.0
    phiRL =   1.4
    root_exudate_frac = 0.075
    Kxam = 3.0,     dx = -3.0, cx = 1.5
    Klam = 3.0E-01, dl = -3.0, cl = 1.5
    psi_tlp = -2.5
    root_perm  = 5.0e-7
    branch_wood_frac =  0.2065217
    phenology_type = 'evergreen'
    leaf_refl = 0.1, 0.39
    F_scorch_height = 0.11
    ROS_max = 0.3
    CC_leaf =  0.75,  CC_stem =  0.2, CC_litter =  0.55
    F_scorch_height = 0.1487
    LMA_understory_factor = 1.0, Vmax_understory_factor = 1.0, Resp_understory_factor = 1.0
    use_light_saber = F
    leaf_N_retrans_frac = 0.5
    r_cus = 2000.
    r_cuo = 4000.
    r_cuo_wet = 200
    A_aer     = 2.e-3
    gamma_aer = 0.56
    alpha_aer = 1.    
/
 "species", "land_mod", "larix"
    long_name = larix
    alpha_leaf =  0.12
    alpha_root = 0.4
    alpha_wood = 0.25e-01
    beta_root = 1.25
    beta_vleaf = 0.0
    beta_sapwood = 0.1e-02
    srl =    43900.0
    root_r =   0.12e-03
     LMA =   0.76e-01
#    LMA =   0.38e-01
    m_cond =    7.0
    Vmax =   0.17e-04
    gamma_resp =   0.35e-01
    growth_resp = 0.333
    NSC2targetbl = 4.0
    leaf_age_tau =    0.0
    cnst_crit_phen =   0.3
    gdd_crit = 180
    tc_crit = 278.15
    dat_height =    19.5
    dat_root_density =    4.9
    dat_root_zeta =   0.25813
    dat_rs_min =    43.6
    allometry_type = HML
    alphaHT = 34.88173
    thetaHT = 1.04406
    gammaHT = 0.22555
    alphaCA = 161.562
    thetaCA = 1.5814
    alphaBM = 0.366
    phiCSA = 0.5247044
    maturalage =    5.0
    seedling_height = 0.5
    prob_e =   0.4
    mortrate_d_c =   0.2e-01
    mortrate_d_u =   0.81e-01
    rho_wood =  245.0
    LAImax =   5.0
#    LAImax =   3.5
    phiRL =   1.4
#    phiRL =   0.8
    root_exudate_frac = 0.075
    Kxam = 3.0,     dx = -3.0, cx = 1.5
    Klam = 3.0E-01, dl = -3.0, cl = 1.5
    psi_tlp = -2.5
    root_perm  = 5.0e-7
#    branch_wood_frac =  0.25
     branch_wood_frac = 0.2065217
    leaf_refl = 0.1, 0.39
    F_scorch_height = 0.11
    ROS_max = 0.3
    CC_leaf =  0.75,  CC_stem =  0.2, CC_litter =  0.55
    F_scorch_height = 0.1487
    LMA_understory_factor = 1.0, Vmax_understory_factor = 1.0, Resp_understory_factor = 1.0
    use_light_saber = F
    leaf_N_retrans_frac = 0.6
    r_cus = 2000.
    r_cuo = 4000.
    r_cuo_wet = 200
    A_aer     = 2.e-3
    gamma_aer = 0.56
    alpha_aer = 1.1
/
 "species", "land_mod", "acer"
    long_name = acer
    alpha_leaf =  0.12
    alpha_root = 0.5
    alpha_wood = 0.25e-01
    beta_root = 1.25
    beta_vleaf = 0.0
    beta_sapwood = 0.1e-02
    srl =    43900.0
    root_r =   0.12e-03
    LMA =   0.38e-01
    m_cond =    7.0
    Vmax =   0.2e-04
    gamma_resp =   0.35e-01
    alpha_phot = 0.04
    growth_resp = 0.333
    NSC2targetbl = 4.0
    leaf_age_tau = 0.0
    cnst_crit_phen =   0.3
    dat_height =    19.5
    dat_root_density =    4.9
    dat_root_zeta =   0.25813
    dat_rs_min =    43.6
    allometry_type = HML
    alphaHT = 49.11781
    thetaHT = 0.7590974
    gammaHT = 0.5309686
    alphaCA = 150.0
    thetaCA = 1.5
    alphaBM = 0.3683791
    phiCSA = 0.4106051
    maturalage =    5.0
    seedling_height = 0.5
    prob_e =   0.4
    mortrate_d_c =   0.01
    mortrate_d_u =   0.81e-01
    rho_wood =   245.0
    LAImax =   3.5
    phiRL =   0.8
    leaf_refl = 0.1, 0.45
    root_exudate_frac = 0.075
    Kxam = 3.0,     dx = -3.0, cx = 1.5
    Klam = 3.0E-01, dl = -3.0, cl = 1.5
    psi_tlp = -2.5
    root_perm  = 5.0e-7
    branch_wood_frac = 0.2065217
    ROS_max = 0.22
    CC_leaf =  0.7,  CC_stem =  0.1, CC_litter =  0.45
    F_scorch_height = 0.094
    LMA_understory_factor = 1.0, Vmax_understory_factor = 1.0, Resp_understory_factor = 1.0
    use_light_saber = F
    leaf_N_retrans_frac = 0.6
    r_cus = 2500.
    r_cuo = 6000.
    r_cuo_wet=400.
    A_aer     = 5e-3
    gamma_aer = 0.56
    alpha_aer = 0.8    
/
  "species", "land_mod", "c4grass"
    long_name = Idealized C4 grass
    lifeform = grass
    physiology_type = C4
    phenology_type = deciduous
    alpha_leaf   = 2.0
    alpha_root   = 0.8
    alpha_wood   = 2.0
    beta_sapwood = 0.1e-02
    beta_root    = 1.25
    root_r =   0.12e-03
    srl = 112.0e3
#    srl = 31950.0
    LMA = 0.02655
    m_cond =    4.0
    Vmax = 0.1e-4
    gamma_resp = 0.03
    alpha_phot = 0.03
    growth_resp = 0.333
    NSC2targetbl = 4.0
    leaf_age_tau =    0.0
    cnst_crit_phen =   0.3
    dat_height =    19.5
    dat_root_density =    4.9
    dat_root_zeta =   0.35212
    dat_rs_min =    43.6
    allometry_type = HML
    alphaHT = 1.411496
    thetaHT = 2.61129
    gammaHT = 0.001410067
    alphaCA = 95.0
    thetaCA = 1.5
    alphaBM = 1.0
    rho_wood = 69.4
    phiCSA = 0.0
    maturalage =    0.0
    seedling_height = 0.1
    prob_e =   0.6
    prob_g = 0.44
    v_seed = 0.1
    mortrate_d_c =   0.14
    mortrate_d_u =   0.14
    LAImax =  2.5
    phiRL =   0.8
    root_exudate_frac = 0.075
    Kxam = 3.0,     dx = -3.0, cx = 1.5
    Klam = 3.0E-01, dl = -3.0, cl = 1.5
    psi_tlp = -2.5
    root_perm  = 5.0e-7
    branch_wood_frac = 0.0
    seedling_nsc_frac = 3.0
    leaf_refl = 0.11, 0.45
    ROS_max = 0.4
    CC_leaf       = 0.70,  CC_stem       = 0.45,  CC_litter     = 0.45
    fireMort_leaf = 0.85,  fireMort_stem = 0.0,   fireMort_root = 0.2
    LMA_understory_factor = 1.0, Vmax_understory_factor = 1.0, Resp_understory_factor = 1.0
    reproduces_in_understory = T
    limit_tussock_R = T, tussock_Ra = 0.5, tussock_Rb = 1.0
    use_light_saber = F
    leaf_N_retrans_frac = 0.7
    r_cus = 1000.
    r_cuo = 4000.
    r_cuo_wet = 200
    A_aer     = 2e-3
    gamma_aer = 0.54
    alpha_aer = 1.2
/
 "species", "land_mod", "c3grass"
    long_name = Idealized C3 grass
    lifeform = grass
    phenology_type = deciduous
    alpha_leaf   = 2.0
    alpha_root = 0.8
    alpha_wood   = 2.0
    beta_sapwood = 0.1e-02
    beta_root    = 1.25
    root_r =   0.12e-03
    srl =    150.0e3
    LMA = 0.02655
    m_cond =    7.0
    Vmax = 0.2e-4
#    gamma_resp = 0.02
    gamma_resp = 0.015
    alpha_phot = 0.06
    growth_resp = 0.333
    NSC2targetbl = 4.0
    leaf_age_tau =    0.0
    cnst_crit_phen =   0.15
    dat_height =    19.5
    dat_root_density =    4.9
    dat_root_zeta =   0.17039
    dat_rs_min =    43.6
    allometry_type = HML
    alphaHT = 1.411496
    thetaHT = 2.61129
    gammaHT = 0.001410067
    alphaCA = 95.0
    thetaCA = 1.5
    alphaBM = 1.0
    rho_wood = 69.4
    phiCSA = 0.0
    maturalage =    0.0
    seedling_height = 0.1
    prob_e =   0.6
    prob_g = 0.44
    v_seed = 0.1
    mortrate_d_c =   0.02475
    mortrate_d_u =   0.01936
    LAImax =  2.5
    phiRL =   0.8
    root_exudate_frac = 0.075
    Kxam = 3.0,     dx = -3.0, cx = 1.5
    Klam = 3.0E-01, dl = -3.0, cl = 1.5
    psi_tlp = -2.5
    root_perm  = 5.0e-7
    branch_wood_frac = 0.0
    seedling_nsc_frac = 3.0
    leaf_refl = 0.11, 0.45
    ROS_max = 0.4
    CC_leaf       = 0.70,  CC_stem       = 0.45,  CC_litter     = 0.45
    fireMort_leaf = 0.85,  fireMort_stem = 0.0,   fireMort_root = 0.2
    LMA_understory_factor = 1.0, Vmax_understory_factor = 1.0, Resp_understory_factor = 1.0
    reproduces_in_understory = T
    limit_tussock_R = T, tussock_Ra = 0.5, tussock_Rb = 1.0
    use_light_saber = F
    gdd_crit = 180
    tc_crit =  278.15
    leaf_N_retrans_frac = 0.7
    r_cus = 1000.
    r_cuo = 4000.
    r_cuo_wet = 200    
    A_aer     = 2.e-3
    gamma_aer = 0.54
    alpha_aer = 1.2    
/
