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
