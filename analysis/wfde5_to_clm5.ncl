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
     delete(x&lat)              ; ← 1D lat 좌표 제거
  end if
  if (iscoord(x,"lon")) then
     delete(x&lon)              ; ← 1D lon 좌표 제거
  end if
  x&time = t
  delete_VarAtts(x, -1)
  x@long_name  = ln
  x@units      = un
  x@mode       = "time-dependent"
  x@_FillValue = 1.e20          ; WFDE5 land-only fill (ERA5는 1.e36; WFDE5는 ocean=missing)
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
; wfde5_to_clm5.ncl
;
; era5_to_clm5.ncl (서버 1_CLM/, 연도별 단일파일 버전) 의 WFDE5 버전.
; 출력 구조(연도별 1파일 YYYY_wfde5.nc 에 7변수 통합 + LONGXY/LATIXY/EDGE
; + noleap time)를 그대로 보존. 입력만 ERA5 hourly -> WFDE5 6h-mean monthly.
;
; ERA5 대비 달라진 점 (입력이 이미 LSM-ready 라서 계산이 대폭 줄어듦):
;   - 입력: /data2/ydkoh/WFDE5_6h/{Var}/{Var}_WFDE5_CRU_YYYYMM_v3.0_6h.nc
;           (이미 6h 평균, 월별 분리; 1년치는 12개월 cat)
;   - QBOT : WFDE5 Qair 그대로 (dewpoint->q 계산 불필요)
;   - WIND : WFDE5 Wind 그대로 (u,v->wind 계산 불필요)
;   - FSDS : WFDE5 SWdown 그대로 (6h 평균/단위환산 불필요)
;   - PRECTmms : Rainf + Snowf (둘 다 kg m-2 s-1 = mm/s; WFDE5는 비/눈 분리)
;   - grid : WFDE5 lon -180~180 -> lonFlip -> 0~360 (GSWP3 셀과 정확히 일치)
;            lat 는 이미 -89.75~89.75 ascending (ERA5처럼 ::-1 뒤집기 불필요)
;   - noleap : WFDE5는 proleptic_gregorian(2/29 존재) -> drop_feb29 로 제거
;   - _FillValue : 1.e20 (WFDE5 ocean missing 보존)
;
; Run on climate00 (입력 /data2, 출력 /data2):
;   /usr/local/ncl_ncarg/6.6.2_gcc485/bin/ncl wfde5_to_clm5.ncl
;----------------------------------------------------------------------

begin

  w6_dir  = "/data2/ydkoh/WFDE5_6h"
  out_dir = "/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM_WFDE5"
  system("mkdir -p " + out_dir)

  yr_start = 1979
  yr_end   = 2024

  ; CLM5 variable mapping
  clm5_vars  = (/"TBOT","QBOT","PSRF","FSDS","FLDS","PRECTmms","WIND"/)

  do yr = yr_start, yr_end
    yyyy = sprinti("%0.4d", yr)

;;== TBOT ==;;
    files := systemfunc("ls "+w6_dir+"/Tair/Tair_WFDE5_CRU_"+yyyy+"??_v3.0_6h.nc")
    fi := addfiles(files,"r")
    ListSetType(fi,"cat")
    tbot := fi[:]->Tair                       ; (time,lat,lon) K, lat ascending
    tbot := drop_feb29(tbot)
	print(" "+yyyy+".. Tair done.. ")
;;==========;;

;;== QBOT ==;;
    files := systemfunc("ls "+w6_dir+"/Qair/Qair_WFDE5_CRU_"+yyyy+"??_v3.0_6h.nc")
    fi := addfiles(files,"r")
    ListSetType(fi,"cat")
    qbot := fi[:]->Qair                        ; kg/kg (그대로)
    qbot := drop_feb29(qbot)
	print(" "+yyyy+".. Qair done.. ")
;;==========;;

;;== PSRF ==;;
    files := systemfunc("ls "+w6_dir+"/PSurf/PSurf_WFDE5_CRU_"+yyyy+"??_v3.0_6h.nc")
    fi := addfiles(files,"r")
    ListSetType(fi,"cat")
    psrf := fi[:]->PSurf                        ; Pa
    psrf := drop_feb29(psrf)
    printVarSummary(psrf)
	print(" "+yyyy+".. PSurf done.. ")
;;==========;;

