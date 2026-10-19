# Poster references — LM4+ 전 지구 LAI 모의 특성 진단 (2026-10-03)

DOI는 Crossref로 서지 확인(문헌조사 에이전트). `PDF` = 이 폴더에 있음, `↓` = 직접 다운로드 필요 (`references.html`에 링크).
LM4.1 수치는 Shevliakova 2024 전문에서 직접 확인.

## A. 관측에서 LAI가 중요한 이유
| # | Citation | 핵심 수치 | 파일 |
|---|---|---|---|
| A1 | Zhu et al. 2016, *Nat. Clim. Change* 6, 791–795. doi:10.1038/nclimate3004 | 1982–2009 식생면적 25–50 % greening (browning <4 %); 기여 CO₂ 70 %, N침적 9 %, 기후 8 %, LCC 4 % | ↓ |
| A2 | Chen et al. 2019, *Nat. Sustain.* 2, 122–129. doi:10.1038/s41893-019-0220-7 | 2000년 이후 greening 1/3을 중국·인도(식생면적 9 %)가 차지 — 토지관리 | ↓ |
| A3 | Piao et al. 2020, *Nat. Rev. Earth Environ.* 1, 14–27. doi:10.1038/s43017-019-0001-x | greening 특징·원인·피드백 리뷰 (서론용) | ↓ |
| A4 | Forzieri et al. 2017, *Science* 356, 1180–1184. doi:10.1126/science.aal1727 | LAI 증가가 식생면적 ~60 %에서 온난화 ~14 % 완화, 북방은 알베도로 ~10 % 증폭 | ↓ |
| A5 | Zeng et al. 2017, *Nat. Clim. Change* 7, 432–436. doi:10.1038/nclimate3299 | greening이 지면 온난화 0.09±0.02 °C(12 %) 완화, 70 %가 증발산 냉각 | ↓ |
| A6 | Zeng et al. 2018, *J. Climate* 31, 2633–2650. doi:10.1175/JCLI-D-17-0236.1 | LAI +8 % → ET +12.0±2.4 mm/yr(관측 ET 증가의 55 %), 강수 +12.1 mm/yr, 건조지 토양수분↓ | ↓ |
| A7 | Cao et al. 2023, *ESSD* 15, 4877–4899. doi:10.5194/essd-15-4877-2023 | **GIMMS LAI4g** 1982–2020, Landsat 360만 샘플+BPNN, 궤도표류 제거, LAI3g·GLASS보다 정확 | PDF |
| A8 | Zhu et al. 2013, *Remote Sens.* 5, 927–948. doi:10.3390/rs5020927 | LAI3g (LM4.1 평가·Gier 2024가 사용한 관측) | ↓ |

## B. 모델에서 LAI 중요성·공통 결함
| # | Citation | 핵심 | 파일 |
|---|---|---|---|
| B1 | Anav et al. 2013, *J. Climate* 26, 6801–6843. doi:10.1175/JCLI-D-12-00417.1 | CMIP5 18개 ESM: GPP·LAI 대부분 과대 | ↓ |
| B2 | Anav et al. 2013, *Remote Sens.* 5, 3637–3661. doi:10.3390/rs5083637 | 북반구 고위도 LAI 과대, 휴면 늦어 성장기 과다 | ↓ |
| B3 | Murray-Tortarolo et al. 2013, *Remote Sens.* 5, 4819–4838. doi:10.3390/rs5104819 | TRENDY 오프라인 8개: 전부 LAI 과대(특히 북방), 7개가 성장기 과다, **증가추세가 위성보다 큼** | ↓ |
| B4 | Mahowald et al. 2016, *Earth Syst. Dynam.* 7, 211–229. doi:10.5194/esd-7-211-2016 | 현재 열대 LAI skill이 미래 LAI 전망 불확실성으로 연결 | PDF |
| B5 | Song et al. 2021, *Adv. Clim. Change Res.* 12, 584–595. doi:10.1016/j.accre.2021.06.008 | CMIP6 27개: LAI 과대(비산림), 추세·연변동 패턴 틀림, 북극–북방 정점 1–2개월 지연 | ↓ |
| B6 | Gier et al. 2024, *Biogeosciences* 21, 5321–5360. doi:10.5194/bg-21-5321-2024 | CMIP6 LAI 편차는 CMIP5의 절반 이하지만 과대 잔존. **GFDL-ESM4 북부 고위도 큰 양편차** | PDF |
| B7 | Park & Jeong 2021, *ERL* 16, 034027. doi:10.1088/1748-9326/abe2cf | ESM의 LAI (본문 수치 미확인) | ↓ |

