# 지면모델(LSM)의 발전 — 세대별 해설 (학부생 수준)

작성 2026-10-03. 목적: 4개 LSM(CLM5·LM4p·JULES·Noah-MP)을 진단할 때 "이 모델이 어느 세대의 무엇을 갖고 있나"를
한눈에 보고, 설정 차이를 해석하는 근거로 쓰기 위함. 기준점은 CLM4 CNDV/BGC.
"(확인 필요)"는 기억에 기댄 세부사항 — 보고서 인용 전 원문 확인할 것.

---

## 0. 한 장 요약

| 세대 | 시기 | 새로 들어온 질문 | 핵심 아이디어 | 대표 모델·문헌 |
|---|---|---|---|---|
| 1. 양동이 | 1960–70s | 땅이 물을 얼마나 내보내나? | 토양 = 물 양동이 하나 | Manabe (1969) |
| 2. 식생–대기 교환 (SVAT) | 1980s | 식물이 증발을 어떻게 조절하나? | 캐노피·기공·다층 토양·복사 | BATS (Dickinson et al. 1986), SiB (Sellers et al. 1986) |
| 3. 광합성 결합 | 1990s | 기공은 왜 열고 닫나? | 기공 전도도 = 광합성의 함수 | SiB2 (Sellers et al. 1996), NCAR LSM (Bonan 1996), MOSES (Cox et al. 1999) |
| 4. 동적 식생 (DV) | 1996–2003 | 어떤 식물이 어디에 사나? | 탄소 저장 + 기후로 PFT 분포 변화 | IBIS (Foley et al. 1996), TRIFFID (Cox 2001), LPJ (Sitch et al. 2003) |
| 5. 탄소–질소 (C–N) | 2005–2012 | 질소가 성장을 제한하나? | 질소 흡수·무기화·침착·고정 | CLM4-CN (Thornton et al. 2007), O-CN (Zaehle & Friend 2010) |
| 6. 개체군 역학 (cohort) | 2001→2015~ | 숲은 몇 그루, 어떤 크기 구조인가? | 크기별 cohort, 빛 경쟁, 사망·유입 | ED (Moorcroft et al. 2001), PPA (Purves et al. 2008), FATES (Koven et al. 2020), LM3-PPA (Weng et al. 2015) |

세대 구분 자체는 Sellers et al. (1997)과 Pitman (2003)의 리뷰가 표준 참고문헌.
**각 세대는 앞 세대를 대체하지 않고 그 위에 쌓인다.** 지금 모델은 1–3세대 물리를 모두 갖고, 4–6세대를 옵션으로 켜고 끈다.

**식생 설정을 말할 때는 세 축으로 나눌 것** (같은 "동적 식생"이라는 말로 섞지 말 것):
- ① **C/N** — 탄소(와 질소)를 계산해 잎·줄기·뿌리·목재를 예측. **LAI는 여기서 나온다** (잎 탄소 × 비엽면적).
- ② **DV (생물지리)** — 어떤 PFT가 그 칸에 몇 % 사는가.
- ③ **cohort (개체군 역학)** — 나무의 크기·개수·나이 구조.

---

## 1. 양동이 모델 (1세대)

**비유**: 땅을 **구멍 난 양동이** 하나로 본다. 비가 오면 물이 차고, 넘치면 유출, 증발은 양동이가 얼마나 찼는지에 비례한다.

- 증발 = 잠재증발 × β, β = 토양수분 / (임계 토양수분). 양동이가 가득(약 15 cm 물)이면 β = 1.
- 식물·지면온도·눈의 세부는 없다. 지면 온도는 에너지 수지 하나로 진단.
- **의미**: 처음으로 "땅의 물 상태가 대기에 되먹임한다"를 기후모델에 넣었다. Manabe (1969)가 GFDL 기후모델에 도입.
- **한계**: 식물이 가뭄에 기공을 닫아 증발을 줄이는 것, 뿌리 깊이, 낮과 밤의 차이를 못 다룸. 증발이 너무 쉽게 일어나는 경향.
- **지금 남아 있는 흔적**: β 함수 개념은 지금 모델의 토양수분 스트레스 함수(예: JULES `fsmc`, CLM `btran`)로 이어짐.

## 2. 식생–대기 교환, SVAT (2세대)

