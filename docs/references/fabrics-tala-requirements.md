# trama 요구사항 명세

Oct 31, 2026 · @Dex Kim

## 개요와 목표

**trama**는 Fabrics 프로젝트 그룹의 디자인 도구다(서브도메인 `trama.fabrics.*`).

자유 캔버스에서 디자인한 화면을 규칙에 따라 결정적으로 HTML/CSS로 변환하고, 사람과 AI가 같은 문서를 실시간으로 함께 편집하는 웹 기반 UI 디자인 도구를 만든다.

**핵심 기능**

- Frame과 Section 단위로 화면을 나눠 디자인한다.
- 디자인 결과를 범용 웹 기준의 HTML/CSS로 내보낸다.
- 디자인 토큰을 도구 안에서 관리하고, DTCG 형식으로 가져오기/내보내기 한다.
- AI가 API(MCP)로 화면을 읽고 원격으로 수정한다.

**설계 원칙**

1. **결정적 변환**: 같은 문서는 항상 같은 HTML을 만든다. 추론에 의존하는 변환은 하지 않는다.
2. **하나의 렌더 경로**: 편집기 화면, 내보낸 HTML, 서버의 헤드리스 렌더가 같은 변환기와 같은 브라우저 엔진(Chromium)을 쓴다.
3. **단일 소스 반응형**: 하나의 Frame은 하나의 HTML을 만든다. BP별 차이는 CSS로만 표현한다.
4. **서버가 최종 검증**: 사람과 AI의 모든 변경은 같은 연산 형식으로 서버에 들어오고, 서버가 규칙을 검사한 뒤 적용한다.

## 확정 결정 요약

| # | 주제 | 결정 |
| --- | --- | --- |
| Q1 | 문서 모델 | 자유 캔버스. 규칙 기반 워크플로우로 CSS 박스 모델과 마크업으로 변환 |
| Q2 | 레이아웃 정보 | 명시형. flow 컨테이너 안의 자식은 좌표 없이 순서만 가짐 |
| Q3 | 반응형 구조 | 단일 Frame + BP override. Frame별 BP 기본 3개, 추가/삭제 가능 |
| 추가 | 최소 폭 | Frame 속성 `minWidth`(기본 320). `body`의 min-width로 출력 |
| 추가 | 오버플로 표시 | fold 라인, minWidth 점선, 문제 노드 빨간 아웃라인 상시 표시 |
| Q4 | BP override 범위 | 스타일, 레이아웃, `<picture>` 이미지 소스만. 텍스트·구조 변경은 모든 BP에 적용 |
| Q5 | 적응형 | 기능으로 만들지 않음. Frame끼리 연결하지 않음 |
| Q6 | 토큰 원본 | 도구 내부가 SSOT. JSON 가져오기/내보내기. 외부 저장소 연동은 범위 밖 |
| Q7 | BP별 토큰 값 | 토큰은 BP를 모름. BP override에서 바인딩 토큰을 교체 |
| Q8 | 모드 출력 | modifier마다 `data-*` 속성. 모드는 `prefers-color-scheme`과도 연동 |
| 추가 | 토큰 계층 | 평면 구조. 순환 참조 차단. 토큰 하나는 한 가지 기준에 따라서만 값이 달라짐 |
| Q9 | AI 아키텍처 | 서버 주도 + 서버 측 헤드리스 렌더러 |
| Q10 | AI 변경 반영 | 바로 반영. 사람 협업자와 동일 |
| Q11 | AI API 형태 | 선언형 일괄 연산 `apply_ops` + 소수의 읽기 도구 |
| Q12 | AI 읽기 형식 | 주석 HTML 기본, 단계적으로 깊이 읽기 |
| Q13 | 컴포넌트 | 원본 + 인스턴스 + 기본 변형(노드별 CSS 속성만) |
| Q14 | Frame 렌더링 | Frame마다 iframe(`srcdoc`). 보드와 오버레이는 DOM |
| Q15 | 기술 스택 | 편집기 TypeScript·React, 자체 WebSocket + 속성 단위 LWW, PostgreSQL. 서버는 TypeScript가 아닌 언어(Python)로 하고 계약은 JSON Schema·적합성 fixture로 공유한다 (2026-10-31 수정) |
| 추가 | 편집기 대상 브라우저 | 최신 Chrome(Chromium)만 |
| Q16 | 출력 HTML 대상 | 범용 웹 기준(Baseline Widely available) |

