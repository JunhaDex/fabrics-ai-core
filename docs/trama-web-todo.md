# trama-web todo

저장소: https://github.com/JunhaDex/fabrics-trama-web · 로컬: `projects/trama-web/`
Slack: `C0CDK58U22F`
목적: 자유 캔버스에서 디자인한 화면을 규칙에 따라 결정적으로 HTML/CSS로 변환하고, 사람과 AI가 같은 문서를 실시간으로 함께 편집하는 웹 기반 UI 디자인 도구
요구사항 명세: `docs/references/fabrics-tala-requirements.md`

## 결정 사항

### 정체성과 요구사항의 정본
- 이름은 trama다. 서브도메인 `trama.fabrics.*`
- 설계 원칙 4개(결정적 변환, 하나의 렌더 경로, 단일 소스 반응형, 서버가 최종 검증)와 확정 결정(Q1~Q16)은
  요구사항 명세가 정본이다. 이 파일에는 옮기지 않고, 명세를 구현 수준으로 구체화한 결정만 적는다
- 편집기 자체의 UI는 common-design(`@junhadex/core`, 테마 `@junhadex/theme-neutral`)으로 만든다. 없는 범용 컴포넌트는 로컬에서 먼저
  만들고 검증되면 common-design으로 승격한다. Frame iframe 안의 내용은 변환기 출력만 쓰며 common-design과 무관하다
- 앱이므로 CHANGELOG 생성기는 git-cliff다 (저장소마다 따로 둔다)
- 명세 Q15 중 서버 항목(TypeScript 단일 공유, Node.js, MCP TypeScript SDK)은 철회한다. 서버는 TypeScript가 아닌
  언어로 만든다. 편집기 쪽(TypeScript, React)과 나머지 항목(자체 WebSocket + 속성 단위 LWW, PostgreSQL,
  Playwright + Chromium 헤드리스 렌더)은 유지한다

### 단계 구분
- 1단계(web): 편집기만 만든다. 서버, 동시 편집, MCP, 헤드리스 렌더, PostgreSQL, 인프라는 만들지 않는다
- 2단계(server, infra): 동기화 서버, `apply_ops`·MCP 엔드포인트, Playwright 헤드리스 렌더, PostgreSQL,
  terraform. 1단계가 끝나면 착수한다

### 저장소 구조
- 구성 요소마다 저장소를 나눈다. 서버의 언어가 달라 한 저장소에 담으면 복잡도만 높아지고 코드 공유의 이점이 없기 때문이다
  - web: `fabrics-trama-web`, `projects/trama-web/` (1단계)
  - server, infra: 2단계에 만든다
- 저장소 사이의 계약(문서 모델, 연산 스키마, 오류 코드, 출력 CSS 허용 목록)은 메타 저장소
  `docs/architecture/`에 둔다. app-pocket 브릿지 계약과 같은 방식이다

### web 저장소 구성
- Next.js(App Router) 단일 패키지로 만든다. monorepo 도구(pnpm workspace, Turborepo)는 쓰지 않는다.
  패키지 매니저는 pnpm, Node `>=24`다
- 편집기 화면은 클라이언트 컴포넌트로 만든다. 보드, iframe, 오버레이가 모두 브라우저 상태에 의존하기 때문이다
- 편집기 상태 관리는 zustand다. 문서는 `DocSource`가 소유하고 스토어는 그 구독 결과를 반영한다. 선택·뷰포트 같은 UI 상태는 스토어가 소유한다
- 런타임과 도구는 `create-next-app` 템플릿 값을 따른다: Next 16.4, React 19.3, TypeScript 5.9, ESLint 9, Tailwind v4, pnpm 10.23
- 디렉터리는 `src/model`(스키마, 연산 검증·적용), `src/render`(HTML/CSS 변환기), 편집기 UI(`src/app`,
  `src/editor`)로 나눈다. 의존 방향은 편집기 → render → model이고, render와 model은 DOM·React·Next에
  의존하지 않는다
- 서버가 헤드리스 Chromium에서 불러 쓸 단독 ESM 번들 `render.js`는 Next 빌드와 별도로 tsdown으로
  만든다(common-design과 같은 번들러). 2단계 착수 시 추가한다 (제안, 승인 대기)

### web·server 계약과 원칙 유지 방식
- 하나의 렌더 경로(원칙 2): 서버는 변환기를 다시 구현하지 않는다. 헤드리스 Chromium 페이지에 web의
  `render.js`를 불러 같은 함수로 `srcdoc`·`annotated` 출력을 만든다. 서버 렌더와 `inspect`가 편집기와 같은
  코드, 같은 엔진을 쓴다
