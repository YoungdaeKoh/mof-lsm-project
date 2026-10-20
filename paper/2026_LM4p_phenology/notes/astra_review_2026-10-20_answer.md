**연구 방향은 타당하지만, 현재 결과가 뒷받침하는 주장은 “phenology의 구조적 문제를 진단하고 유망한 수정안을 찾았다”까지입니다.** 아직 “LM4p의 계절성과 탄소순환을 개선했다”거나 “coupled ESM에 적용할 준비가 끝났다”고 주장하기에는 부족합니다. 가을 수정은 근거가 강하고, 전역 τ5 봄 수정은 그대로 채택하기 어렵습니다.

브리프, 허용된 노트·실험 결과표·patch를 읽었습니다. 아래 수치는 저장소 기록에 근거하며 직접 재계산하지 않았습니다. `dayllat`과 `phasewfde5`는 완료 결과를 확인하지 못했으므로 예상 효과를 실험 결과로 취급하지 않았습니다.

**1. 현재 접근은 논문과 ESM 개선에 충분한가?**

**1년 paired experiment는 원인 진단에 적절하지만, 최종 검증 설계로는 부족합니다.** 동일 restart에서 시작하면 초기 상태 차이를 통제할 수 있고, 계산 자원이 제한된 상황에서 후보를 거르는 데 효과적입니다. 그러나 지금 실험은 엄밀한 의미의 one-parameter-at-a-time도 아닙니다.

- `daylspring5`는 **온도 평활시간 단축과 봄철 cold leaf-off 차단을 동시에 변경**합니다. 따라서 결과는 두 변경의 합성 효과입니다.
- `dayllat`은 기존 종별 13/12 h에서 공통 위도식으로 바뀝니다. DL과의 차이는 slope 추가뿐 아니라 종별 intercept 차이의 제거도 포함합니다.
- 가을 leaf-off는 GDD를 reset합니다. 따라서 다년 실험에서 가을과 다음 봄의 상호작용은 구조적으로 가능합니다.

논문에서는 이를 **규칙별 intervention 또는 ablation experiment**라고 부르는 편이 정확합니다. 구조 변화와 parameter tuning도 구분해야 합니다. Photoperiod 도입과 on/off 분리는 구조 변경이고, 13 h·0.05 h/°·τ5의 선택은 parameterization입니다.

검토자가 가장 강하게 요구할 부분은 다음입니다.

| 필요한 검증 | 현재 결과에서 중요한 이유 |
|---|---|
| 독립 연도·지역 검증 | 2010과 이미 살펴본 climatology에 맞춘 개선인지 구분 |
| 계절곡선 전체 평가 | EOS50 개선이 감소 시작·속도의 오차 상쇄일 수 있음 |
| PFT·종 기여분별 진단 | c3grass 조정으로 실제 forest phenology를 대신 맞출 위험 |
| GPP 및 보조 flux 평가 | LAI timing 개선이 기능적 개선으로 이어지는지 확인 |
| 공통 executable·restart 검증 | 재컴파일 차이와 restart 상태 유실의 영향 분리 |

특히 [실험 결과표](/Volumes/data01/MOF_LSM_project/poster/2026_LM4p_LAI/data/daylspring5_2010.txt)는 결론을 제한합니다. 50–70N에서 DL→DLS5는 SOS를 +14.7→+7.9일로 개선하지만, 연중 LAI MAE는 **0.49→0.51로 악화**합니다. 반대로 ENA는 SOS가 −23일로 나빠져도 MAE는 0.38→0.34로 좋아집니다. **날짜와 크기 중 하나만 선택하면 서로 반대되는 결론이 나옵니다.**

LAI 3종 비교는 유지하되, 이를 독립 관측 3개의 검증이나 uncertainty confidence interval로 표현하지 마십시오. GIMMS consolidated와 AVHRR는 자료 계보를 공유하며, 제품 간 범위에는 공통 오차가 포함되지 않습니다.

