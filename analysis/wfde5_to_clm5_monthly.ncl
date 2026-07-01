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
     delete(x&lat)              ; ← 1D lat 좌표 제거 (출력은 LATIXY 2D)
  end if
  if (iscoord(x,"lon")) then
     delete(x&lon)              ; ← 1D lon 좌표 제거 (출력은 LONGXY 2D)
  end if
  x&time = t
  delete_VarAtts(x, -1)
  x@long_name  = ln
  x@units      = un
  x@mode       = "time-dependent"
  x@_FillValue = 1.e20          ; WFDE5 land-only fill (ocean = missing)
end
;----------------------------------------------------------------------
; wfde5_to_clm5_monthly.ncl
;
; era5_to_clm5_monthly.ncl 의 WFDE5 버전. 출력 구조(GSWP3 monthly 3그룹
; Solar/Precip/TPHWL, LONGXY/LATIXY/EDGE, noleap time, clmforc 파일명)는
; 그대로 보존. 입력만 ERA5 hourly -> WFDE5 6h-mean monthly 로 교체.
;
; ERA5 대비 달라진 점 (입력이 이미 LSM-ready 라서 계산이 대폭 줄어듦):
;   - 입력: /data2/ydkoh/WFDE5_6h/{Var}/{Var}_WFDE5_CRU_YYYYMM_v3.0_6h.nc
;           (이미 6h 평균, 이미 월별, 변수별 분리 파일)
;   - QBOT : WFDE5 Qair 그대로 (dewpoint->q 계산 불필요)
;   - WIND : WFDE5 Wind 그대로 (u,v->wind 계산 불필요)
;   - FSDS : WFDE5 SWdown 그대로 (6h 평균/단위환산 불필요)
;   - PRECTmms : Rainf + Snowf (둘 다 kg m-2 s-1 = mm/s; WFDE5는 비/눈 분리)
;   - grid : WFDE5 lon -180~180 -> lonFlip -> 0~360 (GSWP3 셀과 정확히 일치)
;            lat 는 이미 -89.75~89.75 ascending (ERA5처럼 ::-1 뒤집기 불필요)
;   - noleap : WFDE5는 proleptic_gregorian(윤년 2/29 존재) -> 2월 leap년은
;              앞 112스텝만 취해 2/29 제거 (mdays*4 slice)
;
; Run on climate00 (입력 /data2, 출력 /data2):
;   /usr/local/ncl_ncarg/6.6.2_gcc485/bin/ncl wfde5_to_clm5_monthly.ncl
;----------------------------------------------------------------------