## C. GFDL LM4 계열
| # | Citation | LAI 관련 보고 | 파일 |
|---|---|---|---|
| C1 | **Shevliakova et al. 2024, *JAMES* 16, e2023MS003922. doi:10.1029/2023MS003922** | LM4.1 전용. LAI=잎생물량×SLA. MODIS 대비 **북방·열대 일부 과대, 서부 아마존 과소**, ESM2G 대비 편차 ~50 %↓. 침엽수 툰드라 확장(N·생물지리 한계 없음), 방목 5 %/일(LAI<1이면 방목 중단 — 하한이 아니라 문턱)로 목초지 과소, 이모작·관개 없음, 열대 초본 경쟁 과대. PPA 목표 crown LAI*: 열대 6.0, 상록침엽 5.0, 온대 3.5, 초본 2.5 | PDF |
| C2 | Dunne et al. 2020, *JAMES* 12, e2019MS002015. doi:10.1029/2019MS002015 | ESM4.1 결합 개요(LAI 평가는 C1로 위임) | ↓ |
| C3 | Zhao et al. 2018a,b, *JAMES* 10, 691–734 / 735–769. doi:10.1002/2017MS001208, 10.1002/2017MS001209 | AM4.0/LM4.0 (LAI 내용 미확인) | ↓ |
| C4 | Weng et al. 2015, *Biogeosciences* 12, 2655–2694. doi:10.5194/bg-12-2655-2015 | LM3-PPA — lm4P PPA cohort의 원형 | PDF |
| C5 | Weng et al. 2017, *Glob. Change Biol.* 23, 2482–2498. doi:10.1111/gcb.13542 | 상록/낙엽 분포가 N 피드백에 의존 (우리 설정 N off) | ↓ |
| C6 | Weng et al. 2019, *Biogeosciences* 16, 4577–4599. doi:10.5194/bg-16-4577-2019 | 경쟁(PPA)이 N·CO₂ 반응을 바꿈 → 추세가 구조에 의존 | PDF |
| C7 | Martínez Cano et al. 2020, *Glob. Change Biol.* 26, 4478–4494. doi:10.1111/gcb.15188 | LM3PPA-TV 열대 allometry·배분 | ↓ |
| C8 | Pak et al. 2021, *Ocean Sci. J.* 56, 18–45. doi:10.1007/s12601-021-00001-7 | KIOST-ESM(CMIP6) 개요, LAI 평가 없음 | ↓ |

미확인: Song 2021의 GFDL-ESM4 개별 수치, LM4.0 LAI 처리, LM4.2/ESM4.5 기술논문(찾지 못함 → 포스터엔 "LM4.1 계열"), LM4 phenology·Leuning 민감도 정량 논문.

## 우리 결과(ctl vs GIMMS, LM4 notes §13.66)와의 연결
| 선행연구 보고 | 우리 결과 | 판정 |
|---|---|---|
| 모델 LAI 과대 (B1–B3, B5, B6) | 전구 +54 % | 일치, 크기 큼 |
| LM4.1 북방 과대 (C1, B6) — 결합모델 온난·습윤 편차 탓으로 설명 | 오프라인(WFDE5)에서도 50–70N **+57 %** | **결합 편차 없이도 남음 = 지면모델 자체 원인** (포스터 핵심 기여) |
| 늦은 휴면·성장기 과다 (B2, B3, B5) | 한대 9월 2.87 vs 1.16 | 일치 |
| TRENDY 추세 과대 (B3) | 2001–2020 **−0.11 vs +0.28 %/yr** (남반구 주도) | **반대** — lm4P 고유 문제 |
| 목초지 과소(C1) vs CMIP6 비산림 과대(B5) | 남반구 온대 +113 % | 확인 필요 (PFT별 분해) |

