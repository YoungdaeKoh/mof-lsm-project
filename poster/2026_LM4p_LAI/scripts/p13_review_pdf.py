#!/usr/bin/env python3
"""Internal review PDF for the supervisor: LM4+ autumn phenology diagnosis and all 2010 pilot runs (Korean text).

Written as HTML (Apple SD Gothic Neo) and printed to PDF with headless Chrome.
Pages: 1 summary (setup, experiments, key numbers, caveats) | Fig. A diagnosis 1982-2010 | Fig. B normalised 2010 cycles + B' GIMMS/CTRL/DL13/12 only,
all runs | Fig. C absolute 2010 LAI | Fig. D EOS maps, all runs.
Numbers are copied from ../data/phentest_regions_summary{,_dl}.txt, lai_regional_sos_eos.txt and p12 output (2026-10-08).
output: ../LM4plus_phenology_pilot_review_2026-10-08.pdf (+ the .html next to it)
"""
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = os.path.abspath(os.path.join(HERE, ".."))
HTML = os.path.join(BASE, "LM4plus_phenology_pilot_review_2026-10-08.html")
PDF = HTML[:-5] + ".pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def tbl(rows, cls=""):
    h = "".join("<th>%s</th>" % c for c in rows[0])
    b = "".join("<tr>%s</tr>" % "".join("<td>%s</td>" % c for c in r) for r in rows[1:])
    return '<table class="%s"><thead><tr>%s</tr></thead><tbody>%s</tbody></table>' % (cls, h, b)


exp = tbl([["실험", "변경 내용", "비고"],
           ["CTRL", "현재 설정 (낙엽 문턱 5 °C: 낙엽송·C3 풀)", "기준"],
           ["TC10", "낙엽 문턱 5 → 10 °C (낙엽송·C3 풀)", "설정만 변경. 봄 잎 나기 문턱도 함께 바뀜"],
           ["DL14+TC10", "낮 &lt; 14 h 이고 평활기온 &lt; 10 °C 이면 낙엽 (낙엽송·C3 풀)", "코드 패치 (낮 길이 조건 추가)"],
           ["DL13/12", "낮 &lt; 13 h (낙엽송·C3 풀) / &lt; 12 h (활엽수), 기온 상한 20 °C", "패치, 활엽수 포함"],
           ["DLtype", "낙엽송 13.5 / C3 풀 12.5 / 활엽수 11.5 h, 기온 상한 20 °C", "관측 EOS 시점의 유형별 낮 길이에서 정함"]])
gap = tbl([["9–10월 과잉 LAI 해소율", "NWN", "ESB", "RFE", "ENA", "WCE", "EAS"],
           ["TC10", "45 %", "21 %", "54 %", "9 %", "5 %", "21 %"],
           ["DL14+TC10", "38 %", "20 %", "50 %", "0 %", "6 %", "2 %"],
           ["<b>DL13/12</b>", "<b>49 %</b>", "<b>32 %</b>", "<b>84 %</b>", "<b>60 %</b>", "<b>116 %</b>*", "<b>40 %</b>"],
           ["DLtype", "40 %", "22 %", "63 %", "46 %", "86 %", "32 %"]], "num")
eos = tbl([["EOS 편차 (모델 − GIMMS, 일)", "CTRL", "TC10", "DL14+TC10", "DL13/12", "DLtype"],
           ["50–70°N (4,716 격자)", "+33", "+9", "+16", "<b>+10</b>", "+15"],
           ["40–50°N (1,606)", "+42", "+38", "+34", "<b>+8</b>", "+12"],
           ["20–40°N (1,317)", "+27", "+26", "+21", "<b>0</b>", "+1"]], "num")

FIGS = [("Fig. A. 1982–2010 기후값 LAI 계절 곡선 (GIMMS vs LM4+ CTRL), 6개 AR6 지역. 점선 = SOS/EOS(진폭 50 %). "
         "모든 지역에서 잎 지는 시기가 28–70일 늦음.", "fig2_regional_seasonal_cycle.png"),
        ("Fig. B. 2010 pilot 실험, 정규화 LAI ((LAI−최소)/(최대−최소)) — 시기만 비교. 회색 = GIMMS(목표). "
         "DL13/12(초록)이 한대·온대 모두에서 가을 하강을 관측 쪽으로 가장 많이 당김. 봄 곡선은 낮 길이 실험 모두 CTRL과 겹침.",
         "fig3b_phentest_regions_normalised_dl.png"),
        ("Fig. B′. Fig. B에서 GIMMS·CTRL·최선 실험(DL13/12)만. 한대(RAR·ESB·NWN)는 한 달가량 당겨졌으나 관측보다 2–3주 늦음이 남고, "
         "온대(ENA·EAS)는 관측에 거의 도달, NEU는 과보정. 한대 봄은 CTRL과 겹침. ENA·EAS 1–3월이 높아진 것은 겨울 최저값 변화에 따른 "
         "정규화 효과로 추정(확인 필요).", "fig3b_phentest_regions_normalised_dl_best.png"),
        ("Fig. C. 같은 실험의 절대 LAI (m² m⁻²). 크기 편차(전구 MJJAS +41 %)는 phenology 수정으로 바뀌지 않음 — 시기만 바뀜.",
         "fig3_phentest_regions_dl.png"),
        ("Fig. D. 2010 EOS: (a) GIMMS, (b)–(f) 각 실험 − GIMMS (일, 빨강 = 늦음). DL13/12(e)에서 북미·동아시아 온대의 붉은 영역이 "
         "대부분 사라지고, 서유럽·북유럽은 파랑(과보정).", "fig6_eos_maps_all_runs_2010.png")]