- 서버가 최종 검증(원칙 4): 서버는 `apply_ops` 검증·적용을 자기 언어로 구현한다. web의 TypeScript 구현과
  일치하는지는 공유 적합성 fixture로 보장한다
  - `docs/architecture/trama-ops.schema.json`: web의 zod 스키마에서 생성한 JSON Schema. 서버는 여기서 타입을 만든다
  - `docs/architecture/trama-ops-conformance/`: `{문서, 연산, 기대 결과 또는 오류 코드}` 사례 묶음. 두 구현이 모두 통과해야 한다
  - 출력 CSS 허용 목록도 코드가 아니라 데이터 파일로 계약에 둔다
- 스키마는 zod 4로 정의하고 `z.toJSONSchema()`로 JSON Schema를 생성한다

### 1단계에서 "서버가 최종 검증" 원칙을 지키는 방식
- 편집기는 문서 상태를 직접 바꾸지 않는다. 모든 편집은 `apply_ops` 연산 배열을 만들어 문서 소스(`DocSource`)에 보낸다
- 1단계 구현은 `LocalSource`다. 브라우저 안에서 `src/model`의 검증·적용 함수를 호출한다. 2단계에서
  WebSocket으로 서버에 보내는 `RemoteSource`로 교체한다. 편집기 코드는 바뀌지 않는다
- 연산 트랜잭션에는 처음부터 `actor`와 `txId`를 둔다. 1단계 actor는 로컬 사용자 하나다
- Undo는 적용 결과로 역연산을 만들어 actor별 스택에 쌓는다. 트랜잭션 1개가 Undo 1단계다
- 저장은 IndexedDB이고, 문서 JSON 파일로 내보내기·가져오기를 지원한다

### 문서 모델
- `docs/architecture/trama-document-model.md` 초안을 v0.2 구현 기준으로 승인했다. 구현 중 바뀌는 부분은 문서를 함께 고친다. 핵심은 아래와 같다
  - 문서는 `객체 ID → 속성 키 → 값`의 평면 맵이고, 충돌 단위는 `(ID, 키)` 하나다
  - 트리는 `parent` + `order`(fractional index)로 표현하고, 연산은 `placement` 필드로 위치 지정(`first`, `last`, `before`, `after`)만 받는다. CSS에 대응하는 노드 속성 `position`과 구분하기 위해 이 이름을 쓴다
  - override는 `기본키@bp:<BP ID>@var:<속성 ID>=<값>@state:<상태>` 키로 저장한다. BP와 속성을 ID로 참조한다
  - 연산은 `create`, `set`, `move`, `delete`, `detach` 5개다. 레이아웃·토큰 바인딩·인스턴스 속성 변경은 모두 `set`이다
  - Undo는 이전 값으로 되돌리는 새 트랜잭션이며, 이후 다른 참여자가 바꾼 키는 건너뛴다
  - 텍스트 `content`는 서식 없는 문자열이다. 인라인 서식은 이후 구조 확장 시 다시 정한다
  - 절대 배치는 부모의 레이아웃 모드가 아니라 노드 속성이다. 모든 노드는 편집기에서 rect(x, y, w, h)로 다루고, `position`(기본 `static`)을 `absolute`로 바꾸면 그 순간의 rect를 부모 좌상단 기준으로 저장한다. 제약(우측·중앙 고정 등)은 두지 않고, static으로 되돌려도 좌표는 보존한다

### 변환기
- `src/render`는 순수 함수다. DOM·브라우저 API에 의존하지 않는다
- 출력 클래스 이름은 노드 ID 기반 `.n-<id>`다. 항상 유일하고 레이어 이름 변경이 출력에 영향을 주지 않는다
- 문서 → 중간 트리(요소 트리 + CSS 규칙 목록) → 직렬화 순서로 변환한다. 직렬화 대상은 3개다
  - `export`: 내보내기용 HTML/CSS
  - `srcdoc`: 편집기 iframe용. `data-id`를 포함한다
  - `annotated`: AI 읽기용 주석 HTML (`data-id`, `data-layout`)
  세 출력이 같은 중간 트리에서 나오므로 "하나의 렌더 경로" 원칙이 유지된다
- 결정성 규칙: CSS 규칙은 트리 순서로 내보내고, 노드 안에서는 base → BP 오름차순 → 변형(속성 정의 순서) →
  상태 순으로 내보낸다. 선언은 속성 이름순으로 정렬하고 숫자 표기를 고정한다. "같은 입력이면 바이트 단위로
  같은 출력"을 golden 테스트로 검증한다
- 출력 CSS 허용 목록은 `web-features` 패키지의 Baseline 상태(`high` = Widely available)에서 생성하고, 패키지
  버전을 고정한다. 허용 목록 밖의 속성은 `apply_ops` 검증 단계에서 거부한다

### 설계 문서 위치
- 노드 모델·연산 스키마와 HTML 변환 규칙은 `docs/architecture/trama-document-model.md`,
  `docs/architecture/trama-html-conversion.md`에 현행 명세로 둔다. 다른 언어로 만드는 서버와 외부 AI(MCP)가
  같은 계약을 따르기 때문이다. 기계 판독용 계약 파일(JSON Schema, 적합성 fixture, CSS 허용 목록)도 같은 폴더에 둔다