## D. 우리 그룹·전신 과제 / 기존 확보분 (2026-10-04 추가)
| # | 문헌 | 핵심 | 파일 |
|---|---|---|---|
| D1 | **Kim, D., Lee, M.-I., Seo, E. (2019) *J. Climate* 32, 127–143.** Improvement of soil respiration parameterization in a DGVM and its impact on the simulation of terrestrial carbon fluxes | CLM4 고정 Q10=1.5 → 토양온도·수분 다변량회귀로 **식생 17종별·시공간 변동 Q10**(Qi 2002 방법, Hashimoto 2015 Rs). 고위도 Rh 과소 50 % 이상 개선, 시베리아 GPP 과소 개선 — **경로는 분해→질소 무기화→GPP** | `lm4/LAI/reference/05_Kim2019_Q10_reparameterization_template_JCLI.pdf` (사용자가 9/11 "방법론 템플릿"으로 지정) |
| D2 | UNIST (2019) 기후예측 시뮬레이터를 위한 지면-대기 탄소순환 모형 개발 최종보고서 (책임 이명인, 위탁 전남대 정지훈), 과기정통부 기후변화대응기술개발사업 | D1의 보고서판 + GAIA-ESM(CLM4) 결합, CO₂ 계절진동, phenology 오차 | `reference/UNIST2019_…최종보고서(이명인,위탁정지훈).pdf` |
| D3 | GAIA 지구시스템 모형을 이용한 기후변화 진단 및 예측 최종보고서 (2009–2019, 책임 이재학) | 전신 과제 | `reference/GAIA 지구시스템 모형을 이용한 기후변화 진단 및 예측 최종보고서.pdf` |
| D4 | CRESCENDO (2025) *Biogeosciences* 22, 7117–7135. doi:10.5194/bg-22-7117-2025 — Plant phenology evaluation of CRESCENDO land surface models | 다중모델 phenology/LAI 편차 기준선 | `lm4/LAI/reference/04_CRESCENDO2025_LAI_evaluation_BG.pdf` |

※ `lm4/LAI/reference/`(9/11 확보, 목록 `_받을것.md`)에 Weng 2015·2019, Shevliakova 2024, Martínez Cano 2020, Medlyn 2002, Bernacchi 2001, Paulsen & Körner 2014 등이 이미 있음 — 이 폴더 PDF와 일부 중복.

## E. 가을 phenology 선례 — 하지·일장 기준 (2026-10-06 추가, LM4 notes §13.69 패치 근거)
| # | 문헌 | 핵심 | 파일 |
|---|---|---|---|
| E1 | Lawrence et al. (2019) *JAMES* 11, 4245–4287. doi:10.1029/2018MS001583 + CLM5 Technical Note (seasonal-deciduous phenology) | **CLM4/4.5/5 표준**: 잎 켜기 = **동지 이후** 토양온도 GDD 적산, 잎 끄기 = **하지 이후** 일장 < 10.92 h(≈11 h, 전 지구 공통). 가을을 일장만으로 결정 | 미확보 |
| E2 | **Birch et al. (2021) *Geosci. Model Dev.* 14, 3361.** doi:10.5194/gmd-14-3361-2021 — Addressing biases in Arctic–boreal carbon cycling in CLM5 | 증상이 우리와 같음(한대 가을 생산성이 늦게까지 과대). 일장 문턱을 **65°N 이북 15 h → 45°N 11 h 선형**으로 변경. 켜기는 GDD 대신 토양온도(10일)>0 °C·최저기온(5일)>0 °C·적설<10 cm. **전 지구 공통 11 h는 북극에 안 맞았다 = 일장 문턱은 위도 의존** | 미확보 (open access) |
| E3 | **Zohner et al. (2023) *Science* 381, eadf5098.** doi:10.1126/science.adf5098 — Effect of climate warming on the timing of autumn leaf senescence reverses after the summer solstice | 관측: 북반구 숲 84 %에서 **하지 전** 온난화는 낙엽 시작을 1.9±0.1 일/°C 앞당기고, **하지 후** 온난화는 낙엽 기간을 2.6±0.1 일/°C 늘림 → "하지 이후" 조건의 생물학적 근거 | 미확보 |