FLUXCOM-X는 seasonal GPP 검증에 유용하지만 독립적인 직접 관측은 아닙니다. 특히 NEE interannual variability와 공간적 평균 NEE의 제약이 논문 자체에 명시되어 있습니다. **May–Jun GPP를 주요 기능 지표로, NEE는 GPP·respiration을 분해한 보조 지표로** 쓰는 것이 안전합니다. 가능하면 대표 flux tower나 PhenoCam 사례를 추가하십시오. [Nelson, Walther et al. (2024)](https://bg.copernicus.org/articles/21/5079/2024/bg-21-5079-2024.html)

Coupled test는 이 offline 논문의 필수조건으로 만들 필요는 없습니다. 다만 결론은 **“KIOST-ESM2에 이식할 후보 scheme”**으로 제한하고, coupled climate bias 개선은 별도 검증 대상으로 남겨야 합니다.

**2. τ5가 온대 봄을 너무 앞당기는 문제는 어떻게 풀어야 하는가?**

**현재의 전역 τ5는 채택하지 않는 것이 좋습니다.** Winter hold는 겨울 재개엽 문제를 줄이지만, 온대 spring forcing requirement의 부족을 해결하지 않습니다. 12 h 조건은 사실상 춘분 부근의 제한이므로, 그 이후에도 필요한 온도 누적과 dormancy 과정을 대신할 수 없습니다.

문헌에서 가져와야 할 것은 숫자보다 **과정의 구분**입니다.

- **CLM의 Arctic–boreal 수정:** Birch et al.은 5일 평균 minimum air temperature뿐 아니라 10일 평균 soil temperature와 snow depth를 함께 사용했습니다. LM4p의 canopy mean temperature를 지수평활하는 τ5와는 다른 formulation입니다. 이 논문은 북방에서 짧은 thermal response를 시험할 근거이지, LM4p 전역 τ5를 검증한 근거가 아닙니다. [Birch et al. (2021)](https://gmd.copernicus.org/articles/14/3361/2021/)
- **ORCHIDEE·JSBACH 계열:** PFT별 thermal requirement, chilling 및 soil-water 조건을 구분하는 방향이 참고됩니다. 다만 다른 모델의 문턱을 옮기면 temperature definition, GDD 시작일·reset, leaf growth 방식이 달라 의미가 바뀝니다. 모델 간 평가도 보편적인 최적 scheme을 제시하지 않습니다. [Peano et al. (2021)](https://bg.copernicus.org/articles/18/2405/2021/)
- **GSI:** minimum temperature·photoperiod·VPD의 제한을 결합하고, 후속 연구는 PFT와 제한요인별 반응시간을 구분합니다. 이는 단일 τ의 한계를 지지하지만, GSI 전면 도입은 현재 논문에 비해 큰 변경입니다. [Jolly et al. (2005)](https://www.frames.gov/documents/catalog/spa/jolly_nemani_running_2005.pdf), [Forkel et al. (2014)](https://bg.copernicus.org/articles/11/7025/2014/bg-11-7025-2014.pdf)
- **Chilling–forcing–photoperiod:** Caffarra et al.의 접근은 dormancy와 forcing에 대한 photoperiod 작용을 구분합니다. 종별 반응을 설명하는 근거이며, 모든 식생에 동일한 12 h floor를 적용하는 근거는 아닙니다. [Caffarra, Donnelly & Chuine (2011)](https://doi.org/10.3354/cr00983)

제 권고는 두 단계입니다.

**이번 논문의 최소 수정 후보:** acer와 temperate vegetation에는 기존 spring rule을 유지하고, **독립적으로 정의한 boreal cold-season c3grass에만 짧은 response time을 시험**하십시오. 이는 생리적 정답이 아니라, 과도한 전역 변경을 제한하는 검증 가능한 가설입니다. Boreal 구분은 SOS bias 지도를 보고 정하지 말고, 기존 biome 또는 사전에 고정한 climate classification으로 정의해야 합니다. 단순 50°N 절단은 진단용으로는 가능하지만 최종 formulation으로는 약합니다.

**후속 구조 개선:** woody deciduous vegetation에는 dormancy release–forcing–leaf expansion을 구분하고, grass에는 soil thaw·water availability와 thermal response를 중심으로 설계하십시오. c3grass와 acer를 같은 spring mechanism으로 고치는 것은 설득력이 약합니다.

추가로 중요한 점은 다음입니다.

- **“Chilling을 기각했다”는 표현은 너무 강합니다.** 현재 분석은 특정 chilling formulation이 2010 boreal SOS 지연을 충분히 해소하지 못했다는 뜻입니다. 온대 warm winter에서 premature leaf-out을 제한하는 역할까지 기각한 것은 아닙니다.
- τ를 단축하면 기존에 비활성처럼 보이던 GDD·soil-water gate가 새로운 병목이 됩니다. “CTRL에서 temperature gate가 98%를 지배했다”는 결과를 수정 후에도 적용하면 안 됩니다.
- 현재 cold leaf-off 차단은 `shortening`으로 계절을 구분합니다. 고위도에서는 봄 녹화가 하지 이후까지 이어질 수 있으므로 **하지가 곧 생리적 가을이라는 가정은 취약**합니다. RAR에서 SOS가 개선되지 않는 원인 후보이지만, 현재 자료로 확정할 수는 없습니다.
- Winter false-start 감소도 주의해서 읽어야 합니다. leaf-off 경로를 차단하면 잘못된 조기 개엽이 지속되어 “켜졌다 꺼지는 사건”만 감소할 수 있습니다. False-start 빈도와 함께 **겨울 LAI 및 첫 지속적 leaf-on 날짜**를 봐야 합니다.

**3. 위도 의존 autumn day-length rule은 정당화할 수 있는가?**

**가능합니다. 다만 “관측으로 입증한 photoperiod mechanism”보다 “관측에 제약된 effective parameterization”으로 제시해야 합니다.**

현재 근거는 temperature-only rule의 부족을 상당히 잘 보여줍니다. 그러나 EOS 날짜를 day length로 변환한 뒤 latitude에 회귀하는 것은 그 자체로 인과 검증이 아닙니다. **Day length는 latitude와 calendar date의 결정적 함수**이므로, 공간적 EOS 패턴만으로 photoperiod 제어를 독립적으로 식별할 수 없습니다.

다음 네 가지를 보완하면 방어력이 높아집니다.

1. **고정 13/12 h보다 위도식이 독립 지역·연도에서 실제로 나은지 검증하십시오.** 이미 전체 climatology를 보고 식을 만들었으므로, 같은 기간을 사후에 나누고 완전한 blind validation이라고 부르면 안 됩니다.
2. **단순 calendar-date baseline과 비교하십시오.** 동일한 수의 parameter를 가진 날짜 규칙보다 낫지 않다면, photoperiod의 추가 설명력을 강하게 주장하기 어렵습니다.
3. **EOS50와 senescence onset을 구분하십시오.** 관측 EOS50의 day length를 모델 leaf-off trigger로 직접 쓰면, trigger 이후 LAI 감소 지연이 남습니다. 이는 parameter 추정의 대상부터 다른 것입니다.
4. **적용 범위를 제한하십시오.** 동일한 \(|latitude|\) 식을 남반구·고산·water-limited grassland까지 보편적으로 적용할 근거는 아직 부족합니다. 특히 summer drought에 따른 LAI 감소를 autumn senescence로 맞추면 안 됩니다.

현재 노트의 **“늦게 감소를 시작하고 너무 빨리 진다”**는 결과가 slope 0.05보다 더 중요한 연구 발견입니다. EOS50 하나를 맞추더라도 EOS10이 크게 빨라지고 decline duration이 잘못되면, 개선은 부분적입니다. 모델과 관측을 같은 시간 간격으로 맞춘 뒤 onset·EOS50·late-season LAI·decline duration을 함께 평가해야 합니다. 격자 내 종과 지형의 이질성이 관측 감소를 완만하게 만들 수 있다는 불확실성도 남습니다.

Delpierre et al.의 photoperiod-triggered, temperature-dependent senescence progression은 이런 문제를 다룰 구조적 대안입니다. 그러나 프랑스 deciduous trees의 **leaf colouring**을 대상으로 한 formulation이므로, 계수를 boreal c3grass의 LAI 감소에 그대로 이식할 수 없습니다. [Delpierre et al. (2009)](https://www.sciencedirect.com/science/article/abs/pii/S0168192308003353)

노트의 “관측 EOS temperature sensitivity가 거의 0이므로 temperature-independent decline이 맞다”는 해석도 아직 이릅니다. **비유의 회귀계수는 효과가 없다는 증거가 아닙니다.** 월자료 날짜 오차, 짧은 연도별 변동폭, temperature window 선택, 수분 및 이전 계절의 영향이 섞일 수 있습니다. Climatological timing에서 원간격과 월자료의 차이가 작았다는 검증도, interannual sensitivity가 정확하다는 보장은 아닙니다.

따라서 이번에는 단순 photoperiod rule을 기준 후보로 유지하되, 점진적 senescence는 **계절곡선 오차가 최종 채택을 막을 때 확장할 다음 구조 개선**으로 두는 편이 효율적입니다.

**4. Seed와 1년 설계의 한계: 언제 다년 실행으로 넘어가야 하는가?**

**2010에 대한 추가 tuning은 다음 세 실험 정도에서 마치고, 후보가 정해지면 다년 paired run으로 넘어가십시오.** 2010 성능이 더 좋아질 때까지 계속 parameter를 바꾸면 과적합 위험만 커집니다.

그 전에 해결해야 할 구체적인 문제가 있습니다.

[Spring patch](/Volumes/data01/MOF_LSM_project/lm4/patches/lm4P.phenology_spring_tau.diff)의 `tc_pheno_on`은 restart에 저장되지 않고, 실행 시작 때 `tc_pheno`에서 다시 초기화됩니다. **Winter hold 자체가 stateless라는 사실과 전체 scheme의 restart 연속성은 별개입니다.** 연별 chain이면 매년 상태가 바뀌며, 1월이 생장기인 남반구에는 특히 중요합니다. 새 상태를 restart에 보존하고 continuous run과 segmented run을 비교해야 합니다.

권장 최종 설계는 다음입니다.

- **HistCO2 CTRL과 최종 EXP를 동일한 historical restart에서 분기.**
- README의 계획대로 **1996–2000 adjustment, 2001–2015 evaluation**을 기본으로 하되, 5년이면 평형이라는 가정은 하지 않음.
- 두 branch는 동일 forcing·CO₂·executable·land-use 설정을 사용하고 phenology 설정만 달리함.
- Daily LAI와 실제 gate 상태, GDD, 온도 상태, species LAI를 저장하고 GPP·respiration·ET·albedo도 평가.
- 느린 carbon pool은 공통 drift와 EXP−CTRL 차이를 함께 보고, 장기 carbon equilibrium 개선을 주장하지 않음.

292 ppm에서 발견한 timing bias가 HistCO2에서도 유지된다는 기존 결과는 유용합니다. 하지만 이것이 **수정안의 GPP·LAI amplitude 효과도 CO₂에 무관하다**는 뜻은 아닙니다. 최종 functional validation은 historical CO₂에서 해야 합니다.

Rain/snow partitioning은 phenology와 별도 factor로 유지하십시오. `phasewfde5`의 2010 봄은 기존 snowpack을 상속하므로 효과가 작아도 forcing 영향이 작다고 결론 내릴 수 없습니다. 영향이 중요하거나 판단이 모호하면 기록에 제안된 2009–2010 paired extension이 적절합니다. 최종 forcing을 바꾸기로 하면 CTRL·EXP 양쪽을 같은 forcing으로 맞춰야 합니다.

계산량은 현재 속도 기준 20년 한 branch가 약 **220–260시간**, 두 branch는 **440–520시간**입니다. 기존 HistCO2 CTRL을 재사용할 수 있는지는 설정·진단 출력의 일치 여부에 달려 있습니다. 짧은 후보 탐색을 끝내고 이 검증에 계산 시간을 쓰는 편이 논문 가치가 큽니다.

**5. Boreal peak LAI 과대는 범위에 넣을 것인가?**

**수정은 범위 밖, 원인 분류와 성능 해석은 범위 안에 두십시오.**

Allocation·LMA·PPA까지 동시에 조정하면 phenology 효과의 식별이 어려워집니다. 그러나 peak bias를 단순히 “별도 문제”라고 치우면, 봄을 앞당겨 이미 높은 LAI와 GPP를 더 증가시키는 부작용을 설명할 수 없습니다.

최소한 다음을 구분해야 합니다.

- Peak amplitude는 비교적 맞고 timing이 틀린 셀.
- Peak가 이미 과대인 셀.
- 관측과 모델 vegetation composition이 다른 셀.

특히 **larix 부재와 picea 대체는 일반적인 allocation 오차보다 근본적인 representation 문제**입니다. 실제 deciduous needleleaf forest를 모델 evergreen과 understory grass로 표현한 곳에서, grass phenology를 바꿔 총 LAI를 맞추면 생리 과정이 개선됐다고 보기 어렵습니다.

따라서 전체 영역 결과와 함께 vegetation-type agreement가 높은 subset의 결과를 제시하고, mismatch 영역의 면적과 성능도 공개하십시오. 실패 지역을 사후에 제외해서 평균을 개선하면 안 됩니다.

또한 노트에 따르면 일부 cohort는 LAImax에 제한됩니다. 이런 경우 LMA를 바꿔도 기대한 LAI 반응이 나오지 않을 수 있으므로, **LMA sensitivity보다 leaf biomass가 target/cap에 얼마나 붙어 있는지 진단하는 것이 먼저**입니다. 현재 자료만으로 NWN/NEN/WSB 과대의 주원인을 allocation이나 PPA로 확정할 수는 없습니다.

**6. 논문의 storyline과 다음 세 실험은?**

추천 storyline은 다음입니다.

> **LM4p의 계절별 환경 반응 규칙이 LAI timing bias를 어떻게 만드는지 분리하고, 최소한의 규칙 수정이 어느 식생·지역에서 효과적인지와 그 기능적 한계를 검증한다.**

핵심 전개는 네 단계면 충분합니다.

1. 다년·다제품에서 persistent bias를 보이되, amplitude·timing·vegetation mismatch를 분리한다.
2. 실제 gate 진단으로 spring thermal-memory delay와 autumn temperature-only rule의 한계를 보여준다.
3. Autumn-only, spring-only, combined intervention으로 효과와 상호작용을 검증한다.
4. 독립 연도에서 LAI 계절곡선과 GPP를 평가하고, temperate·tundra·composition-mismatch 영역의 실패도 설명한다.

**“일장을 넣었더니 EOS가 맞았다”만으로는 기여가 약합니다.** 계절별 규칙의 비대칭성, 잘못된 vegetation representation에 따른 보상 오차, LAI phenology와 functional phenology의 차이가 더 강한 논문 기여입니다.

현재 진행·대기 중인 `dayllat`, `phasewfde5` 이후 새로 할 세 실험은 다음을 권합니다.

| 순서 | 실험 | 목적·판정 |
|---|---|---|
| **1** | **Spring-only global τ5**, autumn=CTRL, hold 없음. 현재 DLS5와 동일한 cold-off 처리 사용 | 기존 DL·DLS5와 비교해 spring package의 독립 효과와 autumn interaction을 확인. 이를 “τ만의 효과”라고 부르지 않음 |
| **2** | **Spring-only boreal c3grass τ5**, acer·temperate·기타 종은 CTRL, autumn=CTRL | 전역 수정의 온대 악화를 피하면서 boreal 이득을 유지하는지 검증. 실제 cohort별 기여분을 함께 확인 |
| **3** | **선택된 autumn rule + 실험 2의 spring rule + winter hold 후보** | 최종 package 평가. Boreal timing뿐 아니라 온대 early leaf-out, 겨울 LAI, seasonal GPP·LAI 악화 여부로 채택 판단 |

실험 1이 이미 동일 설정으로 완료되어 있다면 재실행하지 말고 결과를 활용하십시오. 실험 2에서는 현재 module-level `tau_pheno_on`을 종·적용영역별로 선택하도록 바꾸되, **cold-off 변경도 같은 적용 대상에만 제한**해야 합니다.

Winter hold를 실험 3에 포함하면 추가 factor가 되므로, 기존 DLS5–DLH5 비교를 보조 근거로 쓰고 새 autumn rule에서도 interaction이 같다고 가정하지 마십시오. 최종 논문에서 hold의 독립 효과까지 핵심 주장으로 삼으려면 별도 ablation이 필요합니다.

세 실험의 공통 판정 기준은 실행 전에 고정하는 것이 좋습니다.

- Boreal SOS 개선이 **May–Jun LAI·GPP의 실질적 악화 없이** 나타나는가?
- ENA/EAS에서 새로운 조기 개엽을 만들지 않는가?
- EOS50뿐 아니라 late-season LAI와 decline duration도 개선되는가?
- 결과가 특정 satellite product 하나에만 의존하지 않는가?
- 개선이 실제 leaf-state 변화인지, 연중 min/max 변화에 따른 threshold 이동인지 구분되는가?

**실험 2가 실패하면 봄 수정을 억지로 최종안에 넣지 않는 것이 좋습니다.** 검증된 autumn correction과 spring 구조의 한계를 명확히 보여주는 논문도 충분히 성립합니다. 반대로 성공하면 restart 문제를 해결한 뒤 곧바로 HistCO2 다년 paired validation으로 넘어가는 것이 다음 우선순위입니다.