## 작업 영역과 Frame

작업 영역은 보드, Frame, 오버레이의 3개 층으로 구성하고, Frame 내용은 iframe 안에서 브라우저가 그대로 렌더링한다. 내보내는 HTML에는 `<canvas>` 요소가 들어가지 않는다.

&#91;embedded content: 작업 영역 구조 · 3개 층\]

아래 층부터 보드가 전체를 움직이고, Frame 층이 실제 화면을 그리며, 오버레이가 편집 표시와 입력을 담당한다.

**동작 규칙**

- 줌과 뷰포트는 분리된다. 축소해도 iframe 안의 폭은 그대로라 미디어쿼리는 Frame 크기를 바꿀 때만 전환된다.
- 디자인 모드에서 iframe은 `pointer-events: none`이고, 오버레이가 입력을 받아 board 변환의 역변환으로 iframe 좌표를 계산한다.
- 선택 테두리는 대상 요소의 `getBoundingClientRect()`에 board 변환을 곱한 위치에 그린다.
- iframe은 `srcdoc` + `sandbox="allow-same-origin"`으로 만들어 부모가 DOM에 바로 접근하고, 스크립트는 실행하지 않는다.
- 화면 밖 Frame이나 크게 축소한 Frame은 정적 스냅샷으로 바꾸고, 보이는 Frame만 실제 iframe으로 띄운다(가상화).

