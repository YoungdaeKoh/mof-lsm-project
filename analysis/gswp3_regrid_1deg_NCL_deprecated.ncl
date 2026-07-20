; GSWP3 0.5° → 1° regrid for JULES (CLM-format, 3 groups, conservative remap).
; GSWP3 is globally complete (no land-only fill) so area_conserve_remap is safe.
; Preserves datm7 structure: TPQWL(TBOT/QBOT/PSRF/WIND/FLDS) + Solr(FSDS) + Prec(PRECTmms)
; + LONGXY/LATIXY/EDGE at 1°. Output: clmforc.GSWP3.c2011.1x1.{grp}.YYYY-MM.nc
begin
  src = "/data1/CESM2_INPUT/atm/datm7/atm_forcing.datm7.GSWP3.0.5d.v1.c170516"
  out = "/data2/ydkoh/jules_gswp3_1deg"
  system("mkdir -p " + out)

  ; year/month from env (default 1981-01 validation)
  y0 = toint(getenv("Y0")) 
  y1 = toint(getenv("Y1"))
  if (ismissing(y0)) then
    y0 = 1981
  end if
  if (ismissing(y1)) then
    y1 = 1981
  end if

  ; target 1° grid
  T_LON = fspan(0.5, 359.5, 360)
  T_LAT = fspan(-89.5, 89.5, 180)
  T_LON@units = "degrees_east"
  T_LAT@units = "degrees_north"

  ; group -> (file tag, variables)
  grps  = (/"TPQWL", "Solr", "Prec"/)
  dirs  = (/"TPHWL", "Solar", "Precip"/)
  ftag  = (/"TPQWL", "Solr", "Prec"/)

  do yr = y0, y1
  do mo = 1, 12
    yyyy = sprinti("%0.4d", yr)
    mm   = sprinti("%0.2d", mo)
    do ig = 0, 2
      infile = src + "/" + dirs(ig) + "/clmforc.GSWP3.c2011.0.5x0.5." + ftag(ig) + "." + yyyy + "-" + mm + ".nc"
      if (.not. fileexists(infile)) then
        continue
      end if
      fin = addfile(infile, "r")
      outfile = out + "/clmforc.GSWP3.c2011.1x1." + ftag(ig) + "." + yyyy + "-" + mm + ".nc"
      system("/bin/rm -f " + outfile)
      fout = addfile(outfile, "c")
      filedimdef(fout, "time", -1, True)

      ; variables to regrid (skip coords)
      vnames = getfilevarnames(fin)
      do iv = 0, dimsizes(vnames)-1
        v = vnames(iv)
        if (v.eq."time" .or. v.eq."LONGXY" .or. v.eq."LATIXY" .or. \
            v.eq."EDGEE" .or. v.eq."EDGEW" .or. v.eq."EDGES" .or. v.eq."EDGEN") then
          continue
        end if
        x = fin->$v$
        if (dimsizes(dimsizes(x)).ne.3) then
          continue
        end if
        S_LON = fin->LONGXY(0,:)
        S_LAT = fin->LATIXY(:,0)
        xr = area_conserve_remap_Wrap(S_LON, S_LAT, x, T_LON, T_LAT, False)
        xr!0 = "time"
        xr!1 = "lat"
        xr!2 = "lon"
        copy_VarAtts(x, xr)
        fout->$v$ = xr
        delete([/x, xr/])
      end do
      ; time + 1° coord metadata (LONGXY/LATIXY 2D)
      fout->time = fin->time
      lon2d = conform_dims((/180,360/), T_LON, 1)
      lat2d = conform_dims((/180,360/), T_LAT, 0)
      lon2d!0="lat"
      lon2d!1="lon"
      lon2d@long_name="longitude"
      lon2d@units="degrees_east"
      lat2d!0="lat"
      lat2d!1="lon"
      lat2d@long_name="latitude"
      lat2d@units="degrees_north"
      fout->LONGXY = lon2d
      fout->LATIXY = lat2d
      delete(fin)
      print(yyyy + "-" + mm + " " + ftag(ig) + " done")
    end do
  end do
  end do
end