## 진행 중: v0.3 작업 영역

- 컨텍스트: v0.2의 model·render 위에 첫 편집기 UI를 올려, 사람이 문서를 만들고 고치고 내보낼 수 있게 한다
- 핵심 기능 (모두 완료되면 릴리스):
  - [x] `LocalSource`: 모든 편집을 `apply_ops`로 적용, actor별 Undo·Redo, IndexedDB 저장, 문서 JSON 내보내기·가져오기
  - [x] 보드: 팬/줌, Frame별 `srcdoc` iframe(`sandbox="allow-same-origin"`, `pointer-events: none`)
  - [x] 오버레이: 역변환 좌표로 선택, 선택 테두리
  - [x] 레이어 트리와 속성 패널로 노드 추가·삭제·이동·속성 편집
  - [x] 드래그앤드롭: flow 컨테이너는 삽입 인덱스, absolute 노드는 좌표 이동
  - [x] 기본 스타일 키: 배경색, 글자색·크기·굵기, padding, border, radius. 값은 Dimension·Color(srgb). 허용 목록 생성(web-features)은 이후 버전에서 대체한다
  - [x] HTML 미리보기: 내보내기 HTML(CSS 인라인)을 팝업에서 코드로 보여주고 복사한다. 코드 강조는 shiki. 폴더에 파일을 쓰는 방식은 브라우저 보안 제약으로 쓰지 않는다
- 세부 step:
  - [x] model: 적용 결과로 `(ID, 키)`별 변경 목록을 돌려주고, 변경 목록으로 되돌리는 함수 추가
  - [x] `LocalSource`와 zustand 스토어
  - [x] 보드·iframe·오버레이
  - [x] 레이어 트리·속성 패널
  - [x] 드래그앤드롭
  - [x] IndexedDB 저장, JSON 저장·열기, HTML 미리보기
- 다음 행동: v0.3 핵심 기능 완료. push 전 주석 점검 후 PR, 릴리스한다

## 다음 버전 (계획)

1단계(web)
- v0.4 반응형과 오버플로: Frame별 BP 목록, BP override, `minWidth`, `<picture>`, fold 라인·minWidth 점선·빨간
  아웃라인 표시, 화면 밖 Frame 가상화
- v0.5 디자인 토큰: 토큰 표 편집기, modifier, 토큰 순환 검사, 조합 미리보기, 램프 생성기, DTCG 2025.10
  가져오기/내보내기, `[data-*]`·`prefers-color-scheme` CSS 출력
- v0.6 컴포넌트: 원본·인스턴스·변형·상태, `.c-*` 클래스와 `data-*` 선택자 출력

2단계(server, infra). 버전 번호는 1단계를 마칠 때 정한다
- 동기화 서버: WebSocket, 속성 단위 LWW, presence, 연산 로그, PostgreSQL, `RemoteSource`
- AI: MCP(Streamable HTTP) 도구, Playwright 헤드리스 렌더와 `inspect`, AI 세션 스냅샷과 변경 기록 패널
- 인프라: terraform

## 완료
- v0.2 (2026-10-31) 문서 모델과 변환기: `apply_ops`(`create`·`set`·`move`·`delete`) 검증·적용과 노드 5종의 HTML/CSS 변환(`export`·`srcdoc`·`annotated`), golden 테스트. 계약 문서 2개와 JSON Schema·적합성 fixture를 web 테스트가 생성
- v0.1 (2026-10-31) 최초 골격: Next.js 앱과 `src/model`·`src/render`·`src/editor` 골격, common-design(`theme-neutral`) 빈 편집기 셸, `cliff.toml`. 프로젝트 `CLAUDE.md`·색인·Slack 매핑 구성

## 미확정 사항

- 이미지 자산 저장: 1단계 IndexedDB blob, 내보내기 시 파일 묶음 형식, 2단계 객체 저장소
- 웹폰트: `fontFamily` 토큰이 가리키는 폰트의 로딩 방식과 내보내기 포함 여부
- 서버 언어와 배포 대상(terraform 프로바이더). 2단계 착수 전에 정한다
- 2단계 저장소의 등록 방식: todo 파일명 규칙(`<디렉터리명>-todo.md`)과 Slack 채널-디렉터리 1:1 매핑은 저장소가 하나일 때를 전제한다. server·infra 저장소가 생기면 이 todo와 채널을 어떻게 대응시킬지 정한다
- 문서 모델 초안의 미확정 사항 (`docs/architecture/trama-document-model.md` 11절)
- 명세 Q15·"기술 스택과 대상 브라우저" 절을 서버 언어 철회에 맞게 고칠지 여부. 레이아웃 규칙 5("absolute 컨테이너")도 노드 단위 `position` 결정과 어긋난다
