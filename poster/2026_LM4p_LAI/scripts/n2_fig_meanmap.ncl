;=====================================================================
; n2_fig_meanmap.ncl
; Poster Fig. 1: seasonal-mean LAI 1982-2010 (MON below; MJJAS), LM4p ctl vs GIMMS LAI4g
;   (a) GIMMS  (b) LM4p  (c) LM4p - GIMMS, each with its zonal mean attached on the right
; input : ../data/{lm4p_ctl,gimms}_lai_clim_1982_2010.nc  (n1_lai_clim_anom.ncl)
; output: ../figures/fig1_lai_mean_bias.png
; common mask: cells valid in both, 60S-90N, Greenland removed (Iceland and Baffin/Ungava kept;
;   the earlier 60N+/75-10W box also cut those, global bias +54.0 -> +53.9 %)
;   (same mask as the summary numbers in ../data/lai_mean_trend_summary.txt)
;=====================================================================
begin

  MON  = (/4,5,6,7,8/)   ; 0-based month indices averaged (all 12 = annual mean)
  SEAS = "MJJAS"

  fi   = addfile("../data/lm4p_ctl_lai_clim_1982_2010.nc", "r")
  clim = fi->clim(:,:,:)
  printVarSummary(clim)
  clim!0 = "time"
  clim!1 = "lat"
  clim!2 = "lon"
  lm4  = dim_avg_n_Wrap(clim(MON,:,:), 0)
  delete(clim)

  fi   = addfile("../data/gimms_lai_clim_1982_2010.nc", "r")
  clim = fi->clim(:,:,:)
  clim!0 = "time"
  clim!1 = "lat"
  clim!2 = "lon"
  gim  = dim_avg_n_Wrap(clim(MON,:,:), 0)
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
  print(SEAS+" global mean LM4p "+sprintf("%5.3f",gm)+"  GIMMS "+sprintf("%5.3f",gg)+"  bias "+sprintf("%+5.1f",(gm/gg-1)*100)+" %")

  zm   = dim_avg_n(lm4, 1)
  zg   = dim_avg_n(gim, 1)
  zd   = zm - zg
  print("zonal mean max: LM4p "+max(zm)+" GIMMS "+max(zg)+" | diff min "+min(zd)+" max "+max(zd))

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

  ; layout (NDC): three maps of identical size stacked on the left; (a),(b) share one
  ; colour bar on the right; (d) zonal mean sits right of (c) on the same latitude axis
  W    = 0.58
  H    = W*145./360.          ; 60S-85N by 360 deg, cylindrical equidistant
  X0   = 0.07
  GAP  = 0.068               ; room for longitude labels plus the next panel title
  YA   = 0.955
  YB   = YA - H - GAP
  YC   = YB - H - GAP
  lev1 = (/0.25,0.5,1,1.5,2,2.5,3,4,5,6,7/)
  lev2 = (/-3,-2,-1.5,-1,-0.5,-0.25,0.25,0.5,1,1.5,2,3/)
  res@mpShapeMode          = "FreeAspect"
  res@vpXF                 = X0
  res@vpWidthF             = W
  res@vpHeightF            = H
  res@lbLabelBarOn         = False
  res@tmXTOn               = False   ; no tick marks on the top and right map edges
  res@tmYROn               = False
  res@gsnMajorLonSpacing   = 60      ; one longitude tick every 60 degrees
  res@mpGridAndLimbOn      = True    ; grey dashed lines every 30 degrees of latitude and longitude
  res@mpGridLatSpacingF    = 30
  res@mpGridLonSpacingF    = 30
  res@mpGridLineColor      = "gray50"
  res@mpGridLineDashPattern = 2
  res@mpGridLineThicknessF = 1.0

  res@cnFillPalette        = "MPL_YlGn"
  res@cnLevelSelectionMode = "ExplicitLevels"
  res@cnLevels             = lev1
  res@tmXBLabelsOn         = True    ; longitude labels on every map
  res@vpYF                 = YA
  res@gsnLeftString        = "(a) GIMMS LAI ("+SEAS+")"
  p1 = gsn_csm_contour_map(wks, gim, res)
  res@vpYF                 = YB
  res@gsnLeftString        = "(b) LM4+ LAI ("+SEAS+")"
  p2 = gsn_csm_contour_map(wks, lm4, res)

  delete([/res@cnLevels, res@cnFillPalette/])
  res@cnFillPalette        = "MPL_BrBG"
  res@cnLevels             = lev2
  res@tmXBLabelsOn         = True
  res@vpYF                 = YC
  res@gsnLeftString        = "(c) Diff. (Model - Obs.; bias : "+sprintf("%+3.0f",(gm/gg-1)*100)+"%)"
  p3 = gsn_csm_contour_map(wks, dif, res)

  ; zonal means: one panel per row, left edge on the right edge of the map, same latitude axis
  ZW                       = 0.10
  xr                       = True
  xr@gsnDraw               = False
  xr@gsnFrame              = False
  xr@vpXF                  = X0 + W
  xr@vpWidthF              = ZW
  xr@vpHeightF             = H
  xr@trYMinF               = -60
  xr@trYMaxF               = 85
  xr@tmYLOn                = False
  xr@tmXTOn                = False
  xr@tmXBMode              = "Explicit"
  xr@tmXBLabelFontHeightF  = 0.011
  xr@tiXAxisFontHeightF    = 0.012
  xr@xyDashPatterns        = (/0, 0/)
  xr@gsnYRefLine           = (/-30., 0., 30., 60./)   ; same latitude guides as the maps
  xr@gsnYRefLineColor      = "gray50"
  xr@gsnYRefLineDashPattern = 2
  xr@gsnYRefLineThicknessF = 1.0

  xa                       = xr          ; row (a): GIMMS
  xa@vpYF                  = YA
  xa@trXMinF               = 0
  xa@trXMaxF               = 7
  xa@tmXBValues            = (/2,4,6/)
  xa@tmXBLabels            = (/"2","4","6"/)
  xa@tmXBLabelsOn          = True
  xa@gsnXRefLine           = (/2., 4., 6./)          ; grey guides at the labelled values
  xa@gsnXRefLineColor      = "gray50"
  xa@gsnXRefLineDashPattern = 2
  xa@gsnXRefLineThicknessF = 1.0
  xa@xyLineThicknesses     = (/3.0, 3.0/)
  xa@xyLineColors          = (/"forestgreen", "forestgreen"/)
  p4 = gsn_csm_xy(wks, (/zg, zg/), lat, xa)

  xb                       = xa          ; row (b): LM4+ with GIMMS for reference
  xb@vpYF                  = YB
  xb@tmXBLabelsOn          = True
  xb@xyLineThicknesses     = (/3.0, 1.5/)
  xb@xyLineColors          = (/"blue3", "forestgreen"/)
  xb@pmLegendDisplayMode   = "Always"
  xb@xyExplicitLegendLabels = (/" LM4+", " GIMMS"/)
  xb@pmLegendWidthF        = 0.03
  xb@pmLegendHeightF       = 0.03
  xb@pmLegendParallelPosF  = 0.55
  xb@pmLegendOrthogonalPosF = -1.16
  xb@lgLabelFontHeightF    = 0.009
  xb@lgPerimOn             = False
  p5 = gsn_csm_xy(wks, (/zm, zg/), lat, xb)

  xc                       = xr          ; row (c): difference
  xc@vpYF                  = YC
  xc@trXMinF               = -1
  xc@trXMaxF               = 3.5
  xc@tmXBValues            = (/0,1,2,3/)
  xc@tmXBLabels            = (/"0","1","2","3"/)
  xc@tiXAxisString         = "LAI difference"
  xc@gsnXRefLine           = (/0., 1., 2., 3./)      ; zero line solid, the others dashed guides
  xc@gsnXRefLineColor      = "gray50"
  xc@gsnXRefLineDashPatterns = (/0, 2, 2, 2/)
  xc@gsnXRefLineThicknessF = 1.0
  xc@xyLineThicknesses     = (/3.0, 3.0/)
  xc@xyLineColors          = (/"black", "black"/)
  p6 = gsn_csm_xy(wks, (/zd, zd/), lat, xc)

  ; the four Fig. 2 regions on (c) (same boxes as p3_regional_seasonal_sos_eos.py): lat0, lat1, lon0, lon1
  ; IPCC AR6 land reference regions (Iturbide et al. 2020) used in Fig. 2. Corner vertices from
  ; regionmask.defined_regions.ar6.land (v0.13.0); edges are straight lines in lon-lat.
  bx                       = True
  bx@gsLineColor           = "black"
  bx@gsLineThicknessF      = 5.0
  bdum = new(4, graphic)   ; poster (2026-10-08): the four regions of Figs. 2-3 only
  bdum(0) = gsn_add_polyline(wks, p3, (/-10., -10., 40., 40., -10./), (/48., 72.6, 72.6, 61.3, 48./), bx)        ; NEU
  bdum(1) = gsn_add_polyline(wks, p3, (/130., 130., 180., 180., 157., 152., 130./), \
                                      (/ 45.,  65.,  65., 59.9,  50.,  45.,  45./), bx)                 ; RFE
  bdum(2) = gsn_add_polyline(wks, p3, (/-105.,-130.,-143.,-168.,-168.,-129.,-125.,-105.,-105./), \
                                      (/  50.,  50.,  58., 52.5, 72.6, 72.6, 77.6,  81.,  50./), bx)   ; NWN
  bdum(3) = gsn_add_polyline(wks, p3, (/90., 90., 130., 130., 90./), (/45., 65., 65., 45., 45./), bx)   ; ESB
  tx                       = True      ; region abbreviations, placed just outside each polygon
  tx@txFontHeightF         = 0.009
  tx@txFontColor           = "black"
  tx@txBackgroundFillColor = "white"
  tx@txPerimOn             = False
  tdum = gsn_add_text(wks, p3, (/"NEU","RFE","NWN","ESB"/), \
                               (/ -22., 152., -150., 104./), \
                               (/  66.,  71.,   78.,  71./), tx)

  draw(p1)
  draw(p2)
  draw(p3)
  draw(p4)
  draw(p5)
  draw(p6)

  lb                       = True
  lb@lbPerimOn             = False
  lb@lbMonoFillPattern     = True
  lb@lbLabelFontHeightF    = 0.012
  lb@lbLabelAlignment      = "InteriorEdges"
  lb@lbBoxEndCapStyle      = "TriangleBothEnds"
  LBV                      = (YA - (YB - H))*2./3.   ; 2/3 of the (a)-(b) span, centred on it
  lb@lbOrientation         = "Vertical"       ; shared by (a) and (b)
  lb@vpWidthF              = 0.072
  lb@vpHeightF             = LBV
  lb@lbFillColors          = span_color_rgba("MPL_YlGn", dimsizes(lev1)+1)
  lb@lbTitleString         = "LAI (m~S~2~N~/m~S~2~N~)"
  lb@lbTitleFontHeightF    = 0.012
  lb@lbTitlePosition       = "Right"
  lb@lbTitleDirection      = "Across"
  lb@lbTitleAngleF         = 90
  gsn_labelbar_ndc(wks, dimsizes(lev1)+1, ""+lev1, X0 + W + ZW + 0.035, YA - LBV/4., lb)
  delete([/lb@lbFillColors, lb@lbTitleString, lb@lbTitlePosition, lb@lbTitleDirection, lb@lbTitleAngleF/])
  lb@lbOrientation         = "Horizontal"     ; (c)
  lb@lbLabelAutoStride     = False            ; keep every level labelled on the shorter bar
  lb@lbLabelFontHeightF    = 0.010
  lb@vpWidthF              = W*2./3.          ; 2/3 of the map width, centred under (c)
  lb@vpHeightF             = 0.06
  lb@lbFillColors          = span_color_rgba("MPL_BrBG", dimsizes(lev2)+1)
  gsn_labelbar_ndc(wks, dimsizes(lev2)+1, ""+lev2, X0 + W/6., YC - H - 0.035, lb)
  frame(wks)

;	system("rm -f test.nc")
;	fo = addfile("test.nc","c")
;	fo->dif = dif

end
