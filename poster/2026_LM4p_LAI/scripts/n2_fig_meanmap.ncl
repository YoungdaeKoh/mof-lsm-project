;=====================================================================
; n2_fig_meanmap.ncl
; Poster Fig. 1: annual-mean LAI 1982-2010, LM4p ctl vs GIMMS LAI4g
;   (a) LM4p  (b) GIMMS  (c) LM4p - GIMMS  (d) zonal mean of (a),(b)
; input : ../data/{lm4p_ctl,gimms}_lai_clim_1982_2010.nc  (n1_lai_clim_anom.ncl)
; output: ../figures/fig1_lai_mean_bias.png
; common mask: cells valid in both, 60S-90N, Greenland removed (Iceland and Baffin/Ungava kept;
;   the earlier 60N+/75-10W box also cut those, global bias +54.0 -> +53.9 %)
;   (same mask as the summary numbers in ../data/lai_mean_trend_summary.txt)
;=====================================================================
begin

  fi   = addfile("../data/lm4p_ctl_lai_clim_1982_2010.nc", "r")
  clim = fi->clim(:,:,:)
  printVarSummary(clim)
  clim!0 = "time"
  clim!1 = "lat"
  clim!2 = "lon"
  lm4  = dim_avg_n_Wrap(clim, 0)
  delete(clim)

  fi   = addfile("../data/gimms_lai_clim_1982_2010.nc", "r")
  clim = fi->clim(:,:,:)
  clim!0 = "time"
  clim!1 = "lat"
  clim!2 = "lon"
  gim  = dim_avg_n_Wrap(clim, 0)
  delete(clim)

  lat  = lm4&lat
  lon  = lm4&lon
  lat2 = conform(lm4, lat, 0)
  lon2 = conform(lm4, lon, 1)
  ; Greenland = old box 60N+/75-10W minus Iceland and the Canadian cells (Baffin/Ungava) inside it
  grl  = lat2.gt.60 .and. lon2.gt.-75 .and. lon2.lt.-10 \
         .and. .not.(lat2.gt.63 .and. lat2.lt.67 .and. lon2.gt.-25 .and. lon2.lt.-13) \
         .and. .not.(lon2.lt.-60 .and. lat2.lt.75)
  msk  = ismissing(lm4) .or. ismissing(gim) .or. lat2.lt.-60 .or. grl
  lm4  = where(msk, lm4@_FillValue, lm4)
  gim  = where(msk, gim@_FillValue, gim)
  dif  = lm4
  dif  = lm4 - gim

  rad  = 4.*atan(1.)/180.
  wgt  = cos(lat*rad)
  wgt  = where(wgt.lt.0, 0, wgt)
  gm   = wgt_areaave(lm4, wgt, 1.0, 0)
  gg   = wgt_areaave(gim, wgt, 1.0, 0)
  print("global mean LM4p "+sprintf("%5.3f",gm)+"  GIMMS "+sprintf("%5.3f",gg)+"  bias "+sprintf("%+5.1f",(gm/gg-1)*100)+" %")

  zm   = dim_avg_n(lm4, 1)
  zg   = dim_avg_n(gim, 1)

;---------------------------------------------------------------- plot
  wtype          = "png"
  wtype@wkWidth  = 3000
  wtype@wkHeight = 3000
  wks = gsn_open_wks(wtype, "../figures/fig1_lai_mean_bias")

  res                      = True
  res@gsnDraw              = False
  res@gsnFrame             = False
  res@cnFillOn             = True
  res@cnLinesOn            = False
  res@cnLineLabelsOn       = False
  res@cnFillMode           = "RasterFill"
  res@mpMinLatF            = -60
  res@mpMaxLatF            = 85
  res@mpCenterLonF         = 0
  res@mpGeophysicalLineThicknessF = 0.5
  res@mpFillOn             = False
  res@tmXBLabelFontHeightF = 0.012
  res@tmYLLabelFontHeightF = 0.012
  res@gsnLeftStringFontHeightF  = 0.016
  res@gsnRightStringFontHeightF = 0.014
  res@lbLabelFontHeightF   = 0.012
  res@lbOrientation        = "Vertical"
  res@pmLabelBarWidthF     = 0.06
  res@pmLabelBarOrthogonalPosF = 0.02
  res@gsnRightString       = "m~S~2~N~/m~S~2~N~"

  res@cnFillPalette        = "MPL_YlGn"
  res@cnLevelSelectionMode = "ExplicitLevels"
  res@cnLevels             = (/0.25,0.5,1,1.5,2,2.5,3,4,5,6,7/)
  res@lbLabelBarOn         = False
  res@tmXBLabelsOn         = False
  res@gsnLeftString        = "(a) LM4+ (ctl)  mean "+sprintf("%4.2f",gm)
  p1 = gsn_csm_contour_map(wks, lm4, res)
  res@lbLabelBarOn         = True
  res@gsnLeftString        = "(b) GIMMS LAI4g  mean "+sprintf("%4.2f",gg)
  p2 = gsn_csm_contour_map(wks, gim, res)

  delete([/res@cnLevels, res@cnFillPalette/])
  res@cnFillPalette        = "MPL_BrBG"
  res@cnLevels             = (/-3,-2,-1.5,-1,-0.5,-0.25,0.25,0.5,1,1.5,2,3/)
  res@tmXBLabelsOn         = True
  res@gsnLeftString        = "(c) LM4+ - GIMMS  bias "+sprintf("%+4.2f",gm-gg)+" ("+sprintf("%+3.0f",(gm/gg-1)*100)+"%)"
  p3 = gsn_csm_contour_map(wks, dif, res)

  xr                       = True
  xr@gsnDraw               = False
  xr@gsnFrame              = False
  xr@vpWidthF              = 0.16
  xr@vpHeightF             = 0.62
  xr@trYMinF               = -60
  xr@trYMaxF               = 85
  xr@trXMinF               = 0
  xr@xyLineThicknesses     = (/3.0, 3.0/)
  xr@xyLineColors          = (/"blue3", "forestgreen"/)
  xr@xyDashPatterns        = (/0, 0/)
  xr@tiXAxisString         = "LAI"
  xr@tiXAxisFontHeightF    = 0.012
  xr@tmXBLabelFontHeightF  = 0.011
  xr@tmYLLabelFontHeightF  = 0.011
  xr@gsnLeftString         = "(d) zonal mean"
  xr@gsnLeftStringFontHeightF = 0.014
  xr@pmLegendDisplayMode   = "Always"
  xr@xyExplicitLegendLabels = (/" LM4+", " GIMMS"/)
  xr@pmLegendWidthF        = 0.06
  xr@pmLegendHeightF       = 0.05
  xr@pmLegendParallelPosF  = 0.80
  xr@pmLegendOrthogonalPosF = -1.05
  xr@lgLabelFontHeightF    = 0.011
  xr@lgPerimOn             = False
  zz = (/zm, zg/)
  p4 = gsn_csm_xy(wks, zz, lat, xr)

  pres                     = True
  pres@gsnFrame            = False
  pres@gsnPanelRight       = 0.76
  pres@gsnPanelBottom      = 0.04
  pres@gsnPanelYWhiteSpacePercent = 3
  gsn_panel(wks, (/p1,p2,p3/), (/3,1/), pres)
  setvalues p4
    "vpXF" : 0.80
    "vpYF" : 0.86
  end setvalues
  draw(p4)
  frame(wks)

;	system("rm -f test.nc")
;	fo = addfile("test.nc","c")
;	fo->dif = dif

end