우리 패치의 위치: CLM = 가을을 **일장만**, LM4p·JULES·LPJ = **기온만**, §13.69 패치 = 하지 이후 일장(<14 h)으로 문을 열고 기온(<10 °C)으로 날짜를 정하는 **결합형**. 14 h 고정은 E2가 지적한 위도 의존 문제를 그대로 가짐(한계로 명시).
미확인(기억 기반, 서지·수치 재확인 필요): White et al. 1997 *GBC*(일장+토양온도 낙엽 모형, CLM 원형), Delpierre et al. 2009 *Agric. For. Meteorol.*(일장 의존 냉각적산 낙엽 모형), JULES·LPJ가 기온만 쓴다는 점.

## F. 선행연구는 무엇과 비교했나 — 지면모델 phenology 평가·개선 (2026-10-08 웹 확인)

| 연구 | 모델 | 비교 자료 | SOS/EOS 정의 | 우리와 관련된 결과 |
|---|---|---|---|---|
| Peano et al. 2021, *Biogeosciences* 18, 2405–2428, doi:10.5194/bg-18-2405-2021 (CRESCENDO Part 1) | CLM4.5, CLM5.0, JULES-ES, JSBACH, LPJ-GUESS, ORCHIDEE, ISBA-CTRIP (**LM4 없음**) | 위성 LAI 3종: LAI3g(GIMMS), MODIS, CGLS (2000–2011), ESA CCI 토지피복 | LAI 연주기 진폭 **20 %** 문턱(4GST) | 모델 평균 EOS는 오히려 **≈0.5개월 이름**; EOS 정확 격자 ≈25 %(±1개월 허용 시 ≈45 %), SOS 16 % → **LM4+의 늦은 EOS는 다른 모델과 반대 방향**(논의 거리) |
| Li et al. 2024, *JGR-Biogeosciences* 129, e2024JG008261 | CLM5.0, CLM4.5 | MODIS LAI·phenology, PhenoCam, FLUXNET 지점 | — | CLM5는 LAI 크기는 나아졌으나 **계절 주기는 CLM4.5보다 나빠짐**; 봄 시작이 관측보다 평균 ≈30일 늦음(상록 PFT) |
| MacBean et al. 2015, *Biogeosciences* 12, 7185–7208, doi:10.5194/bg-12-7185-2015 | ORCHIDEE | MODIS NDVI v5 (모델 fAPAR와 대응)로 phenology 파라미터 **최적화** | — | 한대·온대 낙엽 PFT에서 **노화 시작이 앞당겨지며** 오차 감소, 북반구 생장기 최대 30일 단축 → 우리와 같은 방향의 수정 선례 |
| Collier et al. 2018, *JAMES* 10, 2731–2754 (ILAMB) | 벤치마크 체계 | GPP: FLUXCOM 등 · LE/SH: FLUXNET, GBAF(=FLUXCOM 계열) · ET: GLEAM, MODIS · 알베도: CERES, GEWEX.SRB · LAI: AVHRR(GIMMS), MODIS | — | **플럭스 비교의 표준 조합** → 우리 구성(GLEAM·FLUXCOM-X·GLASS)의 근거 |
| Delpierre et al. 2009 (프랑스 낙엽수) | 노화 모델 | 지상 관측 | — | 낮 길이가 노화를 시작시키고, 낮 길이에 민감한 냉각 적산(cold degree-day)으로 진행 → "낮 길이 × 기온" 연속형 모델의 원형 |
| Blümel & Chmielewski 계열 / PEP725 위성–지상 비교 | 위성 phenology 검증 | PEP725 지상 관측 수천 건 | — | 위성 SOS/EOS가 자작나무·너도밤나무 지상 관측과 잘 맞음 → 서유럽 EOS 검증 자료로 사용 가능 (서지 상세 미확인) |
| Moon et al. 2022 (온대 낙엽 활엽수 12종) | 관측 분석 | 지상·위성 | — | 기온도 영향을 주지만 **낮 길이가 모든 종에서 가장 강한 통제** (서지 상세 미확인) |

