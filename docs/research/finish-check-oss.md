# 웹페이지 마감 검사(draw-scroll)를 보강할 오픈소스 조사 (2026-10-19)

이 문서는 kakao-agent 봇의 마감 검사 `projects/kakao-agent/config/draw-scroll.sh` 에 무엇을 더하거나 갈아 끼울지 고르기 위한 자료다. 각 항목은 GitHub API, 저장소 소스 파일, 공식 문서, 스펙, 논문 원문으로 확인했고, 원문을 열지 못한 것은 "미확인"으로 적었다. 일부는 이 Mac 에서 직접 돌려 봤다(아래 "직접 돌려 본 것").

## 결론

- 판정 7종(겹침, 가림, 잘림, 흐림, 대비, 작음, 넘침)을 통째로 대신할 오픈소스는 없다. 접근성 엔진은 대비 하나만 겹치고, 겹침, 잘림, 흐림을 재는 도구는 찾지 못했다. 시각 회귀 도구(BackstopJS, reg-suit, Playwright `toHaveScreenshot`)는 기준 이미지가 있어야 하는데 봇이 만든 페이지는 매번 처음이다.
- 대비는 axe-core 4.14 가 가장 쓸 만하지만 draw-scroll 의 픽셀 판정을 대신하지 못한다. 배경 그림, 그라데이션, 겹친 요소는 "incomplete" 로 넘긴다(소스 확인, 시험 페이지에서 확인). 배경이 단색인 글자의 대비와 `opacity` 를 섞은 대비는 정확하게 내므로, draw-scroll 의 4px 둘레 중앙값을 교차 확인하는 두 번째 의견으로 붙인다. MPL-2.0 이라 그대로 주입하는 데 문제가 없다.
- IBM Equal Access 는 들이지 않는다. 대비 규칙이 한글만 있는 글자를 통째로 건너뛴다(소스의 정규식, 시험 페이지에서 확인). 한자, 영문이 섞이면 잰다.
- 가장 싼 보강은 도구가 아니라 draw-scroll 안의 빈틈 셋이다. 시험 페이지에서 확인했다. (1) 첫 화면 위 1/3 에만 있는 결함은 "2멈춤 이상" 규칙에 걸려 버려진다. (2) `overflow: hidden` 이 글자를 가진 요소 자신에 걸리면 잘림을 못 본다. (3) 휴대폰 흉내 없이 `set viewport` 만 쓴다. 휴대폰 흉내(`set device`)에서는 가로로 넘친 페이지가 넓은 레이아웃 뷰포트로 축소되어 보인다.
- 대비 기준을 APCA 로 바꾸지 않는다. WCAG 3 초안(2026-09-10)은 대비 측정법을 "yet to be determined" 로 둔다. apca-w3 는 OSI 라이선스가 아니다(W3 한정 라이선스, 그 밖은 AGPL v3). 보조 지표가 필요하면 MIT 인 color.js 의 APCA 구현을 쓴다.
- 에이전트용 도구 중 측정형은 impeccable `detect`(Apache-2.0, 61개 규칙)와 chrome-devtools-mcp `lighthouse_audit`(속은 axe) 둘이다. impeccable 은 URL 모드에서 배경 그림 위 대비를 픽셀로 쟀다(1.2:1). 다만 정지 캡처 한 장이라 스크롤 멈춤마다 재지 않는다.

## 조사 방법과 읽는 법

- 별 수, 라이선스, 최근 push 는 `gh api repos/OWNER/REPO` 의 `stargazers_count`, `license.spdx_id`, `pushed_at` 이다(2026-10-19 조회). "최근 push" 는 마지막 커밋과 거의 같지만 정확히 같지는 않다. `null`/`NOASSERTION` 은 GitHub 이 라이선스를 판별하지 못한 것이다.
- "판정" 칸은 draw-scroll 의 7종 중 무엇을 대신하는지(대신), 같은 것을 다른 방법으로 재서 교차 확인하는지(교차), 지금 없는 판정을 새로 더하는지(새로)를 적는다.
- "헤드리스 CLI" 는 GUI 없이 셸에서 돌고 결과를 파일이나 표준 출력으로 내는지다.
- 직접 돌린 환경: 이 Mac, agent-browser 0.33.2, 별도 세션(`--session finishcheck-oss`), Pillow 12.3.0, axe-core 4.14.0, accessibility-checker-engine 4.0.34, apca-w3 0.1.9, colorjs.io(npm 최신), impeccable 4.6.0. 패키지는 scratchpad 의 빈 폴더에 `npm i --ignore-scripts` 로 받았다.

## draw-scroll 이 지금 하는 일 (요약)

`projects/kakao-agent/config/draw-scroll.sh`(kakao-agent repo) 를 끝까지 읽었다(231행, 고치지 않음).

- `agent-browser open` → `set viewport 390 844` → `load` 와 `document.fonts.ready` → 2.5초 대기 → 멈춤마다 `screenshot` 과 페이지 안 JS 탐침(`eval`) → `scroll down <높이/3>` → 0.7초 대기. 60멈춤에서 멈춘다.
- 탐침은 텍스트 노드마다 `Range.getClientRects()` 로 줄 상자를 얻고, 조상 `opacity` 곱과 `filter: blur`, 고정/스티키 막대(화면 40% 미만 높이), 배경 없는 막대, `overflow`/`clip-path` 조상, 기울임, 상자마다 세 점의 `elementFromPoint` 를 본다.
- Python(Pillow)이 대비(상자 둘레 4px 의 휘도 중앙값, 24px 부터 3:1)와 잘림(가림막 가장자리 2px 띠에 글자 색 픽셀 3개 이상)을 픽셀로 잰다. `mix-blend-mode` 글자는 대비를 건너뛰고, 그림자나 외곽선이 있으면 대비만 건너뛴다.
- 같은 (판정, 글) 이 2멈춤 이상 나와야 남긴다. 겹침은 막대 단위로 센다. 배경 사정은 `projects/kakao-agent/knowledge/runbooks/kakao-ai-chat.md` "마감 검사 (2026-10-15)" 절에 있다.

## 직접 돌려 본 것

