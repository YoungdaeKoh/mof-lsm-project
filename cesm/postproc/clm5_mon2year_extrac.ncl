;==============================================================================
;  clm5_mon2year_extrac.ncl
;
;  CLM5 production run (clm5_prod_1979_2023, WFDE5 1979-2023, f09 192x288)
;  monthly h0 history  ->  one yearly file holding the diagnostic variables.
;
;  Why yearly files: the h0 files are stamped at the END of the averaging
;  period (the January mean carries time = Feb 1 00Z), so reading them one by
;  one puts every month in the wrong calendar month.  Here the 12 files of a
;  year are concatenated and the time axis is moved back 15 days, which puts
;  each record in the middle of the month it actually averages.
;
;  in   /data2/ydkoh/cesm2_output/clm5_prod_1979_2023/run/*.clm2.h0.YYYY-MM.nc
;  out  /data2/ydkoh/cesm2_output/postproc/clm5_prod/clm5_prod.YYYY.nc
;
;  run (climate00):
;    nohup /usr/local/ncl_ncarg/6.6.2_gcc485/bin/ncl clm5_mon2year_extrac.ncl \
;          >& clm5_mon2year.log &
;==============================================================================

begin

;========== parameter ==========;
	y1 = 1979
	y2 = 2023

	INPUTDIR = "/data2/ydkoh/cesm2_output/clm5_prod_1979_2023/run"
	CNAME    = "clm5_prod_1979_2023"
	OUTDIR   = "/data2/ydkoh/cesm2_output/postproc/clm5_prod"

;  harmonized diagnostic set (CLM5 native names; the multi-LSM mapping table
;  lives in cesm/postproc/VARIABLE_MAP.md)
	vars = (/ "EFLX_LH_TOT", "FSH", "FGR", "FSA", "FIRA", "FSDS", "FLDS",   \
	          "TSA", "TG", "TV", "TSOI", "TSOI_10CM",                       \
	          "QFLX_EVAP_TOT", "QSOIL", "QVEGE", "QVEGT",                   \
	          "QRUNOFF", "QOVER", "QDRAI", "RAIN", "SNOW",                  \
	          "SOILWATER_10CM", "H2OSOI", "H2OSNO", "SNOW_DEPTH", "FSNO",   \
	          "ZWT", "TLAI", "ELAI", "GPP", "NPP", "NEE",                   \
	          "TOTVEGC", "TOTSOMC" /)

	system("mkdir -p "+OUTDIR)

;========== year loop ==========;
	do YEAR = y1, y2

	year = sprinti("%0.4i",YEAR)

	fname = systemfunc("ls "+INPUTDIR+"/"+CNAME+".clm2.h0."+year+"-*.nc")
;	print(fname)

	if (dimsizes(fname).ne.12) then
		print("ABORT: "+year+" has "+dimsizes(fname)+" monthly files, expected 12")
		exit
	end if

	fi = addfiles(fname,"r")
	ListSetType(fi,"cat")

	fout = OUTDIR+"/clm5_prod."+year+".nc"
	system("rm -f "+fout)
	fo = addfile(fout,"c")

	do jj = 0, dimsizes(vars)-1

	var = vars(jj)

	wrk = fi[:]->$var$

	if (YEAR.eq.y1 .and. jj.eq.0) then
		printVarSummary(wrk)
	end if

;  h0 stamps the mean at the end of its period -> shift to mid-month
	wrk&time = wrk&time - 15

	fo->$var$ = wrk

	delete(wrk)

	end do

	delete(fname)
	delete(fi)
	delete(fo)

	print(""+CNAME+" "+year+" done ("+dimsizes(vars)+" vars)")

	end do

end