**비유**: 양동이 위에 **잎으로 된 우산(캐노피)**을 씌운다. 잎에는 열고 닫는 **창문(기공)**이 있다.

- 새로 들어온 것: 캐노피 층(복사 흡수·반사), 기공 저항, 다층 토양(뿌리층), 캐노피 차단 강수, 눈 층, 거칠기 길이.
- **증산 = 잎 표면과 공기의 수증기 차 / (공기 저항 + 기공 저항)**. 기공 저항은 빛·기온·수증기압차·토양수분의 경험식으로 결정(Jarvis 형).
- 대표: **BATS** (Dickinson et al. 1986, NCAR) — 훗날 CLM의 뿌리 중 하나. **SiB** (Sellers et al. 1986).
- **의미**: 숲과 초지, 사막의 차이(알베도·거칠기·증산)가 기후에 주는 영향을 처음 정량화. 아마존 벌채 실험 같은 연구가 가능해짐.
- **한계**: 기공 저항이 경험식이라 CO₂가 늘 때 반응을 못 넣음. 식생은 지도로 처방(LAI·피복이 고정).
- **우리 모델에서**: Noah LSM (Chen et al. 1996; Ek et al. 2003), GFDL LaD/LM2 (Milly & Shmakin 2002)가 이 단계. Noah-MP의 DVEG=1·3·4(처방 LAI)도 식생 측면에선 이 수준.

## 3. 광합성 결합 (3세대)

**비유**: 창문(기공)을 **열 이유**가 생겼다 — 창을 열어야 CO₂가 들어와 **광합성(돈 벌기)**을 하지만, 열면 물이 나간다(비용).

- **핵심 식 두 개**
  - Farquhar et al. (1980) 광합성 모델: 광합성 = min(효소(Rubisco) 제한, 빛(전자전달) 제한, (C4는 PEP) 제한). C4는 Collatz et al. (1992).
  - Ball, Woodrow & Berry (1987) 기공 모델: 기공 전도도 ∝ 광합성 × 상대습도 / 잎 표면 CO₂. (Medlyn et al. 2011이 최적화 이론 버전)
- 이 둘이 묶이면서 **CO₂ 증가 → 기공이 덜 열려도 같은 광합성 → 증산 감소**(CO₂ 생리 효과)를 계산할 수 있게 됨.
- 대표: **SiB2** (Sellers et al. 1996), **NCAR LSM** (Bonan 1996), **MOSES** (Cox et al. 1999; JULES의 전신).
- **의미**: 물·에너지·탄소 교환이 하나의 식물 생리로 묶임. 이때부터 GPP를 계산하고 FLUXNET과 비교할 수 있다.
- **한계**: 식물의 "몸집"(잎·줄기·뿌리 탄소)은 아직 고정. LAI는 위성 기후값으로 처방 — **CLM의 SP 모드가 정확히 이 단계**.

## 4. 동적 식생, DV (4세대)

**두 가지가 함께 들어왔다 — 이걸 구분하는 게 중요.**
- (a) **탄소 저장(몸집 예측)**: 번 탄소(NPP)를 잎·줄기·뿌리에 나눠 쌓고, 잎이 늘면 LAI가 는다. **LAI = 잎 탄소 × 비엽면적(SLA)**.
- (b) **생물지리(DV)**: 기후가 바뀌면 **어떤 PFT가 사는지**가 바뀐다.
  - 규칙 방식: 기온·강수 한계표(생물기후 envelope)로 PFT 생존/정착 결정 — LPJ, CLM DGVM/CNDV, LM3V, LM4p `do_biogeography`.
  - 경쟁 방식: PFT끼리 면적을 두고 Lotka–Volterra 경쟁 — TRIFFID (`l_veg_compete`).

- 대표: IBIS (Foley et al. 1996), **TRIFFID** (Cox 2001), **LPJ** (Sitch et al. 2003), CLM-DGVM (Levis et al. 2004), LM3V (Shevliakova et al. 2009).
- **역사적 사건**: **Cox et al. (2000, Nature)** — HadCM3LC에 TRIFFID를 결합해 "온난화 → 아마존 숲 고사 → 탄소 방출 → 추가 온난화"라는 양의 되먹임을 보임. 탄소–기후 되먹임 연구의 출발점. 이어 Friedlingstein et al. (2006, C4MIP)이 여러 모델에서 되먹임 크기가 크게 다름을 보임.
- **한계**: 질소 제한이 없어 CO₂ 비료효과가 과대. 숲을 "큰 잎 하나"로 봐서 나무 크기·나이 구조·교란 회복을 표현 못 함.
- **우리 1차년도 설정**: 4개 모델 모두 **(a)는 켜고 (b)는 끔.** 즉 "탄소로 LAI 예측, PFT 분포 고정".
  CLM5 BGC, JULES TRIFFID+`l_veg_compete=F`, LM4p `do_biogeography=F`, Noah-MP DVEG=5.