**참고 제품**: [Paper](https://paper.design/compare/figma)(HTML/CSS DOM 캔버스), [Onlook](https://docs.onlook.com/migrations/electron-to-web-migration)(무한 캔버스 위 iframe), [Instatic](https://instagit.com/CoreBunch/Instatic/instatic-canvas-editor-multi-breakpoint-frames.md)(breakpoint별 iframe을 무한 캔버스에 배치). Figma는 iframe이 아니라 WebGL 캔버스를 쓴다.

## 레이아웃 모델과 HTML 변환 규칙

레이아웃은 디자이너가 명시하고, 변환기는 명시된 값만 사용한다. 좌표에서 레이아웃을 추론하지 않는다.

**노드와 HTML 대응**

| 노드 | HTML | 비고 |
| --- | --- | --- |
| Frame | `<body>` | viewport, safe area, minWidth, BP 목록을 가짐. 기본 레이아웃은 flex column |
| Section | `<section>` | 시맨틱 태그(`header`, `footer`, `nav` 등)로 바꿀 수 있음 |
| 컨테이너 | `<div>` 또는 지정 태그 | 레이아웃 모드: flex row, flex column, grid, absolute |
| 텍스트 | `<p>`, `<h1>`\~`<h6>`, `<span>` 등 |  |
| 이미지 | `<img>` 또는 `<picture>` | BP별 소스가 있으면 `<picture>` |

**레이아웃 규칙**

1. 컨테이너는 레이아웃 모드를 반드시 가진다. 기본값은 flex column이다.
2. flex/grid 컨테이너의 자식은 좌표를 갖지 않고 순서(index)만 가진다. 문서 트리 순서가 곧 DOM 순서다.
3. 자식은 sizing(fill, hug, fixed)을 가진다. 필요하면 min/max 크기를 지정한다.
4. grid는 기본이 auto-placement(순서대로 셀 채움)이다. 셀 위치와 span 지정은 선택 속성이다.
5. 자유 좌표는 보드 위 Frame 배치와 `position: absolute`인 노드에서만 쓴다. 노드를 absolute로 바꾸면 그 순간의 렌더 위치(x, y, w, h)를 부모 좌상단 기준으로 저장하며, 제약(우측·중앙 고정 등)은 두지 않는다 (2026-10-31 수정).

**드래그앤드롭**

- flow 컨테이너에 놓으면 드롭 위치가 삽입 인덱스로 바뀐다. 위치와 크기는 컨테이너 규칙과 자식 sizing이 결정한다.
- absolute 노드를 끌면 좌표(x, y)가 바뀐다.

**변환 보장**

- 같은 문서는 항상 같은 HTML/CSS를 만든다.
- 출력 CSS는 범용 웹 기준(Baseline Widely available) 허용 목록 안의 속성과 값만 쓴다.

## 반응형: BP, minWidth, override

하나의 Frame은 하나의 HTML을 만들고, BP별 차이는 mobile-first `@media (min-width)` 덮어쓰기로만 표현한다.

**Frame 속성**

- BP 목록: Frame마다 가진다. 기본 3개(예: 360, 768, 1280)이고 추가/삭제할 수 있다.
- Frame 크기: 미리보기용 뷰포트일 뿐이다. HTML로 내보낼 때는 BP 목록만 의미를 가진다.
- `minWidth`: 지원하는 최소 뷰포트. 기본 320(WCAG 1.4.10 Reflow 기준)이며, `body { min-width }`로 출력한다.

**BP override 허용 범위**

| 구분 | 내용 |
| --- | --- |
| 허용 | 레이아웃(direction, gap, sizing, grid 열 수), 스타일 속성, 숨김(`display: none`), 바인딩 토큰 교체 |
| 허용(예외) | 이미지 소스 교체 → `<picture>`의 `<source media>`로 출력 |
| 불허 | 텍스트 내용, 자식 추가·삭제, 순서 변경 |

- base가 아닌 BP에서 텍스트나 구조를 편집하면, 그 변경은 모든 BP에 적용된다. 편집기는 "이 변경은 모든 BP에 적용됩니다"를 안내한다.
- BP마다 완전히 다른 화면이 필요하면 사용자가 별도 Frame을 만든다. 도구는 Frame끼리 연결하지 않는다.
- BP별로 다른 타이포 크기 등은 토큰 쪽이 아니라 BP override에서 바인딩 토큰을 바꿔 처리한다(예: base `font.heading.sm`, 768 이상 `font.heading.lg`).

## 오버플로 표시

별도의 검사 모드 없이, 넘침의 종류마다 다른 표시를 상시로 보여준다. 정상적인 넘침은 경고하지 않는다.

| 종류 | 성격 | 표시 |
| --- | --- | --- |
| 세로 넘침 | 스크롤 영역. 정상 | 뷰포트 높이에 fold 라인, 그 아래는 살짝 어둡게 |
| 뷰포트 < minWidth | 의도된 가로 스크롤 | Frame 밖으로 minWidth 폭까지 회색 점선 영역 |
| minWidth 이상인데 가로 넘침 | 버그 | 원인 노드에 빨간 아웃라인. 자식 최소 폭 > 부모 폭이면 편집 시점에 정적으로 계산 |
| clip 컨테이너가 자식을 자름 | 디자이너가 clip을 켠 경우만 발생 | 레이어 패널 배지 |
| 현재 BP에서 숨김 | override 결과 | 레이어 패널에 숨김 아이콘과 BP 표시 |

같은 검사 결과를 AI의 `inspect` 도구에도 그대로 제공해, AI가 수정 후 스스로 검증할 수 있게 한다.

## 디자인 토큰

토큰의 원본(SSOT)은 도구 안에 있고, 평면 구조로 관리하며, DTCG 2025.10 JSON으로 가져오기/내보내기 한다.

**토큰이 저장하는 정보**

| 필드 | 설명 |
| --- | --- |
| `id` | 불변 내부 ID. 바인딩과 참조는 ID로 저장해 이름을 바꿔도 깨지지 않음 |
| `name` | 점 경로(`color.action.primary`), 전역 유일. CSS 변수명과 DTCG 그룹 경로가 여기서 파생 |
| `type` | DTCG 타입(color, dimension, fontFamily, fontWeight, number, duration, shadow, typography 등). 참조 시 타입 일치 필요 |
| `value` | 기본값. 원시값 또는 다른 토큰 참조 |
| `variesBy` | 값이 달라지는 기준: 없음 / 컬러 테마 / 모드 중 하나 |
| `modes` | 그 기준의 컨텍스트별 값. 비어 있으면 기본값을 상속 |
| `description` | 설명. AI가 토큰을 고르는 근거 |
| `deprecated` | 선택. 바인딩 시 경고 |

저장하지 않고 계산하는 정보: 원시값/참조 판정, 조합별 최종 해석값, 역참조 목록, 사용 횟수, 순환 오류 여부.

**규칙**

1. 선언 시점에 Primitive/Semantic을 구분하지 않는다. 값이 원시값이면 Raw, 참조면 Alias로 자동 판정해 필터와 아이콘에만 쓴다.
2. 순환 참조는 빨간 텍스트로 표시하고 저장을 막는다. 모든 기준×컨텍스트 조합에서 검사한다.
3. 토큰 하나는 한 가지 기준에 따라서만 값이 달라진다. 컬러 테마와 모드 둘 다에 반응해야 하면, 팔레트 토큰(테마에 따라 달라짐)과 시맨틱 토큰(모드에 따라 달라짐)으로 나눠 참조로 연결한다.
4. 노드에 원시값 토큰을 직접 바인딩하면 린트 경고를 띄운다.

**전역 기준(modifier) 정의**

- 기본 제공: `mode: [light, dark]`, 기본값 light.
- 사용자 추가: 예) `palette: [corporate, monochrome]`. 조합 수는 기준별 컨텍스트 수의 곱이다.
- 편집기 상단에 기준마다 전환 토글을 둔다(미리보기용).