시험 페이지(390x844)에 결함을 일부러 넣었다: 배경 없는 고정 메뉴, `line-height: .62` 와 `overflow: hidden` 으로 j 꼬리를 자르는 제목, `#999` 회색 글자, 그라데이션 위 흐린 글자, 줄무늬 PNG 위 흰 글자, `opacity: .5` 글, `filter: blur(2px)` 글, 절대 위치 판 밑에 깔린 글, 10px 글자, 폭 520px 상자, `mix-blend-mode: difference` 글, `text-overflow: ellipsis` 글. 본문은 모두 한글이다.

| 결함 | draw-scroll | axe-core 4.14 `color-contrast` | IBM ace 4.0.34 | impeccable 4.6.0 `detect` (URL) |
|---|---|---|---|---|
| 회색 `#999` | 대비 2.8:1 | 위반 2.84 | 위반 2.85 | low-contrast 2.8:1 |
| 그라데이션 위 흐린 글 | 대비 2.4:1 | incomplete `bgGradient` | 결과 없음(한글만이라 건너뜀) | low-contrast 2.4:1 |
| PNG 위 흰 글 | 대비 1.2:1 | incomplete `bgImage` | 결과 없음(한글만) | low-contrast 1.2:1 (canvas-background-image) |
| `opacity .5` | 흐림 | 위반 3.54(투명도를 섞은 대비) | 결과 없음(한글만) | low-contrast 3.5:1 |
| `blur(2px)` | 흐림 | 없음 | 결과 없음 | 없음 |
| 판 밑에 깔린 글 | 가림(전부) | incomplete `bgOverlap` | 결과 없음 | 없음 |
| 고정 투명 메뉴 밑 글 | 겹침 | 없음 | 없음 | 없음 |
| j 꼬리 자르는 가림막(가림막이 부모) | 잘림 90px | 없음 | 없음 | 없음 |
| 같은 가림막이 글자 요소 자신 | **못 잡음** | 없음 | 없음 | 없음 |
| 같은 가림막이 첫 화면 위 1/3 | **못 잡음**(1멈춤에만 보임) | 해당 없음 | 해당 없음 | 해당 없음 |
| 10px | 작음 | 해당 규칙 없음 | 통과(18.88:1, 크기 규칙 없음) | undersized-ui-text |
| 가로 넘침 162px | 넘침 | 없음 | 없음 | 없음 |
| blend 글자 | 대비 건너뜀(의도) | incomplete `equalRatio` | 결과 없음(한글만) | 없음 |
| ellipsis | 없음 | 없음 | 없음 | 없음 |