## 5. 탄소–질소, C–N (5세대)

**비유**: 돈(탄소)만 있으면 집(식물 몸)을 짓는 게 아니라 **벽돌(질소)**도 있어야 한다. 벽돌이 부족하면 돈이 있어도 못 짓는다.

- 식물 조직은 일정한 C:N 비를 가져야 하므로, 토양의 무기 질소(NH₄⁺, NO₃⁻)가 부족하면 성장이 제한된다.
- 질소의 출입: **침착**(대기에서 내려옴, 산업·농업 지역에 많음) · **생물학적 고정**(콩과식물 등) · **무기화**(토양 유기물이 분해되며 질소 방출) · 유실(용탈, 탈질).
- **핵심 결과**: 질소를 넣으면 CO₂ 비료효과로 인한 탄소 흡수가 **줄어든다**(Thornton et al. 2007; Zaehle et al. 2010). 대신 온난화로 분해가 빨라지면 질소가 풀려나 성장이 늘 수도 있어, 되먹임 부호가 복잡해짐.
- 대표: **CLM4-CN** (Thornton et al. 2007, 2009; CESM1에서 CMIP5 최초급), O-CN (Zaehle & Friend 2010), JULES-CN (Wiltshire et al. 2021).
- **중요한 함의 — 토양 탄소가 식물에 되먹임하는 경로가 생긴다.** 빠른 토양·낙엽풀이 분해되며 질소를 내놓으므로, 질소 모델에서는 토양 빠른 풀까지 평형이어야 식물이 안정된다.
- **우리 모델**: CLM5만 켬(`use_cn`, FUN, flexible C:N). LM4p·JULES는 기능 있으나 끔, Noah-MP는 기능 없음. → "CLM5만 GPP가 다르다"면 1순위 의심 = 질소 제한.

## 6. 개체군 역학, cohort (6세대)

**비유**: 숲을 "초록 카펫(큰 잎 하나)"이 아니라 **키가 다른 나무들이 사는 마을**로 본다. 큰 나무가 햇빛을 먼저 받고, 그늘의 작은 나무는 천천히 자라거나 죽는다. 큰 나무가 쓰러지면 빈자리에 새 나무가 자란다.

- **ED, Ecosystem Demography** (Moorcroft, Hurtt & Pacala 2001): 크기·나이가 같은 나무 무리를 **cohort**로 묶고, 교란 이후 경과 시간이 같은 땅을 **patch**로 묶어 계산량을 줄임.
- **PPA, Perfect Plasticity Approximation** (Purves et al. 2008): 키 큰 나무부터 캐노피를 채우고, 캐노피가 차면 그 아래는 그늘층 — 빛 경쟁을 단순하게 계산하는 방법.
- 대표: **FATES** (Fisher et al. 2015; Koven et al. 2020, CLM/E3SM에 연결), **LM3-PPA / LM4.1** (Weng et al. 2015; GFDL ESM4), LPJ-GUESS(개체 기반).
- **무엇이 좋아지나**: 교란(화재·벌채·가뭄 사망) 후 회복 속도, 숲의 나이 구조, 가뭄에 큰 나무가 먼저 죽는 현상, 종 공존. 관측(산림 인벤토리, 라이다 수고)과 직접 비교 가능.
- **대가**: 계산량이 매우 큼(우리 LM4p는 cohort 143,546개, UFS LM4 단일 cohort 대비 37배). **목재·숲 구조가 평형에 가는 데 오래 걸린다** — 우리 LM4p spin-up이 느린 이유.
- **DV와의 관계**: FATES 기본은 여러 PFT를 함께 키워 **경쟁의 결과로** 분포가 나온다(DV가 저절로 나옴). LM4p는 cohort 경쟁은 켜고, 종 분포는 규칙 방식 `do_biogeography`로 따로 켜고 끈다(지금은 끔).
- 리뷰: Fisher et al. (2018, GCB) "Vegetation demographics in Earth System Models".