**편집 UI**

- 표 편집기: 행은 토큰, 열은 그 토큰 기준의 컨텍스트.
- 조합 미리보기 표: 시맨틱 토큰을 선택하면 테마×모드의 최종 값을 보여주고, 칸을 누르면 원본 토큰으로 이동.
- 램프 생성기(기준색 하나로 단계 생성, OKLCH 기반), 컨텍스트 복제.

**내보내기**

- 토큰: DTCG `tokens.json` + `resolver.json`. 내부 `id`는 `$extensions`에 넣어 다시 가져올 때 같은 토큰으로 인식.
- CSS: 기준마다 `[data-<기준>="<값>"]` 블록. 모드는 `prefers-color-scheme`과도 연동하고, `data-mode`가 있으면 그것이 우선.
- 참조는 해석값으로 펼치지 않고 `var()` 참조로 유지해, 조합을 브라우저가 해석하게 한다.

## 컴포넌트와 변형

컴포넌트는 원본과 인스턴스로 구성하고, 변형은 하나의 트리 위에서 노드별 CSS 속성만 바꾸는 기본 수준으로 시작한다.

**원본과 인스턴스**

| 구분 | 내용 |
| --- | --- |
| 인스턴스에서 바꿀 수 있는 것 | 텍스트, 이미지 소스, 토큰 바인딩, 자식 표시/숨김 |
| 바꿀 수 없는 것 | 구조(자식 추가, 삭제, 순서). 필요하면 연결 해제(detach) 후 일반 노드로 전환 |
| BP override | 레이아웃 BP override는 원본에서만 정의 |

**변형(Variant)**

- 컴포넌트는 속성(enum, boolean)을 정의한다. 예: `size: sm | md | lg`, `tone: primary | danger`.
- 변형은 "속성 값에 따라 켜지는 override 층"이다. BP override와 같은 엔진을 쓰며, 조건만 뷰포트 폭 대신 속성 값이다.
- 변형이 바꿀 수 있는 것: 컴포넌트 안 각 노드의 CSS 속성. `display: none`(보이기/숨기기) 포함.
- 변형이 바꿀 수 없는 것: 노드 추가, 삭제, 순서 변경.
- 노드 ID가 모든 변형에서 같으므로, 변형을 바꿔도 인스턴스의 텍스트·이미지 override가 유지된다.
- 두 속성이 같은 노드의 같은 CSS 속성을 바꾸면 속성 정의 순서상 뒤의 것이 이긴다(CSS 캐스케이드와 동일).
- 구조가 크게 다른 경우(가로형/세로형 카드 등)는 변형 대신 별도 컴포넌트 두 개로 만들도록 가이드한다.