- axe 는 멈춤 4곳(scrollY 0, 281, 562, 843)에서 결과가 똑같았다. axe 는 `elementFromPoint` 대신 페이지 전체를 자기 격자로 만들어 쓴다([create-grid.js](https://github.com/dequelabs/axe-core/blob/develop/lib/commons/dom/create-grid.js), [get-rect-stack.js](https://github.com/dequelabs/axe-core/blob/develop/lib/commons/dom/get-rect-stack.js)). 그래서 "멈춤마다 axe" 는 같은 결과를 되풀이할 뿐이고, 스크롤로 상태가 바뀐 뒤에만 의미가 있다.
- axe 실행 중 scroll 이벤트는 0회였고 scrollY 도 그대로였다(`color-contrast` 만 8ms, 전체 규칙 12ms, 작은 시험 페이지). Lighthouse 소스에는 "axe just scrolled the page" 라는 주석이 남아 있다([accessibility.js](https://github.com/GoogleChrome/lighthouse/blob/main/core/gather/gatherers/accessibility.js)). 4.14 의 이 시험에서는 재현되지 않았다. 무거운 페이지의 실행 시간은 미확인이다.
- `measureText` 시험: 같은 제목에서 `actualBoundingBoxDescent` 와 기준선(높이 0 인 inline-block 을 끼워 잰 위치)으로 잉크 아래 끝을 계산하자, 가림막 아래 경계를 6.9px 넘었다. 픽셀로도 잉크가 가림막 끝 행까지 차 있었다. 가림막이 글자 요소 자신이어도 이 방법은 잡는다.
- 휴대폰 흉내: 새 세션에서 `set device "iPhone 14"` 만 주면 가로 넘침이 없는 페이지는 `innerWidth` 390, DPR 3 이었다. 폭 520px 상자가 있는 페이지는 `screen.width` 390 인데 `innerWidth` 552 였다. 휴대폰에서 넘친 페이지는 옆으로 밀리는 대신 전체가 축소되어 글자가 작아진다는 뜻이다. 두 경우 모두 `ontouchstart` 는 없고 `(pointer: coarse)` 도 거짓이었다. `set media light reduced-motion` 은 `prefers-reduced-motion: reduce` 를 참으로 만들었다.

---

## 1. 접근성 엔진

| 이름 / URL | 라이선스 | 별 | 최근 push | 재는 것 | 헤드리스 CLI | 판정 | 함정 |
|---|---|---|---|---|---|---|---|
| [dequelabs/axe-core](https://github.com/dequelabs/axe-core) | MPL-2.0 | 7668 | 2026-10-15 | WCAG 2.x 규칙 155개(`lib/rules`). 대비는 CSS 계산값과 쌓임 맥락으로 배경색을 합성 | 라이브러리. `axe.min.js`(637KB)를 `agent-browser eval -b` 로 주입해 실행했다(직접) | 대비: 교차 | 배경 그림, 그라데이션, 겹침, 가상 요소, 복잡한 그림자, 화면 밖은 incomplete. `filter: blur` 는 보지 않는다. 글자 크기 하한 규칙 없음 |
| [dequelabs/axe-core-npm](https://github.com/dequelabs/axe-core-npm) (`@axe-core/cli`, `@axe-core/playwright` 등) | MPL-2.0 | 727 | 2026-10-15 | 위 엔진을 Puppeteer, Playwright, WebDriver, CLI 로 감싼 것 | CLI 있음(본문 미확인) | 위와 같음 | 스크롤 멈춤 제어는 직접 짜야 한다 |
| [IBMa/equal-access](https://github.com/IBMa/equal-access) (`accessibility-checker-engine`) | Apache-2.0 | 786 | 2026-10-16 | IBM 규칙 집합. 대비는 그라데이션, 배경 그림이면 "potential" | 엔진 `ace.js`(669KB)를 주입해 실행했다(직접). Node CLI `accessibility-checker` 도 있다(본문 미확인) | 대비: 교차(한글 제외) | **한글만 있는 글자는 대비를 재지 않는다.** 소스 [text_contrast_sufficient.ts](https://github.com/IBMa/equal-access/blob/main-4.x/accessibility-checker-engine/src/v4/rules/text_contrast_sufficient.ts) 의 정규식이 영숫자와 한자 범위(`一-鿿`, `㐀-䶿`)만 남기고 지운 뒤 빈 문자열이면 `return null` 한다. 시험: "흐린 한글 글자" 는 결과 없음, "흐린 한글 글자 abc" 와 "淡い漢字" 는 fail. 요소 자신에 `overflow: hidden` 이 있어도 건너뛴다(같은 파일). 랜드마크, 제목 같은 소음이 많다 |
| [pa11y/pa11y](https://github.com/pa11y/pa11y) | LGPL-3.0 | 4578 | 2026-10-19 | 러너 `htmlcs`(기본)와 `axe` 를 Puppeteer 로 돌린다. 10.0.0 은 axe-core `~4.13.0`, puppeteer `^25.9.0` ([package.json](https://github.com/pa11y/pa11y/blob/main/package.json)) | 예(`pa11y <url> --runner axe`) | 대비: 교차 | [README](https://github.com/pa11y/pa11y) 의 actions 는 클릭, 입력, 대기뿐이고 스크롤 동작이 없다. 멈춤마다 재려면 Node API 로 직접 |
| [pa11y/pa11y-ci](https://github.com/pa11y/pa11y-ci) | LGPL-3.0 | 642 | 2026-10-13 | 여러 URL 을 pa11y 로 | 예 | 위와 같음 | 위와 같음 |
| [GoogleChrome/lighthouse](https://github.com/GoogleChrome/lighthouse) | Apache-2.0 | 30906 | 2026-10-18 | 접근성 범주는 axe(13.5.0 은 axe-core 4.13.0)를 `wcag2a`, `wcag2aa` 태그로 돌린다([accessibility.js](https://github.com/GoogleChrome/lighthouse/blob/main/core/gather/gatherers/accessibility.js)) | 예(`lighthouse <url>`). 지금 상태를 재는 snapshot 모드는 Node user flow API(본문 미확인) | 대비: 교차(axe 와 같음) | axe 를 두 겹 감싼 것이라 직접 axe 를 쓰는 것보다 무겁다. 실행 뒤 `scrollTop = 0` 으로 페이지를 맨 위로 올린다(같은 파일) |
| [squizlabs/HTML_CodeSniffer](https://github.com/squizlabs/HTML_CodeSniffer) | BSD-3-Clause | 1145 | 2024-01-07 | WCAG 2 규칙. 대비는 부모를 거슬러 단색 배경을 찾고 배경 그림, 반투명 배경이면 경고로 돌린다([1_4_3_Contrast.js](https://github.com/squizlabs/HTML_CodeSniffer/blob/master/Standards/WCAG2AAA/Sniffs/Principle1/Guideline1_4/1_4_3_Contrast.js)) | pa11y 의 기본 러너로 | 대비: 교차 | 2024-01 이후 push 없음. 쌓임 맥락과 겹침을 axe 만큼 다루지 않는다 |
| [GoogleChrome/accessibility-developer-tools](https://github.com/GoogleChrome/accessibility-developer-tools) | Apache-2.0 | 2309 | 2022-10-04 | 옛 Chrome 접근성 감사 | 아니오 | 없음 | 보관(archived) 저장소. 쓰지 않는다 |

### axe-core `color-contrast` 가 incomplete 로 넘기는 경로 (소스 확인)

`develop` 브랜치, 2026-10-15 커밋 `f01bf5c`, 4.14.0 기준.

- 판정 본체는 [color-contrast-evaluate.js](https://github.com/dequelabs/axe-core/blob/develop/lib/checks/color/color-contrast-evaluate.js) 다. 배경색이나 글자색을 못 정하면(`bgColor === null`, `fgColor === null`) 결과를 `undefined`, 즉 incomplete 로 돌린다(170~181행). 계산값이 정확히 1:1 이면 `equalRatio`, 한 글자짜리 글은 `shortTextContent` 로 넘긴다.
- 배경 그림과 그라데이션: [element-has-image.js](https://github.com/dequelabs/axe-core/blob/develop/lib/commons/color/element-has-image.js) 는 배경 쌓임의 요소가 `IMG`, `CANVAS`, `OBJECT`, `IFRAME`, `VIDEO`, `SVG` 이면 `imgNode`, `background-image` 가 `none` 이 아니면 정규식 `/gradient/` 로 `bgGradient` 와 `bgImage` 를 가른다. [get-background-color.js](https://github.com/dequelabs/axe-core/blob/develop/lib/commons/color/get-background-color.js) 는 쌓임을 위에서 아래로 훑다가 그런 요소를 만나면 바로 `null` 을 돌린다(71~75행). 그림의 실제 픽셀은 보지 않는다.
- 겹친 요소: [get-background-stack.js](https://github.com/dequelabs/axe-core/blob/develop/lib/commons/color/get-background-stack.js) 는 글자 줄 상자마다 쌓임을 구해, 맨 위가 그 요소가 아니면 `bgOverlap`, 줄마다 쌓임이 다르면 `elmPartiallyObscuring` 으로 넘긴다. 배경이 있는 요소가 줄 상자를 다 덮지 못하면 `elmPartiallyObscured` 다(get-background-color.js 91~100행).
- 화면 밖: [filtered-rect-stack.js](https://github.com/dequelabs/axe-core/blob/develop/lib/commons/color/filtered-rect-stack.js) 가 `outsideViewport` 로 넘긴다(48행). 다만 시험에서는 화면 밖의 회색 글자도 매 멈춤 위반으로 나왔다. 격자가 페이지 전체를 담기 때문으로 보인다(정확한 조건은 미확인).
- 투명도: 글자색과 조상 쌓임 맥락의 `opacity` 를 섞는다([get-foreground-color.js](https://github.com/dequelabs/axe-core/blob/develop/lib/commons/color/get-foreground-color.js) 109~121행). 그래서 `opacity: .5` 글은 흐림이 아니라 대비 위반 3.54 로 나온다. `mix-blend-mode` 는 [flatten-colors.js](https://github.com/dequelabs/axe-core/blob/develop/lib/commons/color/flatten-colors.js) 가 합성식으로 계산한다.
- 큰 글자 기준: [color-contrast.json](https://github.com/dequelabs/axe-core/blob/develop/lib/checks/color/color-contrast.json) 의 `largeTextPt: 18`, `boldTextPt: 14`, `boldValue: 700` 이다. draw-scroll 은 굵기와 상관없이 24px 하나로 가른다.
- 정리: axe 가 incomplete 로 넘기는 것이 바로 draw-scroll 이 픽셀로 재는 것(사진, 그라데이션 위 글)이다. axe 는 그 자리를 채우지 못하고, 단색 배경 쪽의 정확도(쌓임 맥락, 투명도, 굵기 기준)를 보탤 수 있다.

---

## 2. 렌더 결과 기반 레이아웃 버그 탐지

| 이름 / URL | 라이선스 | 별 | 최근 push | 재는 것 | 헤드리스 CLI | 판정 | 함정 |
|---|---|---|---|---|---|---|---|
| [galenframework/galen](https://github.com/galenframework/galen) | Apache-2.0(`LICENSE-2.0.txt`, GitHub 판별은 null) | 1417 | 2022-07-15 | Selenium 으로 요소 위치, 크기를 재고 사람이 쓴 spec(`inside screen`, `below header 0px`)과 맞춘다([README](https://github.com/galenframework/galen)) | 예(Java) | 넘침, 가림: 대신(사람이 쓴 spec 이 있을 때만) | 페이지마다 spec 을 써야 한다. 봇이 매번 새로 만드는 페이지에는 맞지 않는다. 2022 이후 push 없음 |
| [redecheck/redecheck](https://github.com/redecheck/redecheck) | MIT | 18 | 2023-03-28 | 폭을 바꿔 가며 DOM 레이아웃 그래프를 만들고 다섯 실패를 찾는다: 요소 충돌(겹침), 요소 돌출(부모 밖으로), 뷰포트 돌출, 아주 좁은 폭에서만 적용되는 레이아웃, 잘못 줄바뀌는 요소. 표본 폭은 60px 간격 균등 표본과 스타일시트 중단점, 차이가 나면 이분 탐색 ([ISSTA 2017 도구 논문](https://eprints.whiterose.ac.uk/116991/)) | Java, Maven 빌드, Selenium. macOS 용 드라이버 자원이 저장소에 들어 있다([README](https://github.com/redecheck/redecheck)) | 넘침: 교차. 요소 충돌: 가림과 비슷 | 연구 도구. 폭을 바꾸는 축만 있고 스크롤 상태와 애니메이션은 모른다. 판단 방법을 빌려 올 가치는 있다(아래 "들일 순서") |
| XFix ([ISSTA 2017 demo](https://conf.researchr.org/details/issta-2017/issta-2017-demos/7/XFix-An-Automated-Tool-for-the-Repair-of-Layout-Cross-Browser-Issues)) | 미확인 | 미확인 | 미확인 | 브라우저 간 레이아웃 차이(XBI)를 탐색 기반으로 자동 수리 | 미확인 | 없음 | 브라우저 간 비교라 기준 브라우저가 둘 필요. 저장소 미확인 |
| VizAssert ([PLDI 2018 논문](https://homes.cs.washington.edu/~mernst/pubs/verify-layout-pldi2018-abstract.html)) | 미확인 | 미확인 | 미확인 | 브라우저 레이아웃을 형식화해, 정해진 범위의 모든 렌더링 매개변수에서 접근성 단언 14개가 성립하는지 증명하거나 반례를 낸다. 전문 디자인 페이지 62개에서 오류 64개, 오탐 13개 | 미확인 | 없음 | 연구 시제품. 실제로 쓸 수 있는 배포물 미확인 |
| Owl Eyes ([ASE 2020, arXiv 2009.01417](https://arxiv.org/abs/2009.01417v2)) | 미확인 | 미확인 | 미확인 | Android 화면 캡처를 딥러닝으로 보고 글자 겹침, 흐린 화면, 빠진 그림 같은 표시 문제를 찾는다 | 미확인 | 겹침, 흐림: 개념상 겹침 | Android 앱 대상. 코드 공개 여부 미확인 |
| "Google 의 visual bug 연구" | 미확인 | | | Google 저자의 웹 시각 버그 탐지 논문을 찾지 못했다. 찾은 것은 VLM 으로 canvas 시각 버그를 보는 연구([arXiv 2501.09236](https://arxiv.org/abs/2501.09236v1))와 브라우저 간 차이를 VLM 으로 보는 XBIDetective([arXiv 2512.15804](https://arxiv.org/abs/2512.15804v1))였다. 두 논문 본문은 열지 않았다 | | | |
| [garris/BackstopJS](https://github.com/garris/BackstopJS) | MIT | 7186 | 2026-10-10 | 기준 캡처와 새 캡처의 픽셀 차이 | 예 | 없음(회귀만) | 기준 이미지가 필요하다. 처음 만든 페이지에는 비교할 것이 없다 |
| [reg-viz/reg-suit](https://github.com/reg-viz/reg-suit) | MIT | 1301 | 2026-10-13 | 캡처 디렉터리 비교와 보고서 | 예 | 없음(회귀만) | 위와 같음. 캡처는 다른 도구가 찍는다 |
| [lost-pixel/lost-pixel](https://github.com/lost-pixel/lost-pixel) | MIT | 1679 | 2026-04-22 | 시각 회귀 | 예 | 없음 | 보관(archived) 저장소 |
| Playwright `toHaveScreenshot` ([문서](https://playwright.dev/docs/api/class-pageassertions)) | Apache-2.0([microsoft/playwright](https://github.com/microsoft/playwright), 별 98038) | | 2026-10-18 | 연속 두 캡처가 같아질 때까지 기다린 뒤 기준과 비교. `animations: "disabled"` 는 CSS 애니메이션, 전환, Web Animations 를 멈추고 유한 애니메이션은 끝으로 감는다 | 예 | 없음(회귀만) | 기준 필요. GSAP 처럼 JS 로 도는 움직임은 `animations: "disabled"` 대상이 아니다(문서가 CSS 와 Web Animations 만 적는다). "두 캡처가 같아질 때까지" 는 정착 판정으로 빌려 올 만하다 |
| [mapbox/pixelmatch](https://github.com/mapbox/pixelmatch) | ISC | 6994 | 2026-10-06 | 두 PNG 의 픽셀 차이 수 | 예(Node) | 없음 | 정착 판정(같은 멈춤 두 캡처 비교)에 쓸 수 있다. Pillow 의 `ImageChops.difference` 로도 된다 |

- 글자 겹침, 잘림, 넘침을 DOM 기하로 찾는 범용 오픈소스는 찾지 못했다. ReDeCheck 의 요소 충돌, 돌출이 가장 가깝지만 글자가 아니라 요소 상자 단위이고 연구 도구다. 웹 검색에서도 Playwright 로 `scrollWidth > clientWidth` 를 찾는 개인 스크립트 정도만 나왔다(1차 출처로 쓰지 않음).

---

## 3. 텍스트 잘림, 넘침 탐지 (줄 상자 대 잉크 범위)

| 방법 / URL | 라이선스 | 무엇을 주는가 | 판정 | 함정 |
|---|---|---|---|---|
| `Range.getClientRects()` | 웹 표준 | 텍스트 노드의 줄 상자. draw-scroll 이 이미 쓴다 | | 줄 상자는 `line-height` 를 따른다. 글리프 잉크가 상자를 넘을 수 있다(그래서 draw-scroll 은 픽셀을 본다) |
| canvas `TextMetrics.actualBoundingBoxAscent/Descent` ([HTML 표준 IDL](https://html.spec.whatwg.org/multipage/canvas.html#dom-textmetrics-actualboundingboxdescent)) | 웹 표준 | 같은 글꼴로 그렸을 때 기준선 위아래 잉크 범위. 기준선 위치는 높이 0 인 `inline-block` 을 끼워 `getBoundingClientRect().top` 으로 잰다 | 잘림: 교차(픽셀 없이 기하로) | 문자열 전체의 최댓값이다(글자별이 아님). canvas 가 고른 대체 글꼴이 DOM 과 다를 수 있다(한글 대체 글꼴, 미확인). 정의 본문은 표준 페이지가 길어 IDL 만 확인했다. 시험 페이지에서는 가림막 아래 6.9px 초과를 정확히 냈다(직접) |
| [seek-oss/capsize](https://github.com/seek-oss/capsize) | MIT | 글꼴 메트릭(캡 높이, 어센더, 디센더)으로 글자 상자를 다듬는 CSS 계산 | 없음(예방) | 측정기가 아니라 레이아웃 도구. 별 1733, 2026-10-15 push |
| `scrollWidth > clientWidth`, `scrollHeight > clientHeight` | 웹 표준 | 요소 안에서 내용이 넘쳐 숨겨졌는지 | 잘림: 새로(줄 단위 잘림, 말줄임) | `text-overflow: ellipsis` 는 의도한 말줄임일 수 있다. 시험 페이지의 말줄임은 네 도구 모두 판정하지 않았다 |

- WCAG 2.2 의 [1.4.12 Text Spacing](https://www.w3.org/TR/WCAG22/) 은 줄 간격 1.5배, 문단 간격 2배, 자간 0.12em, 단어 간격 0.16em 으로 바꿔도 내용이 사라지지 않아야 한다고 한다. 이 스타일을 주입하고 잘림, 넘침을 다시 재는 것은 높이를 고정한 상자를 찾는 싼 압력 시험이다. WebFetch 가 본 것은 1.4.3, 1.4.10 과 큰 글자 정의 앞부분이며, 1.4.12 의 수치는 이 문서를 쓰며 원문에서 다시 확인하지 않았다(미확인).

---

## 4. 대비를 실제 픽셀로 재는 도구

| 이름 / URL | 라이선스 | 별 | 최근 push | 재는 것 | 헤드리스 CLI | 판정 | 함정 |
|---|---|---|---|---|---|---|---|
| [Myndex/apca-w3](https://github.com/Myndex/apca-w3) | **NOASSERTION**. LICENSE.md: W3/AGWG 협력 협정 하의 WCAG 웹 콘텐츠 용도로만, 그 밖은 AGPL v3, 의료, 안전 등 금지 용도 목록, 상표 조건 | 214 | 2026-05-06 | APCA Lc 값과 글꼴 크기별 표(`fontLookupAPCA`) | 라이브러리 | 대비: 교차(지표만 다름) | OSI 라이선스가 아니다. 봇 코드에 그대로 넣기 어렵다. [WCAG 3 초안](https://www.w3.org/TR/wcag-3.0/)(2026-09-10)은 "The contrast algorithm used in WCAG 3 is yet to be determined" 라고 적는다 |
| [color-js/color.js](https://github.com/color-js/color.js) (`colorjs.io`) | MIT | 2313 | 2026-10-19 | `contrast(…, 'WCAG21')`, `'APCA'` 등. APCA 구현은 0.0.98G 상수([src/contrast/APCA.js](https://github.com/color-js/color.js/blob/main/src/contrast/APCA.js)) | 라이브러리 | 대비: 교차 | 색 두 개의 계산기일 뿐 픽셀 표본은 우리가 정한다. 시험에서 apca-w3 와 같은 Lc 를 냈다(`#999`/`#fff` 54.6, 금색 `#c9a24a`/`#111` 은 WCAG 7.87:1 인데 Lc -54.4) |
| impeccable `detect` URL 모드 | Apache-2.0 | (아래 7절) | | 배경 그림 위 글자를 "browser contrast ... via canvas-background-image" 로 잰다(직접, 1.2:1) | 예 | 대비: 교차 | 정지 캡처 한 장, 멈춤마다가 아니다 |
| draw-scroll 의 둘레 4px 중앙값 | (자체) | | | 이미 픽셀 기반 | | | 둘레에 이웃 글자가 들어가면 흔들린다(스크립트 주석). 글자 마스크 없이 글자 안 픽셀은 못 본다 |

- 스크린샷만으로 대비를 재는 독립 오픈소스 CLI 는 찾지 못했다. 픽셀 대비는 draw-scroll 의 방식(DOM 상자 + 캡처 픽셀)이 이미 다른 도구보다 앞서 있다. 보강할 것은 "글자 픽셀 자체" 의 표본이다. 같은 멈춤에서 글자색을 `transparent` 로 바꿔 한 장 더 찍으면 글자 아래 배경을 그대로 얻을 수 있다(아이디어, 시험 안 함).
- 대비 기준의 근거: [WCAG 2.2](https://www.w3.org/TR/WCAG22/) 1.4.3 은 4.5:1, 큰 글자 3:1, 큰 글자는 18pt 또는 14pt 굵게이며 CJK 는 "equivalent size" 라고만 적는다. IBM 엔진은 CJK 를 29.3px 또는 24px 굵게로 본다(ACT 규칙 PR 2121 을 인용, [text_contrast_sufficient.ts](https://github.com/IBMa/equal-access/blob/main-4.x/accessibility-checker-engine/src/v4/rules/text_contrast_sufficient.ts)). draw-scroll 의 24px 는 한글에서 조금 너그러운 쪽이다.

---

## 5. 스크롤 구동 페이지를 멈춤마다 재기

| 대상 / URL | 라이선스 | 근거 | draw-scroll 에 주는 것 | 함정 |
|---|---|---|---|---|
| GSAP ScrollTrigger ([문서](https://gsap.com/docs/v3/Plugins/ScrollTrigger)) | GSAP 표준 라이선스(GitHub 판별 null, [greensock/GSAP](https://github.com/greensock/GSAP) 별 29445) | 숫자 `scrub`(예: `scrub: 1`)은 스크롤이 멈춘 뒤에도 잠시 더 따라간다(`onUpdate` 설명). `onScrubComplete` 콜백이 있다. `ScrollTrigger.getAll()` 이 모든 인스턴스를 돌려준다 | 0.7초 고정 대기 대신 "움직임이 멈췄는지" 를 묻는 정착 판정 | `scrub: 2` 이상이면 0.7초 안에 안 끝날 수 있다(추정, 실측 안 함). `window.ScrollTrigger` 가 전역에 없을 수도 있다 |
| `gsap.matchMedia()` ([문서](https://gsap.com/docs/v3/GSAP/gsap.matchMedia%28%29)) | 위와 같음 | 공식 예시가 `reduceMotion: "(prefers-reduced-motion: reduce)"` 조건으로 `duration: 0` 을 준다 | 줄인 움직임 경로를 한 번 더 찍어 "움직임 없이도 다 보이는가" 를 본다 | 페이지가 matchMedia 를 안 쓰면 reduced-motion 에서도 그대로 움직인다 |
| Lenis ([darkroomengineering/lenis](https://github.com/darkroomengineering/lenis)) | MIT | 별 16687, 2026-10-18 push. `isScrolling` getter, `velocity`. `respectReducedMotion` 기본 true 라 reduce 면 부드러운 스크롤을 끈다([README](https://github.com/darkroomengineering/lenis)) | 정착 판정에 `isScrolling === false` | 인스턴스가 전역 변수가 아니면 못 읽는다 |
| `document.getAnimations()` | 웹 표준 | CSS 애니메이션, 전환, Web Animations 의 `playState` | 정착 판정 | GSAP, Lenis 의 JS 움직임은 잡히지 않는다(이미 runbook 에 실측 기록) |
| Playwright `reducedMotion`, `emulateMedia` ([문서](https://playwright.dev/docs/api/class-testoptions)) | Apache-2.0 | `prefers-reduced-motion: reduce` 흉내, `forcedColors`, `contrast: more` 도 있다 | agent-browser 에도 `set media [dark\|light] [reduced-motion]` 이 있고 동작했다(직접) | |

- 멈춤마다 재는 오픈소스 도구는 찾지 못했다. draw-scroll 의 "휠로 내리고 멈춰서 잰다" 가 이미 레시피다. 남은 개선은 정착 판정(고정 대기 대신)과 줄인 움직임 경로 한 번이다.

---

## 6. 모바일 실측

| 수단 / URL | 근거 | 지금 draw-scroll | 함정 |
|---|---|---|---|
| CDP `Emulation.setDeviceMetricsOverride` ([Emulation.pdl](https://github.com/ChromeDevTools/devtools-protocol/blob/master/pdl/domains/Emulation.pdl)) | `mobile` 매개변수 설명: "This includes viewport meta tag, overlay scrollbars, text autosizing and more." | `set viewport` 만 쓴다. 휴대폰 흉내가 아니다 | agent-browser `set device "iPhone 14"` 는 DPR 3, iPhone UA 를 준다(직접). 넘친 페이지에서 `innerWidth` 가 552 로 넓어졌다(직접). 캡처가 1170x2532 로 커져 Pillow 계산의 `scale` 이 3 이 된다 |
| CDP `Emulation.setTouchEmulationEnabled` (같은 파일) | "Enables touch on platforms which do not support them." | 없음 | agent-browser `set device` 뒤에도 `ontouchstart` 가 없었다(직접). 터치 전용 분기(`pointer: coarse`)는 안 탄다 |
| CDP `Input.synthesizeScrollGesture` ([Input.pdl](https://github.com/ChromeDevTools/devtools-protocol/blob/master/pdl/domains/Input.pdl)) | experimental. `yDistance`, `speed`(기본 800px/s), `gestureSourceType`, `preventFling` | 휠(`scroll down`)로 내린다 | 터치 제스처로 내리면 Lenis 의 `syncTouch` 같은 터치 경로를 탄다. agent-browser 에서 이 명령을 직접 부르는 방법은 미확인(`--cdp` 로 붙는 별도 클라이언트가 필요할 수 있다) |
| agent-browser `-p ios` ([agent-browser](https://github.com/vercel-labs/agent-browser), Apache-2.0, 별 44214) | `agent-browser --help`: "iOS Simulator (requires Xcode and Appium)", `swipe up`, `tap` | 없음 | iOS 시뮬레이터의 실제 WebKit 이다. 카카오톡 iOS 인앱도 WebKit 이라(아래) 가장 가까운 흉내다. Xcode, Appium 설치가 필요하고 이 Mac 에서는 돌려 보지 않았다 |
| 카카오톡 인앱 브라우저 | [3d-agent-skills.md "WebGL 실행 환경"](3d-agent-skills.md) 절: iOS 는 App Store 지침상 WebKit, Android 는 WebView 라는 간접 근거, UA 에 `KAKAOTALK` | | 인앱 툴바 숨김에 따른 뷰포트 높이 변화, 글자 크기 설정(WebView text zoom)이 페이지에 주는 영향은 미확인 |

---

## 7. AI 에이전트용 시각 QA 스킬, MCP

| 이름 / URL | 라이선스 | 별 | 최근 push | 재는 것 | 헤드리스 CLI | 판정 | 함정 |
|---|---|---|---|---|---|---|---|
| [ChromeDevTools/chrome-devtools-mcp](https://github.com/ChromeDevTools/chrome-devtools-mcp) `lighthouse_audit` | Apache-2.0 | 53816 | 2026-10-19 | 접근성, SEO, 모범 사례, "agentic browsing" 점수와 걸린 DOM 노드. 성능은 빠진다. `mode: "snapshot"` 은 지금 상태를, `navigation` 은 새로 고쳐 잰다. `device: mobile` 흉내([tool-reference.md](https://github.com/ChromeDevTools/chrome-devtools-mcp/blob/main/docs/tool-reference.md)) | MCP 서버(`--headless`, `--slim`) | 대비: 교차(속은 axe) | 사용 통계 수집이 기본으로 켜져 있다. `--no-usage-statistics` 로 끈다([README](https://github.com/ChromeDevTools/chrome-devtools-mcp)). MCP 라 세 두뇌에 따로 등록해야 한다 |
| [pbakaus/impeccable](https://github.com/pbakaus/impeccable) `detect` | Apache-2.0 | 82803 | 2026-10-19 | 결정적 규칙 61개(README). 파일 모드는 정적, URL 모드는 설치된 Chrome 으로 렌더해 잰다. 시험 페이지에서 대비 넷, 10px 글자를 잡았다(직접, 위 표) | 예. `npx impeccable detect --json <file\|url>`. npm 의 플랫폼별 바이너리(`@impeccable/cli-darwin-arm64`) | 대비: 교차. 작음: 교차(11px 하한) | 겹침, 가림, 잘림, 흐림, 넘침은 시험에서 안 나왔다. 규칙 대부분은 디자인 취향(글꼴, 장식) 판정이라 마감 검사에 그대로 넣으면 소음이다. `npx impeccable` 은 바이너리를 `~/.impeccable/bin/` 으로 받을 수 있다(README) |
| impeccable `finish-reviewer` ([.claude/agents/impeccable-finish-reviewer.md](https://github.com/pbakaus/impeccable/blob/main/.claude/agents/impeccable-finish-reviewer.md)) | Apache-2.0 | | | 측정형이 아니다. "You have no browser" 로 시작해, 부모가 찍은 `desktop.png`, `mobile.png` 와 시안, 계약서를 읽고 판정 단어(recapture, rebuild, fix, ship)를 낸다. 기계 판정은 부모의 훅 몫이라고 적는다 | 아니오(서브에이전트) | 없음 | 증거(캡처)가 없거나 깨졌으면 리뷰 대신 재캡처를 요구하는 0번 검사는 빌려 올 만하다. draw-scroll 의 `.finish-*.json` 강제와 같은 생각이다 |
| [ibelick/ui-skills](https://github.com/ibelick/ui-skills) | MIT | 9858 | 2026-10-17 | `skills/*/SKILL.md` 지침과 레지스트리 CLI | | 없음 | 측정 코드가 없다. 이미 봇이 디자인 기준으로 쓴다 |
| AThevon/genjutsu (`shoot.mjs`, `design-audit/audit.py`) | NOASSERTION | 571 | 2026-10-05 | 위임 메시지에서 이미 본 것. CDP 정지 캡처와 overflow, 콘솔 에러, 소스 정적 grep. "검사 못 함" 과 "통과" 구분 | | 넘침: 교차 | 라이선스 불명 |

---

## draw-scroll 에 들일 순서

싼 것부터다. "어디에" 는 draw-scroll.sh 안의 위치다. 지금 이 문서는 조사만 했고 스크립트는 고치지 않았다.

1. **첫 멈춤과 마지막 멈춤을 시간차로 두 번 본다.** 지금은 첫 화면 위 1/3 에만 있는 결함이 한 멈춤에만 보여서 "2멈춤 이상" 규칙에 버려진다(시험에서 j 잘림이 사라짐). 멈춤 0 을 찍은 뒤 1.5초 더 기다려 같은 위치를 한 번 더 찍고 탐침을 돌린다. 마지막 멈춤도 같다. 시간차 두 번은 "한 멈춤에만 나오는 로더, 도는 등장" 을 거르는 원래 의도와 맞는다. 붙일 곳: 루프 앞과 루프가 `y == last` 로 끝난 직후. 기대 효과: 히어로 제목의 잘림, 가림, 흐림을 놓치지 않는다. 위험: 2.5초 뒤에도 도는 히어로 반복 애니메이션은 두 번 다 잡혀 오탐이 된다. 같은 멈춤 두 장의 픽셀이 다르면 그 결함은 버리는 조건을 함께 둔다.
2. **잘림 탐침이 글자 요소 자신도 본다.** `clipOf` 가 `el.parentElement` 부터 올라가서, `h1 { overflow: hidden; line-height: .9 }` 처럼 가림막이 글자 요소 자신이면 못 잡는다(시험에서 확인). `clipOf` 를 `el` 부터 시작하게 하고(인라인 요소는 `overflow` 가 적용되지 않으니 `display` 가 inline 이면 건너뛴다), 픽셀 판정 앞에 `measureText` 의 잉크 범위와 기준선으로 "가림막 경계를 몇 px 넘는가" 를 같이 낸다. 붙일 곳: 탐침 `clipOf` 와 `edges` 계산. 기대 효과: SplitText 없이 손으로 짠 가림막의 잘림. 위험: canvas 와 DOM 의 대체 글꼴이 다르면 잉크 범위가 틀린다. 그래서 기하 신호는 픽셀 신호와 둘 다일 때만 잘림으로 친다.
3. **정착 판정으로 0.7초 고정 대기를 바꾼다.** 멈춘 뒤 150ms 간격으로 (a) `document.getAnimations()` 중 running 이 없고 (b) 화면 안 텍스트 상자 좌표 해시가 두 번 연속 같으면 찍는다. 최대 3초. GSAP 문서대로 숫자 `scrub` 은 스크롤이 멈춘 뒤에도 움직인다. 붙일 곳: `scroll down` 뒤 `wait 700`. 기대 효과: 반쯤 나타난 채 찍혀 생기는 흐림 오탐, 느린 scrub 의 놓침이 준다. 위험: 끝없이 도는 마키나 배경 영상은 영영 정착하지 않으니 상한을 둔다. 텍스트 좌표만 보면 색만 바뀌는 전환은 놓친다.
4. **멈춤마다 axe `color-contrast` 를 한 번 주입한다(교차 확인용).** `axe.min.js`(4.14.0, 637KB)를 첫 멈춤에 `eval -b` 로 넣고, 멈춤마다 `axe.run(document, {runOnly: ['color-contrast']})` 를 돌린다. 결과 중 `violations` 와, incomplete 의 `messageKey` 를 탐침 결과 옆에 둔다. draw-scroll 대비와 axe 가 둘 다 위반이면 확정, draw-scroll 만이면 지금처럼, axe 만이면(단색 배경, 굵기 기준 차이) 새로 올린다. 기대 효과: 둘레 표본이 이웃 글자에 흔들리는 오탐을 줄이고, 14pt 굵게 기준을 맞춘다. 위험: axe 는 페이지 전체를 보므로 화면 밖 글도 매 멈춤 나온다(시험). 화면 안 노드만 남기는 걸러내기가 필요하다. `opacity` 를 섞어 흐림을 대비 위반으로 낸다(시험 3.54). 흐림 판정과 같은 글이면 하나로 합친다. 실행 시간은 작은 페이지 8ms 였고 큰 페이지는 미확인이다. MPL-2.0 은 파일 단위 약한 카피레프트라 고치지 않고 주입만 하면 부담이 없다.
5. **휴대폰 흉내로 한 번 더 돈다.** 지금의 `set viewport 390 844` 대신(또는 추가로) `set device "iPhone 14"` 로 돈다. 넘친 페이지가 옆으로 밀리지 않고 축소되는 것을 잡으려면 `innerWidth > screen.width` 를 "넘침(휴대폰에서 축소됨)" 으로 남긴다(시험에서 552 > 390). Pillow 쪽은 이미 `shot.width / W` 로 배율을 구하므로 DPR 3 캡처도 맞는다(코드상, 시험은 device 모드로 draw-scroll 전체를 돌리지 않음). 기대 효과: 카톡 인앱에서 실제로 보이는 글자 크기와 넘침. 위험: 캡처가 9배 커져 시트, MP4 가 무거워진다. 터치는 여전히 흉내 내지 않는다.
6. **줄인 움직임 경로를 한 번 돈다.** `set media light reduced-motion` 뒤 같은 스크롤을 한 번 더 돌려, 움직임 없이도 모든 글이 보이는지(흐림, 가림이 0인지) 본다. 기대 효과: reduced-motion 사용자에게 영영 안 나타나는 글. 위험: 페이지가 reduced-motion 을 처리하지 않으면 같은 결과가 두 번 나올 뿐이다. 실행 시간이 두 배다. 주인이 원할 때만 켜는 선택지로 둔다.
7. **글자 간격 압력 시험(선택).** WCAG 1.4.12 의 간격 스타일을 주입하고 첫 화면만 다시 재서 잘림, 넘침이 새로 생기는지 본다. 기대 효과: 높이를 고정한 카드, 버튼. 위험: 장식용 큰 제목은 원래 줄 간격이 좁게 디자인돼 오탐이 많다. 본문 크기(24px 미만)에만 적용한다.

### 들이지 말 것

- **IBM Equal Access**: 한글만 있는 글의 대비를 재지 않는다(소스, 시험). 봇 페이지는 대부분 한글이다. 랜드마크, 제목 규칙의 소음도 많다.
- **Lighthouse CLI, chrome-devtools-mcp `lighthouse_audit`**: 접근성 부분은 axe 다. axe 를 직접 주입하는 것보다 무겁고, Lighthouse 는 실행 뒤 페이지를 맨 위로 올린다(멈춤 상태가 깨진다). MCP 는 세 두뇌 등록과 기본 사용 통계 수집이 따라온다.
- **pa11y**: axe 와 HTML_CodeSniffer 를 감싼 것이고 스크롤 동작이 없다. LGPL-3.0 이다.
- **BackstopJS, reg-suit, Lost Pixel, Playwright `toHaveScreenshot`**: 기준 이미지가 필요한 회귀 도구다. 처음 만든 페이지에는 쓸 데가 없다. Lost Pixel 은 보관 저장소다. "연속 두 캡처가 같을 때까지" 라는 생각만 3번 정착 판정에 빌린다.
- **Galen**: 페이지마다 사람이 레이아웃 spec 을 써야 한다. 2022 이후 push 가 없다.
- **ReDeCheck, VizAssert, Owl Eyes, XFix**: 연구 도구이거나 배포물이 불분명하다. ReDeCheck 의 "폭을 이분 탐색해 레이아웃이 바뀌는 지점을 찾는다" 는 나중에 폭을 여럿 재게 될 때 참고만 한다.
- **APCA 를 대비 기준으로**: WCAG 3 초안이 측정법을 정하지 않았고, apca-w3 는 OSI 라이선스가 아니다. 보조 지표로 보고 싶으면 color.js(MIT)의 `contrast(…, 'APCA')` 를 쓰되 판정에는 넣지 않는다.
- **impeccable `detect` 를 마감 검사에**: 대비와 작은 글자는 겹치고, 나머지 규칙은 디자인 취향이라 "마감 결함" 과 섞이면 두뇌가 무엇을 고칠지 흐려진다. 디자인 리뷰 단계에서 따로 쓰는 것은 다른 문제다.

## 남은 확인

- axe `color-contrast` 를 실제 봇 시안(pros-night-lux 같은 GSAP 페이지)에서 멈춤마다 돌렸을 때의 실행 시간과, draw-scroll 대비와 엇갈리는 건수.
- `set device` 로 draw-scroll 전체를 돌렸을 때 Pillow 배율, 잘림 띠(2px 가 DPR 3 에서 6px 가 되는지) 동작.
- `Input.synthesizeScrollGesture` 를 agent-browser 세션에 보내는 방법(`--cdp` 연결).
- 카카오톡 인앱(Android WebView, iOS WebKit)의 글자 크기 설정과 툴바 높이 변화가 판정에 주는 영향. 실기기가 필요하다.
- WCAG 2.2 1.4.12 의 수치를 원문에서 다시 확인.
