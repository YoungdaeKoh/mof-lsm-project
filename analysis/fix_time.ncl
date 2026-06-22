;----------------------------------------------------------------------
; fix_time.ncl
;
; Overwrite the time coordinate of existing CLM forcing files in place.
; Fixes datm error "elapsed seconds must be increasing": fspan float drift
; produced non-exact day values (0.9999..) and exact integer-day stamps
; hit datm's date/tod boundary. Use exact ispan arithmetic + 0.125-day
; (3 h) interval-center offset, matching the GSWP3 convention so no
; timestamp lands on an integer day boundary.
;
; Only the time variable values are rewritten; data variables untouched.
;
; Run on climate00:
;   /usr/local/ncl_ncarg/6.6.2_gcc485/bin/ncl fix_time.ncl
;----------------------------------------------------------------------

begin

  dir   = "/data2/ydkoh/2026_MOF_LSM/Atm_forc/1_CLM/tmp"
  years = (/1979,1980,1981,1982/)

  do i = 0, dimsizes(years)-1
    yyyy = sprinti("%0.4d", years(i))
    fn   = dir + "/" + yyyy + "_era5.nc"

    if (.not. fileexists(fn)) then
      print("skip (missing): " + fn)
      continue
    end if

    f  = addfile(fn, "w")
    nt = dimsizes(f->time)

    t = ispan(0, nt-1, 1) * 0.25 + 0.125    ; 0.125,0.375,... exact, center stamps
    t!0        = "time"
    t&time     = t
    t@units    = "days since " + yyyy + "-01-01 00:00:00"
    t@calendar = "noleap"
    t@long_name = "observation time"

    f->time = (/ t /)                        ; overwrite values in place

    print(yyyy + ": time fixed  nt=" + nt + "  [" + t(0) + " .. " + t(nt-1) + "]")

    delete([/ f, t, nt /])
  end do

  print("Done.")

end