**상태(State)**

- hover, pressed, focus, disabled는 예약된 상태 속성으로 둔다.
- 캔버스에서는 미리보기 전환용이고, 내보낼 때는 `:hover`, `:active`, `:focus-visible`, `[disabled]` 같은 CSS로만 변환한다.

**HTML 출력**

- 인스턴스는 펼쳐서 일반 마크업으로 내보내고, 컴포넌트 스타일은 공통 클래스(`.c-button`)로 한 번만 출력한다.
- 변형은 `data-*` 속성 선택자로 출력한다. 예: `.c-button[data-tone="danger"] .c-button__icon { … }`.

## AI 원격 API (MCP)

AI는 MCP로 서버에 직접 접속해 편집기가 열려 있지 않아도 화면을 읽고 수정하며, 쓰기는 `apply_ops` 하나로 통일한다.

**도구 목록**

| 도구 | 역할 |
| --- | --- |
| `get_tree(frame, depth)` | 개요 읽기. Section과 주요 컨테이너만 |
| `get_tree(node_id)` | 필요한 부분만 주석 HTML로 펼침 |
| `get_tree(…, format: "json")` | override 목록 등 정밀한 속성이 필요할 때만 |
| `get_tokens` | 토큰 목록, 설명, 조합별 해석값 |
| `get_components` | 컴포넌트, 속성, 변형 목록 |
| `inspect(node_id, bp, screenshot?)` | 해당 BP에서 실제 계산된 박스 크기, 오버플로·잘림 경고. 스크린샷은 요청할 때만 |
| `apply_ops([...])` | 유일한 쓰기 도구. JSON 연산 배열을 서버가 검증한 뒤 트랜잭션으로 적용 |

**주석 HTML 읽기 형식**

```html
<section data-id="n12" data-layout="flex col gap:{space.lg}">
  <h2 data-id="n13" style="color:var(--color-text-primary)">요금제</h2>
</section>
```

AI는 HTML로 읽고, `data-id`로 대상을 지정해 `apply_ops`로 쓴다.

**apply\_ops 원칙**

- 연산은 선언형 JSON이다(노드 생성, 속성 설정, 레이아웃 설정, 토큰 바인딩, 인스턴스 삽입, `set_instance_props`, 이동, 삭제 등). 임의 스크립트 실행은 허용하지 않는다.
- 서버는 적용 전에 스키마, 타입, 순환(트리·토큰), 레이아웃 규칙을 검사하고, 하나라도 실패하면 전체를 거부한다.
- 편집기의 사람 사용자도 같은 연산 형식을 쓴다. API는 하나다.
- AI의 변경은 바로 반영된다(제안 모드 없음).

## 동시 편집과 이력

동기화는 Figma 방식의 서버 순서 기반 속성 단위 Last-Writer-Wins로 하고, AI는 사람과 같은 층의 참여자로 다룬다.

**동기화 규칙**

1. 문서는 `객체 ID → 속성 → 값` 구조다. 같은 객체의 같은 속성을 동시에 바꿀 때만 충돌하고, 서버에 마지막으로 도착한 값이 이긴다.
2. 자식 순서는 fractional index로 저장한다. 동시에 삽입해도 인덱스가 밀리지 않는다.
3. 서버는 순환을 만드는 이동(트리)과 순환 참조(토큰)를 거부한다.
4. 각 사용자(AI 포함)의 Undo는 자기 변경만 되돌린다.

**AI 참여**

- AI는 사람과 같은 presence(커서, 선택 영역)로 표시한다.
- AI가 작업 중인 Section이나 Frame에는 "AI 작업 중" 배지(소프트 점유)를 띄운다. 사람이 그 안을 편집하면 막지 않고 경고만 한다.

**되돌리기 안전장치**