정리: phenology 자체는 **위성 LAI 다중 자료(GIMMS + MODIS + CGLS)**와 **PhenoCam/FLUXNET/PEP725 지점**으로, 플럭스는 **ILAMB 조합(FLUXCOM·GLEAM·CERES/MODIS 알베도·FLUXNET)**으로 평가하는 것이 표준. 새로 필요한 자료: MODIS LAI 또는 MCD12Q2, CGLS LAI(선택), PhenoCam·FLUXNET2015·PEP725.

### F-추가. Murray-Tortarolo et al. 2013, Remote Sens. 5, 4819–4838, doi:10.3390/rs5104819 (PDF 보유: `MurrayTortarolo2013_RemoteSens_LSM_LAI_HighLat.pdf`, 2026-10-08 원문 확인)
- 대상: TRENDY 오프라인 DGVM 8개(CLM4CN, LPJ, LPJ-GUESS, ORCHIDEE, OCN, SDGVM, TRIFFID, VEGAS; **LM 계열 없음**) vs GIMMS3g 기반 ANN LAI, 1986–2005, 30°N 이북, 월 LAI.
- 정의(§2.5): 진폭 **20 %** 문턱(월 단위, 문턱 위 첫 달 = onset, 마지막 달 = dormancy), **진폭 < 0.5 격자 제외**(우리와 같은 마스크), 여름 중 감소(가뭄 낙엽) 격자 제외.
- 결과: 모든 모델 LAI 과대(특히 북방림); **8개 중 7개가 생장기 과대, 주원인은 늦은 휴면(dormancy 20–60일 늦음, RMSE 31–63일)**, 특히 30–50°N; onset은 모든 모델이 15–20일 늦음; GPP로 같은 방법을 쓰면 휴면이 277 ± 7일로 LAI(315 ± 10일)보다 훨씬 이름 → "잎은 남아 있지만 광합성은 이미 멈춤"; 결론 "deciduous phenology, 특히 leaf shedding 개선 필요". 열적 기준(LPJ류)이 복잡한 phenology보다 생장기 길이를 더 잘 맞춤.
- 우리와의 관계: 같은 결론(늦은 휴면·봄도 늦음)을 LM4+에서 오프라인으로 재확인. 단 정의가 20 %라, 우리 20 % 시험(NEU·NWN ΔEOS ≈ 0)과 수치 직접 비교는 주의. GPP 휴면 비교는 우리 플럭스 분석에 그대로 쓸 수 있는 아이디어.