begin

  w6_dir   = "/data2/ydkoh/WFDE5_6h"
  out_base = "/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5/monthly"
  system("mkdir -p " + out_base + "/Solar " + out_base + "/Precip " + out_base + "/TPHWL")

  yr_start = 1979
  yr_end   = 2024

  ; CLM5 variable mapping (참고용)
  clm5_vars = (/"TBOT","QBOT","PSRF","FSDS","FLDS","PRECTmms","WIND"/)

  ; noleap month lengths (2월 항상 28)
  mdays  = (/31,28,31,30,31,30,31,31,30,31,30,31/)
  msteps = mdays*4                                   ; 6-hourly steps / month

  ; ===== target lat-lon (GSWP3 0.5° 템플릿) =====
  T_grid = addfile("/data1/CESM2_INPUT/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516/TPHWL/clmforc.GSWP3.c2011.0.5x0.5.TPQWL.2010-12.nc","r")
  T_LAT  := T_grid->LATIXY(:,0)
  T_LON  := T_grid->LONGXY(0,:)
  LONGXY = T_grid->LONGXY        ; (lat,lon) 2D
  LATIXY = T_grid->LATIXY
  EDGEE  = T_grid->EDGEE
  EDGEW  = T_grid->EDGEW
  EDGES  = T_grid->EDGES
  EDGEN  = T_grid->EDGEN

  setfileoption("nc","Format","NetCDF4Classic")

  do yr = yr_start, yr_end
    yyyy = sprinti("%0.4d", yr)

    do mo = 0, 11
      mm  = sprinti("%0.2d", mo+1)
      nts = msteps(mo)                              ; noleap steps this month

      ; ---------- read WFDE5 6h monthly files (변수별) ----------
      f := addfile(w6_dir+"/Tair/Tair_WFDE5_CRU_"  +yyyy+mm+"_v3.0_6h.nc","r")
      tbot := f->Tair
      f := addfile(w6_dir+"/Qair/Qair_WFDE5_CRU_"  +yyyy+mm+"_v3.0_6h.nc","r")
      qbot := f->Qair
      f := addfile(w6_dir+"/PSurf/PSurf_WFDE5_CRU_"+yyyy+mm+"_v3.0_6h.nc","r")
      psrf := f->PSurf
      f := addfile(w6_dir+"/SWdown/SWdown_WFDE5_CRU_"+yyyy+mm+"_v3.0_6h.nc","r")
      swdown := f->SWdown
      f := addfile(w6_dir+"/LWdown/LWdown_WFDE5_CRU_"+yyyy+mm+"_v3.0_6h.nc","r")
      lwdown := f->LWdown
      f := addfile(w6_dir+"/Wind/Wind_WFDE5_CRU_"  +yyyy+mm+"_v3.0_6h.nc","r")
      wind := f->Wind
      f := addfile(w6_dir+"/Rainf/Rainf_WFDE5_CRU_"+yyyy+mm+"_v3.0_6h.nc","r")
      rainf := f->Rainf
      f := addfile(w6_dir+"/Snowf/Snowf_WFDE5_CRU_"+yyyy+mm+"_v3.0_6h.nc","r")
      snowf := f->Snowf

      ; PRECTmms = Rainf + Snowf  (둘 다 kg m-2 s-1 == mm/s)
      prect := rainf
      prect = rainf + snowf

      ; ---------- noleap: 2월 leap년 끝의 2/29 제거 (slice) ----------
      tbot   := tbot(0:nts-1,:,:)
      qbot   := qbot(0:nts-1,:,:)
      psrf   := psrf(0:nts-1,:,:)
      swdown := swdown(0:nts-1,:,:)
      lwdown := lwdown(0:nts-1,:,:)
      wind   := wind(0:nts-1,:,:)
      prect  := prect(0:nts-1,:,:)

      ; ---------- lon -180~180 -> 0~360 (lonFlip) ----------
      tbot   := lonFlip(tbot)
      qbot   := lonFlip(qbot)
      psrf   := lonFlip(psrf)
      swdown := lonFlip(swdown)
      lwdown := lonFlip(lwdown)
      wind   := lonFlip(wind)
      prect  := lonFlip(prect)

      ; ---------- regrid onto GSWP3 grid (셀 일치 -> identity) ----------
      tbot_regrid   = area_conserve_remap_Wrap(tbot&lon,   tbot&lat,   tbot,   T_LON, T_LAT, False)
      qbot_regrid   = area_conserve_remap_Wrap(qbot&lon,   qbot&lat,   qbot,   T_LON, T_LAT, False)
      psrf_regrid   = area_conserve_remap_Wrap(psrf&lon,   psrf&lat,   psrf,   T_LON, T_LAT, False)
      swdown_regrid = area_conserve_remap_Wrap(swdown&lon, swdown&lat, swdown, T_LON, T_LAT, False)
      lwdown_regrid = area_conserve_remap_Wrap(lwdown&lon, lwdown&lat, lwdown, T_LON, T_LAT, False)
      wind_regrid   = area_conserve_remap_Wrap(wind&lon,   wind&lat,   wind,   T_LON, T_LAT, False)
      rainf_regrid  = area_conserve_remap_Wrap(prect&lon,  prect&lat,  prect,  T_LON, T_LAT, False)

      ; ----- monthly time (noleap, 6-hourly, days since yyyy-mm-01) -----
      time := ispan(0,nts-1,1)*0.25 + 0.125
      time!0="time"
      time&time=time
      time@units="days since "+yyyy+"-"+mm+"-01 00:00:00"
      time@calendar="noleap"
      time@long_name="observation time"

      ;;== Solar: FSDS ==;;
      fsds_m := swdown_regrid
      setmeta(fsds_m,"total incident solar radiation","W/m**2",time)
      outfile = out_base+"/Solar/clmforc.WFDE5.0.5x0.5.Solr."+yyyy+"-"+mm+".nc"
      system("/bin/rm -f " + outfile)
      fout := addfile(outfile,"c")
      filedimdef(fout,"time",-1,True)
      fout->FSDS   = fsds_m
      fout->time   = time
      fout->LONGXY = LONGXY
      fout->LATIXY = LATIXY
      fout->EDGEE  = EDGEE
      fout->EDGEW  = EDGEW
      fout->EDGES  = EDGES
      fout->EDGEN  = EDGEN

      ;;== Precip: PRECTmms ==;;
      prec_m := rainf_regrid
      setmeta(prec_m,"PRECTmms total precipitation","mm H2O / sec",time)
      outfile = out_base+"/Precip/clmforc.WFDE5.0.5x0.5.Prec."+yyyy+"-"+mm+".nc"
      system("/bin/rm -f " + outfile)
      fout := addfile(outfile,"c")
      filedimdef(fout,"time",-1,True)
      fout->PRECTmms = prec_m
      fout->time   = time
      fout->LONGXY = LONGXY
      fout->LATIXY = LATIXY
      fout->EDGEE  = EDGEE
      fout->EDGEW  = EDGEW
      fout->EDGES  = EDGES
      fout->EDGEN  = EDGEN

      ;;== TPHWL: TBOT,WIND,QBOT,PSRF,FLDS ==;;
      tbot_m := tbot_regrid
      wind_m := wind_regrid
      qbot_m := qbot_regrid
      psrf_m := psrf_regrid
      flds_m := lwdown_regrid
      setmeta(tbot_m,"temperature at the lowest atm level","K",time)
      setmeta(wind_m,"wind at the lowest atm level","m/s",time)
      setmeta(qbot_m,"specific humidity at the lowest atm level","kg/kg",time)
      setmeta(psrf_m,"surface pressure at the lowest atm level","Pa",time)
      setmeta(flds_m,"incident longwave radiation","W/m**2",time)
      outfile = out_base+"/TPHWL/clmforc.WFDE5.0.5x0.5.TPQWL."+yyyy+"-"+mm+".nc"
      system("/bin/rm -f " + outfile)
      fout := addfile(outfile,"c")
      filedimdef(fout,"time",-1,True)
      fout->TBOT   = tbot_m
      fout->WIND   = wind_m
      fout->QBOT   = qbot_m
      fout->PSRF   = psrf_m
      fout->FLDS   = flds_m
      fout->time   = time
      fout->LONGXY = LONGXY
      fout->LATIXY = LATIXY
      fout->EDGEE  = EDGEE
      fout->EDGEW  = EDGEW
      fout->EDGES  = EDGES
      fout->EDGEN  = EDGEN

    end do
    print(" "+yyyy+".. monthly write done.. ")
  end do

  print("Done.")

end