;;== FSDS ==;;
    files := systemfunc("ls "+w6_dir+"/SWdown/SWdown_WFDE5_CRU_"+yyyy+"??_v3.0_6h.nc")
    fi := addfiles(files,"r")
    ListSetType(fi,"cat")
    swdown := fi[:]->SWdown                     ; W/m2 (이미 6h 평균 flux)
    swdown := drop_feb29(swdown)
	print(" "+yyyy+".. SWdown done.. ")
;;==========;;

;;== FLDS ==;;
    files := systemfunc("ls "+w6_dir+"/LWdown/LWdown_WFDE5_CRU_"+yyyy+"??_v3.0_6h.nc")
    fi := addfiles(files,"r")
    ListSetType(fi,"cat")
    lwdown := fi[:]->LWdown                     ; W/m2
    lwdown := drop_feb29(lwdown)
	print(" "+yyyy+".. LWdown done.. ")
;;==========;;

;;== PRECTmms = Rainf + Snowf ==;;
    files := systemfunc("ls "+w6_dir+"/Rainf/Rainf_WFDE5_CRU_"+yyyy+"??_v3.0_6h.nc")
    fi := addfiles(files,"r")
    ListSetType(fi,"cat")
    rainf := fi[:]->Rainf                       ; kg/m2/s
    files := systemfunc("ls "+w6_dir+"/Snowf/Snowf_WFDE5_CRU_"+yyyy+"??_v3.0_6h.nc")
    fi := addfiles(files,"r")
    ListSetType(fi,"cat")
    snowf := fi[:]->Snowf                       ; kg/m2/s
    rainf = rainf + snowf                        ; 비+눈 = 총강수
    rainf@units = "kg/m2/s"
    rainf := drop_feb29(rainf)
	print(" "+yyyy+".. Rainf+Snowf done.. ")
;;==========;;

;;== WIND ==;;
    files := systemfunc("ls "+w6_dir+"/Wind/Wind_WFDE5_CRU_"+yyyy+"??_v3.0_6h.nc")
    fi := addfiles(files,"r")
    ListSetType(fi,"cat")
    wind := fi[:]->Wind                         ; m/s (이미 풍속)
    wind := drop_feb29(wind)
	print(" "+yyyy+".. Wind done.. ")
;;==========;;

	; ---- lon -180~180 -> 0~360 (GSWP3 셀과 일치) ----
	tbot   := lonFlip(tbot)
	qbot   := lonFlip(qbot)
	psrf   := lonFlip(psrf)
	swdown := lonFlip(swdown)
	lwdown := lonFlip(lwdown)
	rainf  := lonFlip(rainf)
	wind   := lonFlip(wind)

	 ; target lat-lon (GSWP3 0.5° 템플릿) — 격자 메타(LONGXY/LATIXY/EDGE)만 사용
	 T_grid = addfile("/data1/CESM2_INPUT/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516/TPHWL/clmforc.GSWP3.c2011.0.5x0.5.TPQWL.2010-12.nc","r")
	 LONGXY = T_grid->LONGXY        ; (lat,lon) 2D
	 LATIXY = T_grid->LATIXY
	 EDGEE  = T_grid->EDGEE
	 EDGEW  = T_grid->EDGEW
	 EDGES  = T_grid->EDGES
	 EDGEN  = T_grid->EDGEN

	; WFDE5(lonFlip 후) 격자 == GSWP3 0.5° 격자와 셀 단위 완전 일치.
	; ERA5(전구 완전자료)와 달리 WFDE5는 land-only(ocean=fill)라
	; area_conserve_remap 을 쓰면 fill 이 섞여 전 격자가 망가짐 -> remap 생략, 직접 대입.
 	tbot_regrid = tbot
 	qbot_regrid = qbot
 	psrf_regrid = psrf
 	swdown_regrid = swdown
 	lwdown_regrid = lwdown
 	rainf_regrid = rainf
 	wind_regrid = wind

	; ===== time (noleap, 6-hourly) =====
	nday = 365
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
    outfile = out_dir + "/" +yyyy+ "_wfde5.nc"
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

    ; global attributes
    fAtt        = True
    fAtt@title  = "CLM5 forcing from WFDE5 v3.0 (CRU)"
    fAtt@source = "youngdaekoh@gmail.com from Sejong Univ."
    fileattdef(fout, fAtt)

  end do

  print("Done.")

end