- AI 요청 1회 = 트랜잭션 1개 = Undo 1단계.
- 변경 기록 패널: 작성자(사람, AI 세션)별로 무엇을 바꿨는지 보여주고 항목 단위로 되돌린다.
- 자동 스냅샷: AI 세션이 시작될 때 버전을 자동 저장한다.
- 근거 데이터: 서버의 연산 로그.

## 기술 스택과 대상 브라우저

연산 스키마와 검증 규칙은 편집기(TypeScript)가 정의하고, JSON Schema와 적합성 fixture로 서버와 공유한다. 서버는 TypeScript가 아닌 언어로 구현한다(2026-10-31 수정. 원래는 TypeScript 단일 스택이었다).

&#91;embedded content: 시스템 구성 · 6개 구성 요소 + 공유 패키지\]

사람과 AI의 변경은 모두 서버를 거치고, 검증과 HTML 변환은 공유 패키지 하나가 담당한다.

| 영역 | 선택 | 이유 |
| --- | --- | --- |
| 언어 | 편집기 TypeScript, 서버 Python | 스키마는 JSON Schema·적합성 fixture로 공유하고, 변환기는 서버가 헤드리스 Chromium에서 편집기 번들을 불러 쓴다 |
| 편집기 UI | React | 패널, 레이어 트리, 토큰 표 등 일반 UI가 많고 생태계가 큼 |
| Frame 렌더 | 공유 HTML 변환기 → `srcdoc` | 편집기, 내보내기, 서버 렌더가 같은 함수 호출 |
| 실시간 동기화 | 자체 WebSocket 서버 + 속성 단위 LWW | 서버가 순서를 정하고 검증하여 위반 변경을 거부할 수 있음 |
| 서버 | Python | 동기화, `apply_ops`, MCP를 한 프로세스로 시작, 부하에 따라 분리. Playwright·MCP 공식 SDK가 있다 |
| AI 인터페이스 | MCP Python SDK, Streamable HTTP | 원격 AI 클라이언트의 표준 접속 방식 |
| 헤드리스 렌더 | Playwright + Chromium | 편집기와 같은 엔진이라 `inspect` 결과가 일치 |
| 저장소 | PostgreSQL | 노드 속성 테이블 + 연산 로그(변경 기록, AI 세션 Undo, 스냅샷의 근거) |

**대상 브라우저**

- 편집기: 최신 Chrome(Chromium)만 지원한다. 편집기, 서버 렌더, `inspect`가 모두 같은 엔진이 된다.
- 내보낸 HTML: 범용 웹 기준. 변환기의 출력 CSS 허용 목록은 Baseline "Widely available" 수준으로 제한한다.

**제외한 것**: 동기화 SaaS(Liveblocks 등), Yjs 같은 클라이언트 병합형 CRDT, WebGL 렌더링, 자체 레이아웃 엔진.

## 범위 밖 항목과 다음 단계

**이번 범위에서 제외**

- 적응형 Frame 분리, Frame끼리 같은 화면으로 연결하는 기능
- 외부 저장소(Git)와 토큰 동기화
- 두 기준(테마와 모드)에 동시에 반응하는 단일 토큰, 조합 전용 값
- 컴포넌트 변형의 구조 변경(노드 추가·삭제·순서)
- AI 제안 모드(브랜치 후 승인)
- AI용 임의 스크립트 실행
- Chrome 외 브라우저에서의 편집기 지원
- Canvas/WebGL 렌더링, 자체 레이아웃·텍스트 엔진

**나중에 고려**

- 내보내기 옵션 "최신 Chrome 전용 출력"
- 토큰 조합 전용 값, 전역 size 모드
- 외부 저장소 연동

**다음 단계**

- [ ] 노드 데이터 모델과 `apply_ops` 연산 스키마 정의
- [ ] HTML 변환 규칙 명세(노드 → 태그, 속성 → CSS, 출력 CSS 허용 목록)
- [ ] 작업 영역 프로토타입: 보드 팬/줌, iframe Frame, 오버레이 선택
- [ ] 동기화 서버 프로토타입: 속성 단위 LWW, fractional index, 서버 검증
- [ ] MCP 서버와 `inspect` 헤드리스 렌더 연결
