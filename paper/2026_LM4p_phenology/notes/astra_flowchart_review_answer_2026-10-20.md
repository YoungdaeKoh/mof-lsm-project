**Flow chart의 핵심 순서는 맞지만, “patched code를 완전히 반영한다”고 하기에는 몇 가지 수정이 필요합니다.** 특히 drought 판정, GDD reset의 적용 상태, tau5가 autumn rule에도 미치는 영향, leaf biomass와 LAI의 처리 방식이 중요합니다. 파일은 변경하지 않았습니다.

아래에서 `D`는 `vegn_dynamics.F90`, `V`는 `vegetation.F90`, `M`은 추가 확인한 `vegn_tile.F90`이며, 모두 `lm4/patches/phenoff_work/` 아래 파일입니다. Figure는 제공된 PNG를 직접 확인했습니다.

**1. Flow chart의 정확성과 빠진 경로**

- **Daily 실행 조건과 순서는 맞습니다.** 다만 `update_vegn_slow` 자체를 “once a day”라고 하기보다는, **그 안의 day-boundary block**이라고 쓰는 것이 정확합니다. GDD와 temperature smoother는 날짜가 바뀔 때 갱신됩니다. Growth → starvation → phenology 순서는 `do_cohort_dynamics`, `do_ppa`, `do_phenology`가 해당 경로를 활성화한 경우입니다.  
  근거: [V:2653](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegetation.F90:2653), [V:2768](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegetation.F90:2768).

- **Growth는 phenology 변경 전 status를 사용합니다.** 따라서 OFF→ON이 된 날에는 그 변경으로 인한 leaf growth가 이미 끝난 growth call에 소급 적용되지 않습니다. 반대로 ON→OFF 당일에는 growth 후 leaf shedding이 가능합니다. 또한 “ON이면 leaves grow”는 단순화입니다. Allocation에는 `temp > T_dorm` 조건도 있습니다.  
  근거: [V:2777](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegetation.F90:2777), [D:1585](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:1585).

- **Drought는 단순한 순간 root-zone soil moisture threshold가 아닙니다.** Cohort별 smoothed 변수에 대해 두 가지 대체 경로가 있습니다.
  \[
  D=
  \begin{cases}
  \theta_{\mathrm{av,phen}}<\theta_{\mathrm{crit}},&
  \psi_{\mathrm{crit}}\le0,\\
  \mathrm{psist}_{\mathrm{av,phen}}>\psi_{\mathrm{crit}},&
  \psi_{\mathrm{crit}}>0.
  \end{cases}
  \]
  `theta_crit`는 species parameter와 wilting-point 값으로 계산하고 [0,1]로 제한합니다. Flow chart에는 **“drought stress from smoothed root-zone moisture or soil-ψ stress”** 정도가 적절합니다.  
  근거: [V:2248](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegetation.F90:2248), [D:2124](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2124).

- **Winter hold와 photoperiod leaf-off에는 activation gate가 있습니다.** Winter hold는 `dayl_crit_on > 0` 및 `tc_crit_off > 0`일 때만, photoperiod leaf-off는 `dayl_crit_off > 0` 및 `tc_crit_off > 0`일 때만 활성화됩니다. Latitude 보정의 `|lat|`는 **degrees**입니다. 또한 winter hold에는 `shortening` 조건이 없습니다.  
  근거: [D:2134](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2134), [D:2151](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2151).

- **GDD reset은 ON cohort에서 cold/photoperiod leaf-off 조건이 성립할 때만 일어납니다.** 이미 OFF인 cohort는 이후 추워져도 해당 reset branch를 통과하지 않습니다. Drought로 먼저 OFF가 되면 GDD가 다음 해까지 유지될 수 있다는 corner case가 코드 주석에도 있습니다. Cold/photoperiod와 drought가 동시에 성립하면 **GDD=0이 유지**됩니다. “Drought면 GDD reset 없음”은 **drought-only leaf-off**에 한정해야 합니다. OFF→ON 직후 같은 call에서 ON→OFF 조건을 다시 평가하지도 않습니다.  
  근거: [D:2131](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2131), [D:2154](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2154), [D:2168](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2168).

- **Tau5는 5-day moving average가 아니라 exponential smoother입니다.** `tau_pheno_on=5`이면 daily weight가 0.2입니다. 첫날에는 **갱신 전 `tc_pheno`**로 초기화한 다음 당일 `tc_daily`를 반영합니다. `tc_pheno_on`은 restart에 저장되지 않으므로 restart 후 재초기화되어 uninterrupted run과 달라질 수 있습니다. `tc_on` 선택에는 `tc_pheno_on > 0` 확인도 있습니다.  
  근거: [V:2664](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegetation.F90:2664), [D:2105](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2105), [M:170](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_tile.F90:170). 기존 `tc_pheno`의 restart read/write는 [V:583](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegetation.F90:583), [V:1565](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegetation.F90:1565)에서 확인됩니다.

