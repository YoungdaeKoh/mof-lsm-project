undef("setmeta")
procedure setmeta(x, ln, un, t)
begin
  x!0 = "time"
  x!1 = "lat"
  x!2 = "lon"
  if (iscoord(x,"time")) then
     delete(x&time)
  end if
  if (iscoord(x,"lat")) then
     delete(x&lat)              ; ← 추가: 1D lat 좌표 제거
  end if
  if (iscoord(x,"lon")) then
     delete(x&lon)              ; ← 추가: 1D lon 좌표 제거
  end if
  x&time = t
  delete_VarAtts(x, -1)
  x@long_name  = ln
  x@units      = un
  x@mode       = "time-dependent"
  x@_FillValue = 1.e36
end

undef("drop_feb29")
function drop_feb29(x)
; Remove Feb 29 timesteps (CLM noleap calendar). No-op for non-leap years.
local utc, keep
begin
  utc  = cd_calendar(x&time, 0)
  keep = ind(.not.(utc(:,1).eq.2 .and. utc(:,2).eq.29))
  return x(keep,:,:)
end
;----------------------------------------------------------------------
; era5_to_clm5.ncl
;
; Convert Chanhyuk ERA5 to CLM5 atmospheric forcing format.
; NCL port of era5_to_clm5.py: rename variables to CLM5 names,
; attach CLM5 long_name/units, write one NetCDF file per month.
; No unit conversion (Rainf is already mm/s); data values are copied as-is.
;
; Run on climate00 (input on /data1, output on /data2):
;   /usr/local/ncl_ncarg/6.6.2_gcc485/bin/ncl era5_to_clm5.ncl
;----------------------------------------------------------------------

begin

  era5_dir = "/data1/ERA5/single_level/hourly_0.25"
;  out_dir  = "/data2/ydkoh/ERA5_atm_forcing/clm"
  out_dir  = "./tmp/"
  system("mkdir -p " + out_dir)

  yr_start = 1987
  yr_end   = 1987

  ; CLM5 variable mapping: ERA5 name -> CLM5 name
  clm5_vars  = (/"TBOT","QBOT","PSRF","FSDS","FLDS","PRECTmms","WIND"/)



  ; ERA5 variable 
  long_names = (/"temperature at the lowest atm level", \
                 "specific humidity at the lowest atm level", \
                 "surface pressure at the lowest atm level", \
                 "total incident solar radiation", \
                 "incident longwave radiation", \
                 "PRECTmms total precipitation", \
                 "wind at the lowest atm level"/)
  units      = (/"K","kg/kg","Pa","W/m**2","W/m**2","mm H2O / sec","m/s"/)
  era5_invar = (/"t2m","d2m","sp","u10","v10","avg_sdswrf","tp","avg_sdlwrf"/)



  base = "/data1/ERA5/single_level/hourly_0.25/"
  era5_var1 = (/"2m_temperature","2m_dewpoint_temperature","surface_pressure","10m_u_component_of_wind","10m_v_component_of_wind", "mean_surface_downward_short_wave_radiation_flux","total_precipitation","mean_surface_downward_long_wave_radiation_flux"/)

  do yr = yr_start, yr_end

;;== TBOT ==;;
    yyyy     = sprinti("%0.4d", yr)
    patt := base+era5_var1(0)+"/dataset/ERA5h_"+yyyy+"????.nc"
    files := systemfunc("ls "+patt)
    fi := addfiles(files,"r")
    ListSetType(fi,"cat")
    t2m := short2flt(fi[:]->$era5_invar(0)$)
    t2m := t2m(:,::-1,:)
    t2m := drop_feb29(t2m)
	print(" "+yyyy+".. "+era5_invar(0)+" done.. ")
;;==========;;