### F-추가 2. Park, H. & Jeong, S. (2021). Leaf area index in Earth system models: how the key variable of vegetation seasonality works in climate projections. *Environ. Res. Lett.* 16, 034027. doi:10.1088/1748-9326/abe2cf (PDF 보유: `ParkJeong2021_ERL_LAI_in_ESMs.pdf`, 2026-10-08 원문 확인; 저자는 정수종 교수 연구실)
- 대상: CMIP5·CMIP6 ESM 14개(BCC, CanESM, CESM, IPSL, MIROC, MPI, NorESM 각 2세대; **GFDL·LM4 없음**), 30°N 이북 낙엽수림, 1982–2014, GIMMS LAI3g + CRU TS.
- 방법: 계절성 지표(연평균, 사인 진폭, 위상) + SOS/EOS/LOS(로지스틱 곡선 맞춤, Park et al. 2018); **연 최대 LAI < 0.5 격자 제외**(숲으로 한정).
- 결과: CMIP6 연평균 1.7 vs GIMMS 1.2 m² m⁻²(CMIP5 2.2), 진폭 0.9 vs 1.2(약함), 위상 226 vs 212 DOY(늦음). **EOS: GIMMS 261 DOY, CMIP5 +22 d, CMIP6 +18 d**; 지연은 >50°N에서 평균 20 d 초과, **낙엽 침엽수림·woodland에서 가장 뚜렷**. SOS 기온 민감도: 관측 −4.5 d K⁻¹, 모델 −2.2/−2.6(약함). **EOS 기온 민감도: 관측 +0.5 d K⁻¹**, 모델 +0.7/+0.8(모델 간 편차 큼). 최근 10년 변화도 대부분 모델이 잘못 재현.
- 표 1: **CESM2/CLM5는 낙엽 종료에 일장(daylength) 문턱 사용**, ORCHIDEE2.0은 cold stress·leaf age, CLM4는 일장+토양온도(활엽)·7일 연속 한랭(침엽).
- 함의(논의): 늦은 EOS는 광합성 영향은 작지만(가을 일사 적음) 과도한 유지호흡·증발산, 낮은 알베도 → 탄소·토양수분·현열/잠열 분배 편향. 결론: "낙엽수 phenology, 특히 leaf senescence 개선 필요".
- **우리에게 중요한 점**: (1) 같은 결론(EOS 지연, 북방·낙엽 침엽수에서 최대)이 CMIP ESM 14개에서 이미 보고됨 → 우리 기여는 이 목록에 없던 LM4+, 오프라인(결합 기후 편차 배제), 원인 규명(기온 단일 문턱 + 평활 지연), 낮 길이 규칙 시험. (2) 낮 길이 규칙의 위험: 관측 EOS는 가을 기온에 +0.5 d K⁻¹로 반응 → 순수 낮 길이 규칙은 민감도 ≈0이 될 수 있으니 다년 실행에서 EOS–기온 민감도를 반드시 점검. (3) CLM5가 이미 일장 문턱을 쓴다는 점 → 우리 규칙의 선례로 인용 가능. (4) 연 최대 LAI < 0.5 마스크는 숲 한정용 선례.

### F-추가 3. Park, H., Jeong, S.-J., Ho, C.-H., Park, C.-E. & Kim, J. (2018). Slowdown of spring green-up advancements in boreal forests. *Remote Sens. Environ.* 217, 191–202. doi:10.1016/j.rse.2018.08.012 (PDF 보유: `Park2018_RSE_spring_greenup_slowdown.pdf`, 2026-10-19 원문 확인)
- SOS = NDVI3g 로지스틱 맞춤 변곡점(상세식 Park et al. 2015). WD(1/1~SOS, <0 °C 일수)·PT·GT·PR 편상관/다중회귀. chilling은 의도적으로 제외. 요약은 `notes/findings.md` 2026-10-19 항목.

### F-추가 4. Park, H., Jeong, S.-J., Ho, C.-H., Kim, J., Brown, M.E. & Schaepman, M.E. (2015). Nonlinear response of vegetation green-up to local temperature variations in temperate and boreal forests in the Northern Hemisphere. *Remote Sens. Environ.* 165, 100–108. doi:10.1016/j.rse.2015.04.030 (PDF 보유: `Park2015_RSE_nonlinear_greenup_temperature.pdf`, 2026-10-19 원문 확인)
- 로지스틱 식 Eq. 1 원출처: NDVI(t) = −γ/(1+exp(−α(1−βt))) + δ, 변곡일 1/β(= 곡선 50 %), VGrate = αβγ/4. 요약은 `notes/findings.md` 2026-10-19 항목.

### F-추가 5. Murray, M.B., Cannell, M.G.R. & Smith, R.I. (1989). Date of budburst of fifteen tree species in Britain following climatic warming. *J. Appl. Ecol.* 26, 693–700. JSTOR 2404093 (PDF 보유: `Murray-DateBudburstFifteen-1989.pdf`, 2026-10-19 원문 확인)
- NCD–GDD 식 원출처: T = a + b·exp(r·C) (T: 1/1~, >5 °C; C: 11/1~, ≤5 °C 일수), 5그룹 계수 Table 1. 요약은 `notes/findings.md` 2026-10-19 항목.
