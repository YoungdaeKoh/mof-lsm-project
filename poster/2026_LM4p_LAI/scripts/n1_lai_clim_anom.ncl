;=====================================================================
; n1_lai_clim_anom.ncl
; Monthly LAI climatology and anomaly on the common 1-degree lat/lon grid,
; same recipe for the model and the observation:
;   LM4p ctl : ../data/lm4p_ctl_lai_monthly_1979_2023.nc   (lm4p_to_latlon.py + CDO mergetime)
;   GIMMS    : ../data/gimms_lai4g_monthly_1deg_1982_2020.nc (p1_gimms_to_monthly_1deg.py)
; analysis period y1-y2 = 1982-2020 (GIMMS LAI4g ends 2020)
; climatology base c1-c2 = 1982-2010 (GIMMS starts 1982, so 1981-2010 is not possible)
; output: ../data/<name>_lai_clim_1982_2010.nc   clim (12,lat,lon)
;         ../data/<name>_lai_anom_1982_2020.nc   anom (time,lat,lon), original time coordinate
;         ../data/<name>_lai_mon_1982_2020.nc    lai  (time,lat,lon), the analysis-period series
;=====================================================================
begin

  y1 = 1982
  y2 = 2020
  c1 = 1982
  c2 = 2010

  names = (/"lm4p_ctl", "gimms"/)
  fins  = (/"../data/lm4p_ctl_lai_monthly_1979_2023.nc", "../data/gimms_lai4g_monthly_1deg_1982_2020.nc"/)

  do n = 0, dimsizes(names)-1

    fi  = addfile(fins(n), "r")
    lai = fi->lai(:,:,:)
    printVarSummary(lai)
    lai!0 = "time"
    lai!1 = "lat"
    lai!2 = "lon"
    times = cd_calendar(lai&time,-1)
    yyyy  = times/100

    tind  = ind(yyyy.ge.y1 .and. yyyy.le.y2)
    lai  := lai(tind,:,:)
    times := cd_calendar(lai&time,-1)
    yyyy  := times/100
;   print(times(0)+" - "+times(dimsizes(times)-1)+"  ntime="+dimsizes(times))

    ic   = ind(yyyy.ge.c1 .and. yyyy.le.c2)
    clim = clmMonTLL(lai(ic,:,:))
    anom = calcMonAnomTLL(lai, clim)
    clim@long_name = "LAI monthly climatology "+c1+"-"+c2
    anom@long_name = "LAI monthly anomaly from the "+c1+"-"+c2+" climatology"

;   print(names(n)+"  clim max "+max(clim)+"  anom mean over base "+avg(anom(ic,:,:)))

    fclim = "../data/"+names(n)+"_lai_clim_"+c1+"_"+c2+".nc"
    fanom = "../data/"+names(n)+"_lai_anom_"+y1+"_"+y2+".nc"
    fmon  = "../data/"+names(n)+"_lai_mon_"+y1+"_"+y2+".nc"
    system("rm -f "+fclim+" "+fanom+" "+fmon)
    fo = addfile(fclim, "c")
    fo->clim = clim
    fa = addfile(fanom, "c")
    fa->anom = anom
    fm = addfile(fmon, "c")
    fm->lai = lai

;	system("rm -f test.nc")
;	ft = addfile("test.nc","c")
;	ft->anom = anom

    delete([/fi, lai, times, yyyy, tind, ic, clim, anom, fo, fa, fm/])
  end do

end