;;== QBOT ==;;
;  era5_invar = (/"t2m","d2m","sp","u10","v10","avg_sdswrf","tp","avg_sdlwrf"/)
    patt := base+era5_var1(1)+"/dataset/ERA5h_"+yyyy+"????.nc"
    files := systemfunc("ls "+patt)
    fi := addfiles(files,"r")
    ListSetType(fi,"cat")
    d2m := short2flt(fi[:]->$era5_invar(1)$)
    d2m := d2m(:,::-1,:)
    d2m := drop_feb29(d2m)

    ;;== PSRF ==;;
    patt := base+era5_var1(2)+"/dataset/ERA5h_"+yyyy+"????.nc"
    files := systemfunc("ls "+patt)
    fi := addfiles(files,"r")
    ListSetType(fi,"cat")
    sp := short2flt(fi[:]->$era5_invar(2)$)
    sp := sp(:,::-1,:)
    sp := drop_feb29(sp)
    printVarSummary(sp)
	print(" "+yyyy+".. "+era5_invar(2)+" done.. ")


    eps = 0.621981
    e	= 611.21 * exp( 17.502*(d2m-273.16) / (d2m-32.19) )   ; Pa
    qbot = eps*e / ( sp - (1.-eps)*e )                          ; kg/kg
    copy_VarCoords(d2m, qbot)
    qbot@units = "kg/kg"
	print(" "+yyyy+".. "+era5_invar(1)+" done.. ")
;;==========;;

;;== FSDS ==;;
;  era5_invar = (/"t2m","d2m","sp","u10","v10","avg_sdswrf","tp","avg_sdlwrf"/)
    patt := base+era5_var1(5)+"/dataset/ERA5h_"+yyyy+"????.nc"
    files := systemfunc("ls "+patt)
    fi := addfiles(files,"r")
    ListSetType(fi,"cat")
    swdown := short2flt(fi[:]->$era5_invar(5)$)
    swdown := drop_feb29(swdown)

    nday = dimsizes(swdown&time)/24
    nt6  = nday*4
    sw6  = new((/nt6,dimsizes(swdown&latitude),dimsizes(swdown&longitude)/),float)
    do i=0,nt6-1
       sw6(i,:,:) = dim_avg_n_Wrap( swdown(i*6:i*6+5,:,:), 0 )   ; 6h average (flux)
    end do
    copy_VarCoords(swdown(0::6,:,:), sw6)
    sw6 := sw6(:,::-1,:)
    swdown := sw6
	print(" "+yyyy+".. "+era5_invar(3)+" done.. ")
;;==========;;

;;== FSDS ==;;
;  era5_invar = (/"t2m","d2m","sp","u10","v10","ssrd","tp","avg_sdlwrf"/)
    patt := base+era5_var1(7)+"/dataset/ERA5h_"+yyyy+"????.nc"
    files := systemfunc("ls "+patt)
    fi := addfiles(files,"r")
    ListSetType(fi,"cat")
    lwdown := short2flt(fi[:]->$era5_invar(7)$)
    lwdown := lwdown(:,::-1,:)
    lwdown := drop_feb29(lwdown)
	print(" "+yyyy+".. "+era5_invar(4)+" done.. ")
;;==========;;

;;== PRECTmms ==;;
    patt := base+era5_var1(6)+"/dataset/ERA5h_"+yyyy+"????.nc"
    files := systemfunc("ls "+patt)
    fi := addfiles(files,"r")
    ListSetType(fi,"cat")
    prec := short2flt(fi[:]->$era5_invar(6)$)
    prec := drop_feb29(prec)

    nday = dimsizes(prec&time)/24
    nt6 = nday*4
    tp6 = new((/nt6,dimsizes(prec&latitude),dimsizes(prec&longitude)/),float)
    	do i=0,nt6-1
    		tp6(i,:,:) = dim_sum_n_Wrap( prec(i*6:i*6+5,:,:),0)
    	end do
    rainf = tp6*1000./21600.
    copy_VarCoords(prec(0::6,:,:), rainf)
    rainf@units = "kg/m2/s"
    rainf := rainf(:,::-1,:)
;	printMinMax(rainf,False)
	print(" "+yyyy+".. "+era5_invar(5)+" done.. ")
;;==========;;
 
;;== WIND ==;;
;  era5_invar = (/"t2m","d2m","sp","u10","v10","ssrd","tp","avg_sdlwrf"/)
	patt := base+era5_var1(3)+"/dataset/ERA5h_"+yyyy+"????.nc"
	files := systemfunc("ls "+patt)
	fi := addfiles(files,"r")
    ListSetType(fi,"cat")
	u := short2flt(fi[:]->$era5_invar(3)$)
	u := drop_feb29(u)

	patt := base+era5_var1(4)+"/dataset/ERA5h_"+yyyy+"????.nc"
	files := systemfunc("ls "+patt)
	fi := addfiles(files,"r")
    ListSetType(fi,"cat")
	v := short2flt(fi[:]->$era5_invar(4)$)
	v := drop_feb29(v)

	wind := sqrt(u*u + v*v)
	copy_VarCoords(u, wind)
	wind := wind(:,::-1,:) 
	wind@units = "m/s"
	printMinMax(wind,False)
	print(" "+yyyy+".. "+era5_invar(6)+" done.. ")