figs = "".join('<section class="fig"><img src="figures/%s"><p>%s</p></section>' % (png, cap) for cap, png in FIGS)

html = """<!doctype html><html lang="ko"><head><meta charset="utf-8"><title>LM4+ phenology pilot review</title>
<style>
@page { size: A4; margin: 14mm 14mm; }
@page fig { size: A4 landscape; margin: 12mm; }
body { font-family: "Apple SD Gothic Neo", "AppleSDGothicNeo", sans-serif; font-size: 9.6pt; line-height: 1.45; color: #111; }
h1 { font-size: 15pt; margin: 0 0 2pt; } .meta { color: #555; font-size: 8.8pt; margin-bottom: 8pt; }
h2 { font-size: 10.5pt; margin: 9pt 0 3pt; color: #14532d; }
ul { margin: 2pt 0 2pt 14pt; padding: 0; } li { margin: 1.5pt 0; }
table { border-collapse: collapse; width: 100%; margin: 3pt 0 6pt; font-size: 8.8pt; }
th { background: #e3efe3; text-align: left; } th, td { border-bottom: 0.5pt solid #bbb; padding: 2.5pt 4pt; vertical-align: top; }
table.num td:not(:first-child), table.num th:not(:first-child) { text-align: right; }
.note { font-size: 8.5pt; color: #444; } .next { margin-top: 8pt; padding: 5pt 7pt; background: #f2f7f2; border-left: 3pt solid #14532d; }
section.fig { page: fig; break-before: page; } section.fig img { width: 100%; max-height: 165mm; object-fit: contain; }
section.fig p { font-size: 10pt; margin-top: 6pt; }
</style></head><body>
<h1>LM4+ 가을 phenology 진단과 낮 길이 pilot 실험 (2010년 1년 케이스)</h1>
<div class="meta">고영대 · 2026-10-08 · 내부 검토용 · KIMST 과제, KIOST-ESM2 지면모델 LM4+ 오프라인 (WFDE5 강제)</div>
<h2>1. 진단 (1982–2010, GIMMS LAI4g 비교)</h2>
<ul>
<li>생장기(MJJAS) LAI 전구 <b>+41 %</b> 과대. 한대(50–70°N)는 여름 정점 +15 %뿐인데 연평균 +56 % → 편차의 <b>87 %가 비생장기(9–4월)</b>: 크기보다 <b>시기</b> 문제.</li>
<li>잎 지는 날(EOS)이 6개 AR6 지역 모두 <b>28–70일 늦음</b> (NWN +33, ESB +38, RFE +28, ENA +42, WCE +49, EAS +70일). 1982–2010 29년 모두 같은 방향.</li>
<li>원인: 낙엽 조건이 “20일 지수평활 캐노피 기온 &lt; 5 °C(풀·낙엽송) / 10 °C(활엽수)” 하나뿐. ESB 손 계산: 관측 EOS 9/3 → 일평균 5 °C 도달 +20일 → 평활 지연 +17일 → 모델 10/11 (모델 실제 10/11).</li>
<li>관측 EOS 시점의 기온은 지역마다 다르지만(14–16 °C인 곳도 있음) <b>낮 길이는 11.4–13.3 h</b>에 모임 → 낮 길이 신호가 빠져 있음.</li>
</ul>
<h2>2. Pilot 실험 (2010-01-01 CTRL 상태에서 1년, 같은 강제·같은 조건)</h2>
""" + exp + """
<h2>3. 결과 요약</h2>
""" + gap + eos + """
<ul>
<li><b>DL13/12가 가장 큼</b>: 온대(ENA·WCE·EAS)가 처음으로 크게 개선. 봄(5–6월) LAI는 낮 길이 실험 모두 CTRL과 동일, 가을 재개엽 0일(일별 LAI 확인).</li>
<li>TC10은 가을도 당기지만 봄 잎 나기까지 늦춤 (RFE 5–6월 LAI 1.01 → 0.70). 기온 문턱만으로는 안 됨.</li>
<li>주의 ① *WCE 116 %, NEU 113 %는 과보정 — 활엽수 12 h가 관측 11.4 h보다 길기 때문(실험 전 손 계산 예측과 같은 방향). ② 20–40°N SOS가 −7 → −28일: 아열대 겨울 낙엽으로 연 최저값이 바뀐 계산상 효과로 추정, 확인 필요. ③ 2010년 1년 결과뿐, 다년 검증 전.</li>
<li>별도 이슈: 모델 종 분포에서 <b>낙엽송이 북반구에 없음</b>(KIOST piControl 400년 경쟁 결과, 남반구 63격자만 남음). CLM5 PFT 지도로 재파종한 초기장 완성(우점 나무 종 95.8 % 일치), 1개월 시험 통과, 1년 실행 중.</li>
<li>실행 속도: 결합 ESM용 대기화학 건식침적 계산을 끄고 진단을 줄여 48랭크 <b>−23 %</b> (지면 결과 비트 동일). 생산 10.6 → 약 8.1 h/yr.</li>
</ul>
<div class="next"><b>다음 단계 (확인 부탁드립니다)</b>: DL13/12 기반으로 활엽수 문턱 보정 → 2008–2010 다년 실행 → 재파종 상태와 결합 → 다중 관측(MODIS, PhenoCam/FLUXNET)·플럭스 영향 평가 → 겨울 GMD 투고 목표. 포스터(ACM 2026)는 진단 + DL14+TC10까지만 공개.</div>
""" + figs + "</body></html>"
open(HTML, "w").write(html)
subprocess.run([CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", "--print-to-pdf=" + PDF, "file://" + HTML],
               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
print("saved", PDF)