- **Grass 처리는 “seedling size로 biomass 전체를 즉시 reset”하는 것은 아닙니다.** Height, DBH, crown area를 즉시 seedling geometry로 바꾸고, 줄어든 `bl_max`를 초과하는 leaves를 제거합니다. 기본 7.5% leaf loss도 적용되어 둘 중 큰 값이 사용됩니다. Stem biomass는 별도 감소식으로 처리됩니다. Leaf-on에서는 `bl_max`뿐 아니라 `br_max`도 갱신합니다. OFF 처리 진입은 grass의 경우 leaves가 없어도 `bsw>0`이면 가능합니다.  
  근거: [D:2142](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2142), [D:2177](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2177).

- **Leaf removal과 litter input은 같지 않습니다.** 제거한 leaf C/N 일부를 retranslocation한 뒤 나머지가 litter로 갑니다. `min_lai_pheno` 검사는 이번 shedding 후 재계산한 LAI가 아니라 **그 시점에 저장된 `cc%lai`**를 사용합니다. LAI는 그 뒤 같은 phenology call 안에서 재계산됩니다.  
  근거: [D:2207](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2207), [D:2217](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2217).

- **Relayer와 merge는 daily phenology 내부에서 실제 호출됩니다.** Merge는 `nindivs` 가중평균으로 GDD와 drought 관련 변수를 바꿀 수 있습니다. `merge_cohorts`는 status를 새로 판정하지 않고 recipient status를 유지합니다. 다만 merge eligibility를 결정하는 `cohorts_can_be_merged`의 구현이 이 source set에 없어, **서로 다른 status의 cohort도 merge 가능한지는 확정할 수 없습니다.** 연도 경계에는 별도의 relayer/merge도 있습니다.  
  근거: [D:2252](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2252), [M:526](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_tile.F90:526), [M:591](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_tile.F90:591), [M:628](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_tile.F90:628), [V:2843](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegetation.F90:2843).

마지막 연결은 **“updated leaf biomass/geometry → LAI → subsequent radiation/photosynthesis calculations”**로 쓰는 편이 정확합니다. 코드의 LAI 식은 `leaf_area_from_biomass(...) / [crownarea × (1−internal_gap_frac)]`입니다. 단순 `bl/LMA/crownarea`는 추가 가정이 필요합니다. 이 파일들만으로 정확한 “next 30 min” 호출 순서까지 검증되지는 않습니다. Canopy-air temperature 누적과 extrema 계산은 직접 확인되지만, `tc_daily`의 daily normalization/reset 위치도 이 파일들에서는 확인되지 않습니다.  
근거: [D:2223](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2223), [V:2264](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegetation.F90:2264).

**2. Figure와 code의 차이 5개에 대한 판정**

| 주장 | 판정 및 수정 |
|---|---|
| 1. Daily mean GDD vs Tmin/Tmax GDD | **맞음.** 다만 차이가 freezing-crossing day에만 생기는 것은 아닙니다. 실제 daily mean이 `(Tmin+Tmax)/2`와 다르면 두 extrema가 모두 base보다 높아도 차이가 납니다. Code의 base는 species별 `gdd_base_T`입니다. [V:2659](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegetation.F90:2659) |
| 2. Canopy-air temperature 명시 누락 | **맞음.** `cana_T`가 mean accumulator와 Tmin/Tmax 모두에 들어갑니다. [V:2265](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegetation.F90:2265) |
| 3. Drought leaf-on/off 누락 | **맞음.** Drought-only leaf-off는 GDD를 reset하지 않는다고 명시해야 합니다. [D:2134](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2134), [D:2160](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2160) |
| 4. Constant vs latitude-dependent threshold | **일반 code 대비로는 맞음.** 실제 DL run의 slope가 0이면 constant 표기는 그 run에 정확합니다. “DL run에서 0”이라는 실행 설정 자체는 제시된 routine으로 확인할 수 없습니다. [D:2151](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2151) |
| 5. Tau5 생략은 autumn-centred scope상 의도적 | **조건부로만 타당함.** 해당 실험에서 tau5가 꺼져 있으면 괜찮습니다. 켜져 있다면 spring smoother뿐 아니라 **기존 cold leaf-off에도 shortening gate가 추가**되므로 autumn-centred라는 이유만으로 생략할 수 없습니다. [D:2154](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2154) |