;;==========;;









	 ; target lat-lon
	 T_grid = addfile("/data1/CESM2_INPUT/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516/TPHWL/clmforc.GSWP3.c2011.0.5x0.5.TPQWL.2010-12.nc","r")
	 T_LAT := T_grid->LATIXY(:,0)
	 T_LON := T_grid->LONGXY(0,:)
	 LONGXY = T_grid->LONGXY        ; (lat,lon) 2D
	 LATIXY = T_grid->LATIXY
	 EDGEE  = T_grid->EDGEE
	 EDGEW  = T_grid->EDGEW
	 EDGES  = T_grid->EDGES
	 EDGEN  = T_grid->EDGEN
;	 print(T_LAT)
;	 print(T_LON)


 	tbot_regrid = area_conserve_remap_Wrap(t2m&longitude, t2m&latitude, t2m, T_LON, T_LAT, False) 
 	qbot_regrid = area_conserve_remap_Wrap(qbot&longitude, qbot&latitude, qbot, T_LON, T_LAT, False) 
 	psrf_regrid = area_conserve_remap_Wrap(sp&longitude, sp&latitude, sp, T_LON, T_LAT, False) 
 	swdown_regrid = area_conserve_remap_Wrap(swdown&longitude, swdown&latitude, swdown, T_LON, T_LAT, False) 
 	lwdown_regrid = area_conserve_remap_Wrap(lwdown&longitude, lwdown&latitude, lwdown, T_LON, T_LAT, False) 
 	rainf_regrid = area_conserve_remap_Wrap(rainf&longitude, rainf&latitude, rainf, T_LON, T_LAT, False) 
 	wind_regrid = area_conserve_remap_Wrap(wind&longitude, wind&latitude, wind, T_LON, T_LAT, False) 


	; ===== time (noleap, 6-hourly) =====
	nt   = nday*4
	time = ispan(0,nt-1,1)*0.25 + 0.125
	time!0="time"
	time&time=time
	time@units="days since "+yyyy+"-01-01 00:00:00"
	time@calendar="noleap"
	time@long_name="observation time"

	setmeta(tbot_regrid,  "temperature at the lowest atm level","K",time)
	setmeta(qbot_regrid,  "specific humidity at the lowest atm level","kg/kg",time)
	setmeta(psrf_regrid,  "surface pressure at the lowest atm level","Pa",time)
	setmeta(swdown_regrid,"total incident solar radiation","W/m**2",time)
	setmeta(lwdown_regrid,"incident longwave radiation","W/m**2",time)
	setmeta(rainf_regrid, "PRECTmms total precipitation","mm H2O / sec",time)
	setmeta(wind_regrid,  "wind at the lowest atm level","m/s",time)




    ; ---- create output file ----
    outfile = out_dir + "/" +yyyy+ "_era5.nc"
	setfileoption("nc","Format","NetCDF4Classic")
    system("/bin/rm -f " + outfile)
    fout = addfile(outfile, "c")
	 fout->$clm5_vars(0)$ = tbot_regrid
	 fout->$clm5_vars(1)$ = qbot_regrid
	 fout->$clm5_vars(2)$ = psrf_regrid
	 fout->$clm5_vars(3)$ = swdown_regrid
	 fout->$clm5_vars(4)$ = lwdown_regrid
	 fout->$clm5_vars(5)$ = rainf_regrid
	 fout->$clm5_vars(6)$ = wind_regrid
	 filedimdef(fout,"time",-1,True)     ; time unlimited
	 fout->time   = time
	 fout->LONGXY = LONGXY
	 fout->LATIXY = LATIXY
	 fout->EDGEE=EDGEE
	 fout->EDGEW=EDGEW
	 fout->EDGES=EDGES
	 fout->EDGEN=EDGEN
	 fout->time = time
	 

    ; global attributes
    fAtt        = True
    fAtt@title  = "CLM5 forcing from ERA5"
    fAtt@source = "youngdaekoh@gmail.com from Sejong Univ."
    fileattdef(fout, fAtt)

	

  end do

  print("Done.")

end
