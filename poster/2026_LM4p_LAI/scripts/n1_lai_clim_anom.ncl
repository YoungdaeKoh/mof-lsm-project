;=====================================================================
; n1_lai_clim_anom.ncl
; Monthly climatology and anomaly on the common 1-degree lat/lon grid,
; same recipe for the model and the observations:
;   LM4p ctl : ../data/lm4p_ctl_<var>_monthly_1979_2023.nc  (lm4p_to_latlon.py + CDO mergetime)
;   GIMMS    : ../data/gimms_lai4g_monthly_1deg_1982_2020.nc (p1_gimms_to_monthly_1deg.py; AVHRR 1982-2003 + MODIS 2004-2020)
;   GIMMS AVHRR-only: ../data/gimms_lai4g_solely_monthly_1deg_1982_2015.nc (p1 ... solely), 1982-2015 / base 1982-2010
;   FLUXCOM-X: ../data/fluxcomx_gpp_monthly_1deg_2001_2021.nc (p2_fluxcomx_gpp_to_monthly_1deg.py)
; periods (y1-y2 analysis, c1-c2 climatology base):
;   LAI, t_ref, precip 1982-2020 / 1982-2010 (GIMMS LAI4g covers 1982-2020)
;   GPP                2001-2020 / 2001-2020 (FLUXCOM-X-BASE starts 2001)
; units: LM4p gpp kg C m-2 yr-1 -> gC m-2 d-1 (x1000/365) to match FLUXCOM-X
; output: ../data/<name>_<var>_clim_<c1>_<c2>.nc   clim (12,lat,lon)
;         ../data/<name>_<var>_anom_<y1>_<y2>.nc   anom (time,lat,lon), original time coordinate
;         ../data/<name>_<var>_mon_<y1>_<y2>.nc    <var> (time,lat,lon), the analysis-period series
;=====================================================================
begin

  names = (/"lm4p_ctl", "gimms", "lm4p_ctl", "lm4p_ctl", "lm4p_ctl", "fluxcomx", "gimms_solely"/)
  vars  = (/"lai", "lai", "t_ref", "precip", "gpp", "gpp", "lai"/)
  fins  = (/"../data/lm4p_ctl_lai_monthly_1979_2023.nc", \
            "../data/gimms_lai4g_monthly_1deg_1982_2020.nc", \
            "../data/lm4p_ctl_t_ref_monthly_1979_2023.nc", \
            "../data/lm4p_ctl_precip_monthly_1979_2023.nc", \
            "../data/lm4p_ctl_gpp_monthly_1979_2023.nc", \
            "../data/fluxcomx_gpp_monthly_1deg_2001_2021.nc", \
            "../data/gimms_lai4g_solely_monthly_1deg_1982_2015.nc"/)
  y1s   = (/1982, 1982, 1982, 1982, 2001, 2001, 1982/)
  y2s   = (/2020, 2020, 2020, 2020, 2020, 2020, 2015/)
  c1s   = (/1982, 1982, 1982, 1982, 2001, 2001, 1982/)
  c2s   = (/2010, 2010, 2010, 2010, 2020, 2020, 2010/)
  scal  = (/1., 1., 1., 1., 1000./365., 1., 1./)

  do n = 0, dimsizes(names)-1

    y1 = y1s(n)
    y2 = y2s(n)
    c1 = c1s(n)
    c2 = c2s(n)

    fi  = addfile(fins(n), "r")
    x   = fi->$vars(n)$(:,:,:)
    printVarSummary(x)
    x!0 = "time"
    x!1 = "lat"
    x!2 = "lon"
    if (scal(n).ne.1.) then
      x = x*scal(n)
      x@units = "gC m-2 d-1"
    end if
    times = cd_calendar(x&time,-1)
    yyyy  = times/100

    tind  = ind(yyyy.ge.y1 .and. yyyy.le.y2)
    x    := x(tind,:,:)
    times := cd_calendar(x&time,-1)
    yyyy  := times/100
;   print(times(0)+" - "+times(dimsizes(times)-1)+"  ntime="+dimsizes(times))

    ic   = ind(yyyy.ge.c1 .and. yyyy.le.c2)
    clim = clmMonTLL(x(ic,:,:))
    anom = calcMonAnomTLL(x, clim)
    clim@long_name = vars(n)+" monthly climatology "+c1+"-"+c2
    anom@long_name = vars(n)+" monthly anomaly from the "+c1+"-"+c2+" climatology"

;   print(names(n)+" "+vars(n)+"  clim max "+max(clim)+"  anom mean over base "+avg(anom(ic,:,:)))

    pre   = "../data/"+names(n)+"_"+vars(n)
    fclim = pre+"_clim_"+c1+"_"+c2+".nc"
    fanom = pre+"_anom_"+y1+"_"+y2+".nc"
    fmon  = pre+"_mon_"+y1+"_"+y2+".nc"
    system("rm -f "+fclim+" "+fanom+" "+fmon)
    fo = addfile(fclim, "c")
    fo->clim = clim
    fa = addfile(fanom, "c")
    fa->anom = anom
    fm = addfile(fmon, "c")
    fm->$vars(n)$ = x

;	system("rm -f test.nc")
;	ft = addfile("test.nc","c")
;	ft->anom = anom

    delete([/fi, x, times, yyyy, tind, ic, clim, anom, fo, fa, fm/])
  end do

end