추가로 Figure에서 다음을 고쳐야 합니다.

- Leaf-on의 `T_pheno > T_crit`는 **`T_on ≥ T_crit`**로 수정합니다.
- **“days since the end of the last growing season”은 부정확합니다.** GDD는 ON/OFF와 무관하게 매일 누적되고 특정 ON→OFF branch에서만 reset됩니다. Merge까지 고려하면 단순한 시간 구간의 누적합보다 **state-variable recurrence**가 적절합니다.
- **“winter hold: no re-greening after the solstice”는 코드 조건을 과도하게 해석합니다.** Winter hold에는 solstice/shortening 검사가 없고, short-day와 cool-temperature 조건만 있습니다. “Suppress re-greening under short, cool days”가 정확합니다.
- **“temperature is the only autumn cue”는 drought path를 제외한 cold-deciduous seasonal rule이라는 범위 표시가 필요합니다.**
- Figure의 12 h, 13 h, 20°C, species별 `T_crit`, “tropical species unchanged”는 **실험 parameter 설정에 관한 주장**입니다. Routine은 species parameter를 읽으므로 해당 값과 적용 species는 run configuration과 별도로 대조해야 합니다.

근거: [D:2134](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2134), [D:2154](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2154), [V:2654](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegetation.F90:2654).

**3. Paper figure의 최소 faithful rule box**

권장 범위는 **“Daily phenological status transitions for non-evergreen cohorts”**입니다. Parameter가 활성화된 해당 실험을 설명한다면 activation gate 자체는 SI로 옮기고, 본문 box에는 다음을 남기면 됩니다.

먼저 \(T_d,T_{\min,d},T_{\max,d}\)를 **daily canopy-air temperatures**로 정의합니다.

\[
G^*=G_{d-1}
+\frac{[T_{\min,d}-T_b]_+ + [T_{\max,d}-T_b]_+}{2},
\qquad [x]_+=\max(x,0)
\]

\[
T_{20,d}=0.95T_{20,d-1}+0.05T_d
\]

\[
\mathrm{OFF}\rightarrow\mathrm{ON}
\iff
G^*>G_{\rm crit}
\land T_{\rm on}\ge T_{\rm crit}
\land\neg D
\land\neg W
\]

\[
W=(L<L_{\rm on})\land(T_{20}<T_{\rm off})
\quad\text{[winter hold enabled]}
\]

\[
C=(T_{20}<T_{\rm crit})\land A
\]

\[
P=S\land(L<L_{\rm off})\land(T_{20}<T_{\rm off})
\quad\text{[photoperiod rule enabled]}
\]

\[
\mathrm{ON}\rightarrow\mathrm{OFF}
\iff C\lor P\lor D
\]

\[
G_d=
\begin{cases}
0,& \text{entering status is ON and }(C\lor P),\\
G^*,& \text{otherwise}.
\end{cases}
\]

여기서 \(D\)는 drought stress, \(S\)는 shortening days입니다. **Tau5가 꺼진 실험이면** \(T_{\rm on}=T_{20}\), \(A=\mathrm{true}\)로 두고 별도의 tau5 식은 생략할 수 있습니다. **Tau5가 켜진 실험이면** \(T_{\rm on}=T_5\), \(A=S\)와 \(T_{5,d}=0.8T_{5,d-1}+0.2T_d\)를 보여야 합니다. 위 식은 status branch와 GDD reset을 그대로 반영합니다.  
근거: [V:2659](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegetation.F90:2659), [D:2131](/Volumes/data01/MOF_LSM_project/lm4/patches/phenoff_work/vegn_dynamics.F90:2131).

Box 아래에는 두 문장이면 충분합니다.

> Evergreen cohorts remain ON. OFF initiates leaf shedding; it does not imply instantaneous loss of all leaves.  
> Phenological status is updated after daily growth.

**SI로 옮겨도 되는 내용**은 drought의 상세 계산, activation gate, day-length 계산식, slope=0인 실험의 일반 latitude-extension 식, grass geometry/biomass 처리, retranslocation, minimum-LAI cutoff, merge, restart 초기화입니다. 다만 **실제로 사용한 tau5 여부와 species별 threshold 값은 caption 또는 parameter table에 명시**해야 합니다. Autumn만 보여주는 더 작은 box를 원한다면 제목을 “Autumn cold/photoperiod leaf-off rules”로 좁히고, drought 및 leaf-on은 별도 Methods/SI에 설명한다는 범위를 명확히 표시하는 것이 적절합니다.