---

## 7. 4개 모델의 계보

### CLM (NCAR) — 커뮤니티 통합형
BATS(1986) + NCAR LSM(1996) + IAP94 → **Common Land Model** (Dai et al. 2003) → CLM2/3 + DGVM (Levis et al. 2004)
→ CLM3.5 (수문 개선) → **CLM4** (CN + CNDV, Lawrence et al. 2011) → **CLM4.5** (BGC: 층별 토양 C/N + CENTURY)
→ **CLM5** (Lawrence et al. 2019: BGC 기본, FUN, 식물 수리학, CNDV 미지원, FATES 옵션) → CTSM.
우리: `release-clm5.0.37`, BGC(crop 없음), CNDV 코드 잔존(`use_cndv=.false.`, `-dynamic_vegetation` 옵션), FATES `sci.1.30.0_api.8.0.0`.

### GFDL LM — 토지이용·cohort 선도
Manabe bucket(1969) → LaD/**LM2** (Milly & Shmakin 2002) → **LM3/LM3V** (Shevliakova et al. 2009; Milly et al. 2014: 탄소 + DV, 토지이용 타일)
→ LM4.0 (Zhao et al. 2018) → **LM4.1** (PPA cohort, Weng et al. 2015; ESM4.1, Dunne et al. 2020) → **lm4P** (질소 코드 추가, KIOST-ESM2에선 끔).
우리: `do_ppa=T`(끄면 소스 주석상 "LM3 mode"), `do_biogeography=F`, 질소 off.

### JULES (Met Office/UK) — 탄소–기후 되먹임 원조
MOSES (Cox et al. 1999), MOSES2 타일 (Essery et al. 2003) + **TRIFFID** (Cox 2001) → HadCM3LC (Cox et al. 2000)
→ **JULES** 커뮤니티화 (Best et al. 2011; Clark et al. 2011) → HadGEM2-ES → GL7 (Wiltshire et al. 2020, 9 PFT 물리 설정)
→ **JULES-ES** (UKESM1; Sellar et al. 2019; Wiltshire et al. 2021, 질소 켬).
우리: vn7.4, 5 PFT + 4 비식생, TRIFFID 켬, `l_veg_compete=F`, `l_nitrogen=F`(질소 침착 자료는 준비됨, JULES notes §18).

### Noah 계열 (NCEP/NCAR/대학) — 예보용, 물리 옵션형
OSU LSM (Pan & Mahrt 1987) → **Noah LSM** (Chen et al. 1996; Ek et al. 2003; 현업 예보 Eta/NAM/GFS/WRF)
→ **Noah-MP** (Niu et al. 2011; Yang et al. 2011: 다중 물리 옵션, Dickinson et al. 1998 동적 잎 모델) → 작물(Liu et al. 2016) → v5 (He et al. 2023).
우리: v5.2.1, DVEG=5(LAI 예측, 최대 식생비율 고정), 질소 기능 없음.

### "CLM이 리더인가?"
기능별 원조는 흩어져 있다 — 기후모델 내 탄소+DV 결합은 **JULES/TRIFFID**, 토지이용 타일은 **GFDL LM3V**, ESM 질소 결합은 **CLM4-CN**,
개체군 역학은 **ED(학계)**에서 FATES·LM4로, 물리 옵션 다양성은 **Noah-MP**. **CLM은 이 기능들을 가장 넓게 모으고 가장 많이 쓰이는
커뮤니티 모델**이라는 뜻에서 리더. 같은 기능이 모델마다 다르게 구현돼 있다는 것이 곧 다중 LSM 비교의 **구조오차**.

---

## 8. CMIP6에서는 어디까지였나

- **배경**: CMIP6에서 지면 관련 MIP — C4MIP (Jones et al. 2016, 탄소–기후 되먹임), LUMIP (Lawrence et al. 2016, 토지이용),
  **LS3MIP** (van den Hurk et al. 2016, 지면 offline·결합 비교 — 우리 과제와 가장 가까움).
- **사실상 표준이 된 것 (지구시스템모델 기준)**
  - 3세대 광합성–기공 결합 + **4세대 (a) 탄소 저장(LAI 예측)** — 탄소 순환 ESM이라면 기본.
  - 토지이용 변화(LUH2, Hurtt et al. 2020) 반영.
- **절반쯤 들어온 것**: **질소 순환** — 탄소–기후 되먹임 분석 ESM 11개 중 **6개**(ACCESS-ESM1.5, CESM2, MIROC-ES2L, MPI-ESM1.2-LR,
  NorESM2-LM, UKESM1-0-LL). CMIP5는 8개 중 2개였음 (Arora et al. 2020). 질소를 넣은 모델은 지면 탄소–농도 되먹임이 작게 나옴.
- **소수만**: 층별 토양 탄소(CESM2, NorESM2 정도; Gaillard et al. 2026 GMD 서술), 영구동토 탄소, 화재 결합,
  **DV(생물지리) 결합** 일부, **cohort(6세대)는 GFDL ESM4 등 극소수**.
- **알려진 약점**: 영구동토 활동층 두께 모의 부족, 토양 탄소 spin-up 미수렴, 모델 간 지면 탄소 흡수 차이가 해양보다 큼.

## 9. CMIP7에서는 어디까지 가야 하나

- **가장 큰 변화**: CMIP7은 **CO₂ 배출량 구동(emissions-driven) 실험**에 참여하도록 프로토콜을 다시 짰다 (Dunne et al. 2025, GMD 18, 6671).
  즉 대기 CO₂ 농도를 처방하지 않고 모델이 탄소 순환으로 **스스로 계산** → 지면 탄소 흡수가 틀리면 기온 예측까지 틀린다.
  "역사기간 CO₂ 농도를 배출량으로부터 재현하는 것"이 모델 신뢰성 기준으로 강조됨.
- **그래서 지면모델에 요구되는 것 (방향, 일부 확인 필요)**
  1. **탄소 순환의 정량 신뢰성**: 역사기간 지면 탄소 흡수(Global Carbon Budget과 비교), spin-up 수렴 — 느린 풀 미수렴은 배출 구동에서 바로 CO₂ 오차가 됨.
  2. **질소(와 인) 제한**: CMIP6에서 절반이던 것이 사실상 기본 기대치로 (확인 필요).
  3. **영구동토 탄소·층별 토양 탄소**: 다음 세대 모델에 필요하다는 공감대 (Gaillard et al. 2026 등).
  4. **토지이용 강제 개선**: 개선된 토지이용 조화 자료 (Chini et al. 2023 계열, LUH3).
  5. **화재, 습지 메탄** 등 추가 탄소 경로 (확인 필요).
  6. **식생 개체군 역학(6세대)**: 아직 기본은 아니지만 선도 그룹(FATES, LM4)은 이미 탑재 — "가는 방향".
- **우리 과제와의 연결**: KIOST-ESM2(LM4p)는 cohort(6세대)는 갖췄으나 **질소가 꺼져 있다** → CMIP7 배출 구동을 목표로 한다면
  질소·토양 탄소 spin-up이 개선 1순위 후보 (Phase 2 "물리과정 고도화"와 직결).

---

## 10. 참고문헌 (주요)

- Arora, V. K. et al. (2020) Carbon–concentration and carbon–climate feedbacks in CMIP6 models and their comparison to CMIP5 models. *Biogeosciences* 17, 4173–4222.
- Ball, J. T., Woodrow, I. E., Berry, J. A. (1987) A model predicting stomatal conductance… *Progress in Photosynthesis Research*.
- Best, M. J. et al. (2011); Clark, D. B. et al. (2011) The Joint UK Land Environment Simulator (JULES), Parts 1 & 2. *GMD* 4.
- Bonan, G. B. (1996) A Land Surface Model (LSM version 1.0)… NCAR Technical Note.
- Chen, F. et al. (1996) *JGR*; Ek, M. B. et al. (2003) Implementation of Noah land surface model advances… *JGR* 108.
- Collatz, G. J., Ribas-Carbo, M., Berry, J. A. (1992) Coupled photosynthesis–stomatal conductance model for leaves of C4 plants. *Aust. J. Plant Physiol.*
- Cox, P. M. et al. (1999) The impact of new land surface physics on the GCM simulation of climate and climate sensitivity. *Clim. Dyn.*
- Cox, P. M. et al. (2000) Acceleration of global warming due to carbon-cycle feedbacks in a coupled climate model. *Nature* 408.
- Cox, P. M. (2001) Description of the TRIFFID dynamic global vegetation model. Hadley Centre Technical Note 24.
- Dai, Y. et al. (2003) The Common Land Model. *BAMS* 84.
- Dickinson, R. E. et al. (1986) Biosphere–Atmosphere Transfer Scheme (BATS)… NCAR Technical Note.
- Dunne, J. P. et al. (2025) An evolving CMIP7 and Fast Track in support of future climate assessment. *GMD* 18, 6671–6700.
- Farquhar, G. D., von Caemmerer, S., Berry, J. A. (1980) A biochemical model of photosynthetic CO₂ assimilation in leaves of C3 species. *Planta* 149.
- Fisher, R. A. et al. (2018) Vegetation demographics in Earth System Models: A review of progress and priorities. *GCB* 24.
- Foley, J. A. et al. (1996) An integrated biosphere model of land surface processes… (IBIS). *GBC* 10.
- Friedlingstein, P. et al. (2006) Climate–carbon cycle feedback analysis: results from the C4MIP model intercomparison. *J. Climate* 19.
- Gaillard, R. et al. (2026) IPSL-Perm-LandN… *GMD* 19, 661.
- Jones, C. D. et al. (2016) C4MIP… *GMD* 9; Lawrence, D. M. et al. (2016) LUMIP… *GMD* 9; van den Hurk, B. et al. (2016) LS3MIP… *GMD* 9.
- Koven, C. D. et al. (2020) Benchmarking and parameter sensitivity of physiological and vegetation dynamics using FATES… *Biogeosciences* 17.
- Lawrence, D. M. et al. (2011) *JAMES* 3 (CLM4); Lawrence, D. M. et al. (2019) The Community Land Model version 5. *JAMES* 11.
- Levis, S. et al. (2004) The Community Land Model's Dynamic Global Vegetation Model (CLM-DGVM). NCAR Technical Note.
- Manabe, S. (1969) Climate and the ocean circulation: I. The atmospheric circulation and the hydrology of the earth's surface. *Mon. Wea. Rev.* 97.
- Milly, P. C. D., Shmakin, A. B. (2002) Global modeling of land water and energy balances (LaD). *J. Hydrometeorol.* 3.
- Moorcroft, P. R., Hurtt, G. C., Pacala, S. W. (2001) A method for scaling vegetation dynamics: the ecosystem demography model. *Ecol. Monogr.* 71.
- Niu, G.-Y. et al. (2011); Yang, Z.-L. et al. (2011) The community Noah land surface model with multiparameterization options (Noah-MP). *JGR* 116.
- Pitman, A. J. (2003) The evolution of, and revolution in, land surface schemes designed for climate models. *Int. J. Climatol.* 23.
- Purves, D. W. et al. (2008) Predicting and understanding forest dynamics using a simple tractable model. *PNAS* 105.
- Sellers, P. J. et al. (1986) A simple biosphere model (SiB)… *J. Atmos. Sci.* 43; Sellers, P. J. et al. (1996) SiB2. *J. Climate* 9;
  Sellers, P. J. et al. (1997) Modeling the exchanges of energy, water, and carbon between continents and the atmosphere. *Science* 275.
- Shevliakova, E. et al. (2009) Carbon cycling under 300 years of land use change… (LM3V). *GBC* 23.
- Sitch, S. et al. (2003) Evaluation of ecosystem dynamics… in the LPJ dynamic global vegetation model. *GCB* 9.
- Thornton, P. E. et al. (2007) Influence of carbon–nitrogen cycle coupling on land model response to CO₂ fertilization and climate variability. *GBC* 21.
- Weng, E. S. et al. (2015) Scaling from individual trees to forests in an Earth system modeling framework using a mathematically tractable model of height-structured competition. *Biogeosciences* 12.
- Wiltshire, A. J. et al. (2021) JULES-CN: a coupled terrestrial carbon–nitrogen scheme (JULES vn5.1). *GMD* 14.
- Zaehle, S., Friend, A. D. (2010) Carbon and nitrogen cycle dynamics in the O-CN land surface model. *GBC* 24.
- Zhao, M. et al. (2018) The GFDL global atmosphere and land model AM4.0/LM4.0. *JAMES* 10.
