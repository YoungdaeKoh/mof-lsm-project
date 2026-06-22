;----------------------------------------------------------------------
; regrid_era5land_swvl.ncl
;
; ERA5-Land volumetric soil water (swvl1-4, 0.1deg) -> CLM f19 grid.
; Horizontal conservative remap only; keeps ERA5-Land's 4 layers.
; Output: one file per year, swvl1-4 on CLM grid (lat96 x lon144), monthly.
;
; Run on climate00 (ERA5-Land on /data1, CLM grid from archive h0):
;   setenv NCARG_ROOT /usr/local/ncl_ncarg/6.6.2_gcc485
;   /usr/local/ncl_ncarg/6.6.2_gcc485/bin/ncl regrid_era5land_swvl.ncl
;----------------------------------------------------------------------

begin

  era5l_base = "/data1/ERA5/land_level/monthly_0.1"
  clm_grid   = "/data2/ydkoh/cesm2_output/archive/I2000_ERA5_spinup/lnd/hist/I2000_ERA5_spinup.clm2.h0.0001-01.nc"
  out_dir    = "/data2/ydkoh/2026_MOF_LSM/diag/era5land_clmgrid"
  system("mkdir -p " + out_dir)

  yr_start = 1979
  yr_end   = 1987        ; TEST: 1979 only first; later set 1988

  layers = (/"volumetric_soil_water_layer_1","volumetric_soil_water_layer_2", \
             "volumetric_soil_water_layer_3","volumetric_soil_water_layer_4"/)
  vnames = (/"swvl1","swvl2","swvl3","swvl4"/)
  nlay   = dimsizes(layers)

  ; ---- target CLM grid ----
  fg   = addfile(clm_grid, "r")
  clat = fg->lat            ; 96, ascending -90..90
  clon = fg->lon            ; 144, 0..357.5

  do yr = yr_start, yr_end
    yyyy = sprinti("%0.4d", yr)
    outf = out_dir + "/era5land_swvl_clmgrid_" + yyyy + ".nc"
    system("/bin/rm -f " + outf)
    setfileoption("nc","Format","NetCDF4Classic")
    fo = addfile(outf, "c")

    do iv = 0, nlay-1
      ; collect 12 months on CLM grid
      sw_out = new((/12, dimsizes(clat), dimsizes(clon)/), float)
      sw_out!0 = "time"
      sw_out!1 = "lat"
      sw_out&lat = clat
      sw_out!2 = "lon"
      sw_out&lon = clon

      do mo = 1, 12
        mm = sprinti("%0.2d", mo)
        inf = era5l_base + "/" + layers(iv) + "/dataset/ERA5m-land_" + yyyy + mm + ".nc"
        if (.not. fileexists(inf)) then
          print("missing: " + inf)
          continue
        end if
        f   = addfile(inf, "r")
        x   = short2flt(f->$vnames(iv)$)        ; (time=1, lat1801, lon3600), m3/m3
        x2  = x(0, ::-1, :)                       ; flip lat -> ascending
        lai = x2&latitude
        loi = x2&longitude
        ; hi->lo area average; handles _FillValue (land-only: ocean skipped).
        ; critpc=50 -> output box must be >=50% valid (land) else missing.
        ropt = True
        ropt@critpc = 50.
        xo  = area_hi2lores_Wrap(loi, lai, x2, True, 1.0, clon, clat, ropt)
        sw_out(mo-1,:,:) = (/ xo /)
        delete([/f, x, x2, lai, loi, xo/])
      end do

      sw_out@long_name = "ERA5-Land " + vnames(iv) + " on CLM grid"
      sw_out@units     = "m3/m3"
      fo->$vnames(iv)$ = sw_out
      delete(sw_out)
      print(yyyy + " " + vnames(iv) + " done")
    end do

    delete(fo)
    print("wrote: " + outf)
  end do

  print("Done.")

end
