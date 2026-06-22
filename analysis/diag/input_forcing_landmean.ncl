;----------------------------------------------------------------------
; input_forcing_landmean.ncl  (run on climate00)
; Land-masked monthly area-mean of INPUT forcing (0.5°) for TBOT/FSDS/FLDS/
; PRECTmms, 1979-1987 -> small nc for "input vs CLM-received" comparison.
;----------------------------------------------------------------------
begin
  fdir = "/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM/tmp"
  dom  = "/data1/CESM2_INPUT/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516/domain.lnd.360x720_gswp3.0v1.c170606.nc"
  outf = "/data2/ydkoh/2026_MOF_LSM/diag/input_forcing_landmean.nc"
  system("mkdir -p /data2/ydkoh/2026_MOF_LSM/diag")

  yrs   = ispan(1979, 1979, 1)
  nyr   = dimsizes(yrs)
  vars  = (/"TBOT","FSDS","FLDS","PRECTmms"/)
  nv    = dimsizes(vars)

  fm    = addfile(dom, "r")
  mask2 = fm->mask                       ; (nj,ni)=(lat,lon), 1=land
  fg    = addfile(fdir+"/1979_era5.nc","r")
  lat   = fg->LATIXY(:,0)                 ; forcing has only 2D LATIXY (no 1D lat)
  wy    = cos(lat*0.01745329)            ; (lat)
  w2    = conform(mask2, wy, 0) * where(mask2.eq.1, 1.0, 0.0)   ; land area weight (lat,lon)

  ; noleap month -> 6-hourly step boundaries
  dpm = (/31,28,31,30,31,30,31,31,30,31,30,31/)
  spm = dpm*4
  st  = new(13,integer)
  st(0)=0
  do m=0,11
    st(m+1)=st(m)+spm(m)
  end do

  out = new((/nv,nyr,12/), float)
  do iv=0,nv-1
  do iy=0,nyr-1
    f = addfile(fdir+"/"+yrs(iy)+"_era5.nc","r")
    x = f->$vars(iv)$                    ; (time=1460,lat,lon)
    do m=0,11
      xm = dim_avg_n(x(st(m):st(m+1)-1,:,:), 0)    ; monthly mean (lat,lon)
      out(iv,iy,m) = sum(xm*w2)/sum(w2)            ; land area-mean
    end do
    delete([/f,x/])
    print(vars(iv)+" "+yrs(iy)+" done")
  end do
  end do

  out!0="var"
  out!1="year"
  out!2="month"
  out@vars = str_join(vars,",")
  system("/bin/rm -f "+outf)
  fo = addfile(outf,"c")
  fo->landmean = out
  print("wrote "+outf)
end
