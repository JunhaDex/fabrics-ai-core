# trama 문서 모델과 연산 계약 (초안)

trama 문서의 데이터 구조, 속성 키, override 키 문법, `apply_ops` 연산, 검증 규칙,
오류 코드의 현행 명세다. web(편집기, TypeScript)과 server(Kotlin)의 두 구현,
그리고 MCP로 접속하는 AI가 이 문서를 그대로 따른다. 요구사항의 정본은
`../references/fabrics-tala-requirements.md`이고, 결정의 근거는 `../trama-web-todo.md`의
"결정 사항"에 있다. HTML/CSS 변환 규칙은 `trama-html-conversion.md`가 담당한다.

- 상태: v0.6. 노드 7종(frame, component, section, container, text, image, instance), `breakpoint`, `componentProp`,
  `modifier`, `token`, 연산 5개(`create`, `set`, `move`, `delete`, `detach`), `@bp`·`@cq`·`@var`·`@state`·`@ctx` 조건 키,
  토큰 바인딩, 인스턴스 override를 구현했다
- 기계 판독용 계약은 web의 테스트가 생성한다(`vitest run -u`). 손으로 고치지 않는다
  - `trama-ops.schema.json`: 트랜잭션과 종류별 props의 JSON Schema. 소수 자릿수 제한처럼 JSON Schema로
    표현되지 않는 조건은 `description`에 적는다
  - `trama-ops-conformance/*.json`: `{ name, doc, tx, expect }` 사례 묶음. `expect`는 `{ ok: true, doc }` 또는
    `{ ok: false, error: { code, opIndex, id, key } }`이며, 결과 문서의 `order` 키까지 일치해야 한다

## 1. 문서 구조

```json
{
  "schemaVersion": 1,
  "objects": {
    "f1": { "type": "frame", "parent": null, "order": "a0", "name": "Pricing", "minWidth": 320 },
    "s1": { "type": "section", "parent": "f1", "order": "a0", "tag": "header" },
    "t1": { "type": "text", "parent": "s1", "order": "a0", "tag": "h2", "content": "요금제",
            "style.color": { "token": "tk7" } }
  }
}
```

- 문서는 `객체 ID → 속성 키 → 값`의 평면 맵이다. 노드, BP, 토큰, modifier, 컴포넌트
  속성 정의가 모두 같은 맵의 객체다
- 동시 편집의 충돌 단위는 `(객체 ID, 속성 키)` 하나다. 같은 쌍을 동시에 바꾸면 서버에
  나중에 도착한 값이 이긴다(LWW). 값이 배열이나 객체여도 통째로 하나의 값이다
- 속성이 없는 것과 기본값은 같은 의미다. `set`에서 값으로 `null`을 주면 속성을 지운다
- `type`은 생성 후 바꿀 수 없다
- `schemaVersion`이 오르면 이전 문서를 변환하는 마이그레이션을 두 구현이 같은 규칙으로 갖는다

## 2. 객체 ID

- 정규식 `^[A-Za-z0-9_-]{6,32}$` 또는 예약 형식 `^_[a-z]{1,31}$`. 생성하는 쪽(편집기, AI)이 충돌 확률이
  무시할 만한 랜덤 문자열로 만든다. 편집기는 21자 nanoid를 쓴다
- 이미 있는 ID로 생성하면 `ID_CONFLICT`로 거부한다
- 예약 ID는 `_`로 시작하며 사용자 생성에 쓸 수 없다. `_mode`는 기본 제공 modifier다

## 3. 객체 종류와 트리

| type | 부모 | 역할 |
|---|---|---|
| `frame` | 없음(`null`) | 보드 위 화면 하나. `<body>`로 출력 |
| `component` | 없음(`null`) | 컴포넌트 원본의 루트. 보드 위에 놓인다 |
| `section` | `frame` | `<section>` 등 시맨틱 영역 |
| `container` | 노드 | 레이아웃 컨테이너 |
| `text` | 노드 | 텍스트. 자식 없음 |
| `image` | 노드 | 이미지. 자식 없음 |
| `instance` | 노드 | 컴포넌트 인스턴스. 자식 없음(원본 트리를 펼쳐 출력) |
| `breakpoint` | `frame` | Frame의 BP 하나 |
| `componentProp` | `component` | 컴포넌트 속성(변형 축) 정의 |
| `token` | 없음 | 디자인 토큰 |
| `modifier` | 없음 | 토큰의 전역 기준(mode, palette 등) |

- "노드"는 `frame`, `component`, `section`, `container`, `text`, `image`, `instance`다
- `container`, `text`, `image`, `instance`의 부모는 `frame`, `component`, `section`,
  `container` 중 하나다. `section`의 부모는 `frame`만 가능하다
- 트리는 각 객체의 `parent`와 `order`로만 표현한다. 부모가 자식 배열을 갖지 않는다
- 형제 순서는 `(order, id)`의 사전순이다. `order`가 같으면 `id`로 정해지므로 결과가 항상 결정적이다
- 이동으로 순환이 생기면 `TREE_CYCLE`로 거부한다. 인스턴스를 만들거나 옮겨 컴포넌트가 (중첩 인스턴스를 거쳐)
  자기 자신의 인스턴스를 포함하게 되는 경우도 `TREE_CYCLE`이다

### order (fractional index)

- base62 문자열 키다. 두 키 사이에 항상 새 키를 만들 수 있어, 동시에 삽입해도 다른 형제의 키가 바뀌지 않는다
- 알고리즘은 David Greenspan의 "Implementing Fractional Indexing"을 따른다(npm
  `fractional-indexing`과 같은 결과). 서버 구현도 같은 결과를 내야 하며 적합성 fixture로 검증한다
- 연산은 `order`를 직접 받지 않고 `placement` 필드로 위치 지정(`first`, `last`, `{ before: id }`, `{ after: id }`)을
  받는다. 서버가 키를 계산한다. AI는 fractional index를 다루지 않는다

## 4. 값 형식

| 형식 | 예 | 비고 |
|---|---|---|
| Dimension | `{ "value": 16, "unit": "px" }` | unit: `px`, `rem`, `%`(스타일 원시값만) |
| Color | `{ "colorSpace": "srgb", "components": [0.2, 0.4, 1], "alpha": 0.5 }` | DTCG 2025.10 color 객체. v0.3은 `srgb`만 허용하며 성분과 `alpha`는 0~1, 소수 넷째 자리까지. `alpha`가 없으면 1 |
| 토큰 바인딩 | `{ "token": "tk7" }` | 토큰 ID로 저장한다. 이름을 바꿔도 깨지지 않는다 |
| 토큰 참조 | `{ "ref": "tk3" }` | 토큰 값이 다른 토큰을 가리킬 때만 쓴다 |
| 자산 | `{ "asset": "as1" }` | 이미지 원본. 저장 방식은 미확정 |
| 키워드 | `"fill"`, `"center"` | 속성별 허용 목록 안의 문자열 |

- 숫자는 유한한 JSON number다. 두 구현의 직렬화 차이를 없애기 위해 Dimension `value`는
  소수 넷째 자리까지만 허용한다
- 토큰 바인딩은 속성이 기대하는 타입과 토큰의 `tokenType`이 같아야 한다(`TOKEN_TYPE_MISMATCH`)

## 5. 노드 속성 키

키는 `영역.이름` 형식이다. 스타일 키는 CSS 속성 이름을 그대로 쓴다.

### 공통 (모든 노드)

| 키 | 값 | 기본값 |
|---|---|---|
| `parent`, `order` | ID, order 키 | — |
| `name` | 문자열 | 레이어 패널 표시명 |
| `tag` | 종류별 허용 태그 | 종류별 기본 태그 |
| `hidden` | boolean | `false` |

종류별 허용 태그:
- `section`: `section`, `header`, `footer`, `nav`, `main`, `aside`, `article`
- `container`, `component`: `div`, `ul`, `ol`, `li`, `figure`, `a`, `button`, `form`, `label`
- `text`: `p`, `h1`~`h6`, `span`, `strong`, `em`, `small`, `label`, `a`, `button`, `li`

### 레이아웃 (`frame`, `component`, `section`, `container`)

| 키 | 값 | 기본값 |
|---|---|---|
| `layout.mode` | `flex-row`, `flex-column`, `grid` | `flex-column` |
| `layout.gap`, `layout.rowGap` | Dimension, 토큰 바인딩 | 0 |
| `layout.justify` | `start`, `center`, `end`, `space-between`, `space-around`, `space-evenly` | `start` |
| `layout.align` | `start`, `center`, `end`, `stretch`, `baseline` | `stretch` |
| `layout.wrap` | boolean (flex만) | `false` |
| `layout.columns` | 1 이상 정수 (grid만) | 1 |
| `layout.clip` | boolean. 넘치는 자식을 자른다 | `false` |

### 자식 배치 (부모의 레이아웃 모드에 따라 유효)

| 키 | 값 | 유효 조건 |
|---|---|---|
| `size.width`, `size.height` | `fill`, `hug`, Dimension, 토큰 바인딩 | 항상 |
| `size.minWidth`, `size.maxWidth`, `size.minHeight`, `size.maxHeight` | Dimension, 토큰 바인딩 | 항상 |
| `grid.colStart`, `grid.colSpan`, `grid.rowStart`, `grid.rowSpan` | 1 이상 정수 | 부모가 `grid` |
| `position` | `static`, `absolute` | 항상. 기본 `static` |
| `x`, `y`, `w`, `h` | number(px, 소수 넷째 자리까지). `w`, `h`는 0 이상 | `position`이 `absolute` |

- 유효 조건을 벗어난 키는 지우지 않고 보존하며 변환기가 무시한다. 부모의 레이아웃 모드를
  바꿨다가 되돌려도 자식의 배치 정보가 남는다
- 자식 sizing의 기본값은 부모 방향의 주축이 `hug`, 교차축이 `fill`이다(정확한 CSS 대응은 변환 규칙 문서)
- 편집기는 모든 노드를 렌더 결과의 rect(x, y, w, h)로 다룬다. rect는 측정값이며 문서에 저장하지 않는다
- `position`을 `absolute`로 바꾸면 편집기가 그 순간의 rect를 부모 좌상단 기준으로 `x`, `y`, `w`, `h`에 저장한다.
  absolute 노드는 부모의 흐름에서 빠지며, 같은 부모 안에 static 자식과 섞일 수 있다. 이때 `size.*`, `grid.*`는 무시한다
- `static`으로 되돌려도 `x`, `y`, `w`, `h`는 지우지 않는다. 다시 `absolute`로 바꾸면 그 시점의 rect로 덮어쓴다
- 제약(우측·중앙 고정, 늘이기)은 두지 않는다. absolute 노드는 부모 좌상단 기준 고정 배치만 한다

### 스타일

- 키는 `style.<CSS 속성 이름>`이다. 예: `style.background-color`, `style.padding-top`, `style.font-size`
- 허용 속성은 계약 파일의 스타일 허용 목록에 있는 것만이다(`STYLE_NOT_ALLOWED`). 레이아웃 모델을
  우회하는 속성(`display`, `position`, `flex-*`, `grid-*`, `width`, `height`, `top`, `left`, `float`,
  `margin*` 등)은 목록에 넣지 않는다. 값은 Baseline Widely available 허용 목록 안에 있어야 한다
- 값은 속성별 형식(Dimension, Color, 키워드) 또는 토큰 바인딩이다
- 현재 허용하는 스타일 키는 아래와 같다. web-features 기반 허용 목록은 이후 버전에서 이 목록을 대체한다

| 키 | 값 | 노드 |
|---|---|---|
| `style.background-color` | Color | 전체 |
| `style.color` | Color | image 제외 |
| `style.font-size` | Dimension | image 제외 |
| `style.font-weight` | 100~900의 100 단위 정수 | image 제외 |
| `style.font-family` | 토큰 바인딩만 (`fontFamily` 토큰) | image 제외 |
| `style.padding-top`, `-right`, `-bottom`, `-left` | Dimension | frame 제외 |
| `style.border-width`, `style.border-radius` | Dimension | frame 제외 |
| `style.border-style` | `none`, `solid`, `dashed`, `dotted` | frame 제외 |
| `style.border-color` | Color | frame 제외 |
| `style.object-fit` | `cover`, `contain`, `fill` | image |

- frame에 padding이 없는 것은 `safeArea`가 `body`의 padding을 쓰기 때문이다
- 토큰 바인딩(`{ "token": ID }`)을 받는 키와 토큰 타입: Color 키는 `color`, Dimension 키(`style.*`, `layout.gap`,
  `layout.rowGap`, `size.*`)는 `dimension`, `style.font-weight`는 `fontWeight`, `style.font-family`는 `fontFamily`.
  토큰이 없으면 `UNKNOWN_OBJECT`, 타입이 다르면 `TOKEN_TYPE_MISMATCH`다. `@bp` 조건 키에도 바인딩할 수 있다

### 종류별 고유 속성

| type | 키 | 값 |
|---|---|---|
| `frame` | `boardX`, `boardY` | 보드 좌표(px) |
| `frame` | `previewWidth`, `previewHeight` | 미리보기 뷰포트 크기. 출력에 영향 없음 |
| `frame` | `baseLabel` | base 구간의 표시 이름. 기본 `"Mobile"` |
| `frame` | `minWidth` | number(px). 기본 320 |
| `frame` | `safeArea` | boolean. safe area inset 처리 여부. 기본 `false` |
| `component` | `boardX`, `boardY` | 보드 좌표(px) |
| `component` | `previewWidth`, `previewHeight` | 컴포넌트 보드 미리보기 크기. 출력에 영향 없음 |
| `text` | `content` | 문자열(서식 없는 텍스트) |
| `image` | `src`, `alt` | 자산, 문자열 |
| `image` | `style.object-fit` | `cover`, `contain`, `fill` |
| `instance` | `component` | 원본 `component` ID. 생성 후 변경 불가 |
| `instance` | `props.<componentProp ID>` | 선택한 옵션 값 |
| `instance` | `node.<경로>.<키>` | 인스턴스 override (아래 8절) |
| `breakpoint` | `minWidth` | number(px). 같은 Frame 안에서 유일, Frame `minWidth`보다 커야 함 |
| `breakpoint` | `name` | 표시 이름 |

## 6. BP와 override 키 문법

```
키        := 기본키 ( "@" 조건 )*
조건      := "bp:" BP_ID
           | "cq:" 1~99999 정수(px, 앞자리 0 없음)
           | "var:" componentProp_ID "=" 옵션값
           | "state:" ( "hover" | "pressed" | "focus" | "disabled" )
```

- 예: `layout.mode@bp:bp2`, `style.font-size@bp:bp2`, `size.width@cq:200`, `style.background-color@var:cp1=danger`,
  `style.background-color@var:cp1=danger@state:hover`
- 조건은 종류마다 최대 1개이고 `bp|cq → var → state` 순서로만 쓴다. 다른 순서는 `KEY_INVALID`로
  거부한다. 같은 의미의 키가 두 가지로 저장되는 일을 막아 결정성을 지킨다
- `@bp`와 `@cq`는 함께 쓸 수 없다. `@cq`는 다른 조건과도 조합할 수 없다(`CONDITION_NOT_ALLOWED`)
- 조건 없는 키가 base 값이다. base 구간은 Frame의 가장 작은 BP보다 좁은 폭이며, mobile-first로
  BP의 `minWidth` 오름차순으로 덮어쓴다
- BP를 ID로 참조하므로 BP의 `minWidth`를 바꿔도 override 키는 그대로다. Frame 생성 시 BP 2개
  (768, 1280)를 함께 만들어 base까지 기본 3구간이 된다

### 조건별 허용 키

| 기본키 | `@bp` | `@cq` | `@var` | `@state` |
|---|---|---|---|---|
| `layout.*`, `size.*`, `grid.*`, `x`, `y`, `w`, `h` | 허용 | 허용 | 허용 | 불허 |
| `style.*` | 허용 | 허용 | 허용 | 허용 |
| `hidden` | 허용 | 허용 | 허용 | 불허 |
| `src` (image) | 허용 (`<picture>`로 출력) | 불허 | 불허 | 불허 |
| `position` | 불허 | 불허 | 불허 | 불허 |
| `content`, `tag`, `name`, `parent`, `order` 등 구조·텍스트 | 불허 | 불허 | 불허 | 불허 |

- `position`에는 조건을 붙일 수 없다(`CONDITION_NOT_ALLOWED`). 노드가 흐름 배치인지 절대 배치인지가
  BP마다 달라지는 것을 막기 위해서다
- 조건은 노드에만 붙일 수 있다. `@bp`는 Frame 안의 노드에만 쓰고, BP는 그 노드가 속한 Frame의 것이어야 한다
- `@cq`, `@var`, `@state`는 컴포넌트 원본 안의 노드에만 쓴다. `@cq`는 컴포넌트 원본의 폭을 기준으로 하므로 원본 루트
  자신에는 쓸 수 없다. `var`의 속성과 옵션은 그 컴포넌트의 것이어야 한다
- BP나 `componentProp`을 삭제하면 그것을 참조하는 조건 키가 같은 트랜잭션 안에서 함께 삭제된다. enum `options`에서
  빠진 옵션의 `@var` 키와 인스턴스 `props.*` 값도 같이 삭제된다
- 노드를 다른 루트(Frame 또는 컴포넌트)로 `move`하면 그 노드와 하위 노드의 조건 키가 모두 같은 트랜잭션 안에서
  삭제된다. 조건이 원래 루트의 BP·속성을 가리키므로 대상이 없어지기 때문이다
- 조건 키의 값은 기본키의 값 형식을 따른다. `trama-ops.schema.json`의 종류별 props 정의는 기본키만 나열하므로,
  조건 키는 기본키 정의로 검증한다
- 검증 순서: 기본키가 그 종류에 없으면 `KEY_NOT_ALLOWED`, 조건 문법·순서가 틀리면 `KEY_INVALID`, 노드가 아니거나
  기본키가 위 표에서 불허이거나 `@cq`를 다른 조건과 조합했거나 루트 종류가 맞지 않거나 컴포넌트 루트에 `@cq`를 쓰면
  `CONDITION_NOT_ALLOWED`, BP·속성·옵션이 없으면 `CONDITION_TARGET_MISSING`, 값이 맞지 않으면 `VALUE_INVALID`
- BP의 `minWidth`가 없거나, 같은 Frame의 다른 BP와 같거나, Frame `minWidth` 이하이면 `VALUE_INVALID`다.
  Frame `minWidth`를 바꿀 때도 같은 조건을 검사한다

## 7. 토큰과 modifier

### modifier

| 키 | 값 |
|---|---|
| `name` | 식별자(`^[a-z][a-z0-9-]*$`). CSS `data-<name>` 속성 이름이 된다. 전역 유일이며 `mode`는 예약 |
| `contexts` | 식별자 배열, 2개 이상, 중복 없음. 예: `["light", "dark"]` |
| `default` | `contexts` 중 하나 |

- 예약 modifier `_mode`(`name: "mode"`, `contexts: ["light", "dark"]`, `default: "light"`)는 항상 존재하고 바꾸거나
  삭제할 수 없다
- `contexts`에서 빠진 컨텍스트의 `value@ctx:` 키는 같은 트랜잭션 안에서 삭제된다. `default`는 `contexts` 중
  하나여야 한다(`VALUE_INVALID`). 토큰이 `variesBy`로 가리키는 modifier는 삭제할 수 없다(`TOKEN_IN_USE`)
- `contexts`는 배열 하나가 LWW 단위다. 두 사람이 동시에 컨텍스트를 추가하면 한쪽이 사라질 수 있다.
  빈도가 낮아 허용한다

### token

| 키 | 값 |
|---|---|
| `name` | 점 경로(`color.action.primary`). 각 구간은 영문자로 시작하는 영숫자다. 전역 유일 |
| `tokenType` | DTCG 타입. v0.5는 `color`, `dimension`, `fontFamily`, `fontWeight`, `number` |
| `value` | 타입에 맞는 원시값 또는 `{ "ref": 토큰 ID }` |
| `variesBy` | modifier ID 또는 `null` |
| `value@ctx:<컨텍스트>` | 그 컨텍스트의 값. 없으면 `value`를 상속 |
| `description`, `deprecated` | 문자열, boolean |

- 토큰 하나는 `variesBy`에 지정한 modifier 하나에 대해서만 값이 달라진다. `@ctx:` 키는
  `variesBy` modifier의 컨텍스트만 쓸 수 있다. `variesBy`를 바꾸면 이전 `@ctx:` 키가 같은 트랜잭션
  안에서 삭제된다
- 참조 대상의 `tokenType`이 같아야 한다. 모든 modifier 컨텍스트 조합에서 참조를 따라가 순환이
  생기면 `TOKEN_CYCLE`로 거부한다
- 노드나 다른 토큰이 참조하는 토큰은 삭제할 수 없다(`TOKEN_IN_USE`)
- Raw/Alias 구분, 해석값, 역참조, 사용 횟수는 저장하지 않고 계산한다
- 타입별 원시값: `color`는 Color, `dimension`은 Dimension, `fontFamily`는 문자열 또는 문자열 배열이며 마지막 항목이
  일반 계열(`serif`, `sans-serif`, `monospace`, `system-ui` 등), `fontWeight`는 1~1000 정수, `number`는 유한한 수
- 토큰에는 `name`, `tokenType`, `value`가 필요하다. 이름이 겹치면 `NAME_CONFLICT`다
- 검사 시점: 토큰·modifier를 만들거나 바꿀 때마다 전체 토큰의 이름, 값 형식, 참조, 컨텍스트, 순환을 검사한다

## 8. 컴포넌트와 인스턴스

### componentProp

| 키 | 값 |
|---|---|
| `name` | 식별자(`^[a-z][a-z0-9-]*$`). 출력 `data-<name>` 속성 이름. 같은 컴포넌트 안에서 유일 |
| `kind` | `enum`, `boolean` |
| `options` | `enum`에만 둔다. 옵션 값 배열(식별자), 1개 이상, 중복 없음. `boolean`의 옵션은 `["true", "false"]`로 고정 |
| `default` | 옵션 값 하나 |

- `name`, `kind`, `default`가 필요하고, `options`는 `enum`에만 반드시 둔다. 어기면 `VALUE_INVALID`, 이름이 겹치면 `NAME_CONFLICT`다
- 속성 정의 순서는 `name`의 사전순이다. 같은 노드·같은 키를 두 속성의 `@var`가 바꾸면 뒤의 것이 이긴다
- componentProp에는 `order`가 없다(노드가 아니다)

### component와 instance

- `component`는 보드 위 루트이며 레이아웃 키와 스타일 키를 가진다. 출력 태그는 `tag`(기본 `div`)다
- `instance`를 만들 때 `component`가 필요하다. 없으면 `VALUE_INVALID`, 가리키는 컴포넌트가 없으면 `UNKNOWN_OBJECT`다
- `props.<componentProp ID>`는 그 컴포넌트의 속성이어야 하고(`CONDITION_TARGET_MISSING`), 값은 그 속성의 옵션
  값이어야 한다(`VALUE_INVALID`). 값이 없으면 속성의 `default`다
- 인스턴스가 하나라도 있는 컴포넌트는 삭제할 수 없다(`COMPONENT_IN_USE`)

### 인스턴스 override

- 키 형식: `node.<경로>.<기본키>`. 경로의 첫 구간은 원본 컴포넌트 트리의 노드 ID다. 중첩 인스턴스 안의 노드는
  `/`로 이어 `node.<인스턴스 ID>/<노드 ID>.<키>`로 가리키며, 앞 구간은 인스턴스여야 한다.
  예: `node.n13.content`, `node.n20.src`, `node.n13.style.color`, `node.cta01/label1.content`
- 허용: text의 `content`, image의 `src`·`alt`, 원본 루트를 제외한 노드의 `hidden`, 그리고 원본 값이 토큰 바인딩인
  키의 다른 토큰 바인딩
- 검증: 경로 문법이 틀리면 `KEY_INVALID`, 조건(`@` 이후)을 붙이면 `CONDITION_NOT_ALLOWED`, 경로가 가리키는 노드가
  없으면 `CONDITION_TARGET_MISSING`, 위 허용 범위 밖이면 `KEY_NOT_ALLOWED`, 값 형식이 틀리면 `VALUE_INVALID`
- 구조 변경(자식 추가·삭제·이동)은 인스턴스 안에서 할 수 없다. 인스턴스는 자식을 갖지 않으며(`INVALID_PARENT`),
  필요하면 `detach`한다
- 노드 ID가 모든 변형에서 같으므로, `props.*`를 바꿔도 `node.*` override가 유지된다
- override는 원본의 base 값을 대신한다. 원본의 `@var`·`@state`·`@cq` 값은 override보다 우선한다
- 원본 노드를 삭제하거나 옮겨 경로가 더는 노드를 가리키지 않으면, 그 override 키는 같은 트랜잭션 안에서 삭제된다

### detach

- 인스턴스를 같은 위치(`parent`, `order`)의 일반 노드 트리로 바꾼다. 원본 루트는 `container`가 되고, 인스턴스 자신의
  공통·배치 키(`name`, `hidden`, `size.*`, `@bp` 키 등)가 그 위에 덮인다
- 새 노드 ID: `"<인스턴스 ID>/<원본 노드 ID>"`의 UTF-8 SHA-256을 부호 없는 빅엔디언 정수로 보고, 62진수(`0-9A-Za-z`)의
  가장 낮은 자리부터 21자를 낸다. 같은 인스턴스는 항상 같은 ID를 만든다. 이미 있는 ID면 `ID_CONFLICT`다
- 인스턴스가 고른 변형의 `@var` 값과 override는 base 값으로 굳힌다. `@state`·`@cq` 키는 일반 노드가 가질 수 없으므로
  버린다. 중첩 인스턴스는 인스턴스로 남고, 그 안을 가리키던 override는 경로 앞 구간을 떼어 옮긴다
- 인스턴스가 아니면 `VALUE_INVALID`다

## 9. apply_ops

### 트랜잭션

```json
{
  "txId": "tx_9f2…",
  "actor": "user:dex",
  "ops": [
    { "op": "create", "id": "c1", "type": "container", "parent": "s1", "placement": "last",
      "props": { "layout.mode": "flex-row", "layout.gap": { "token": "tk2" } } },
    { "op": "set", "id": "t1", "props": { "content": "요금 안내", "style.font-size@bp:bp2": { "token": "tk9" } } },
    { "op": "move", "id": "t1", "parent": "c1", "placement": "first" }
  ]
}
```

- 한 트랜잭션은 전부 적용되거나 전부 거부된다. 연산은 배열 순서대로 적용하며, 뒤 연산은 앞
  연산의 결과를 본다(같은 트랜잭션에서 만든 노드를 바로 참조할 수 있다)
- `actor`는 `user:<id>` 또는 `ai:<세션 id>`다. AI 요청 1회가 트랜잭션 1개이자 Undo 1단계다
- 서버는 적용한 트랜잭션에 문서 단위의 단조 증가 `seq`를 매긴다. 모든 참여자는 `seq` 순서로 반영한다

### 연산

| op | 필드 | 동작 |
|---|---|---|
| `create` | `id`, `type`, `parent`, `placement`, `props` | 객체 생성. 노드는 `placement`가 필요하고, 노드가 아닌 객체(`breakpoint` 등)는 `placement`를 받지 않는다. 어기면 `VALUE_INVALID`(`key: "placement"`) |
| `set` | `id`, `props` | 속성 설정. 값 `null`은 삭제. 레이아웃, 스타일, 토큰 바인딩, 인스턴스 속성 변경이 모두 여기에 해당 |
| `move` | `id`, `parent`, `placement` | 부모와 순서 변경. 노드만 옮길 수 있다 |
| `delete` | `id` | 객체와 하위 노드, 그리고 그것을 참조하는 조건 키를 삭제 |
| `detach` | `id` | 인스턴스를 일반 노드 트리로 전환(8절) |

`placement`는 `"first"`, `"last"`, `{ "before": ID }`, `{ "after": ID }` 중 하나다. `before`·`after`의 기준
노드는 대상 부모의 자식이어야 하며, 없으면 `UNKNOWN_OBJECT`, 다른 부모의 자식이거나 자기 자신이면 `VALUE_INVALID`다.

### 응답

```json
{ "ok": true, "seq": 1042, "warnings": [{ "code": "TOKEN_DEPRECATED", "id": "t1", "key": "style.color" }] }
{ "ok": false, "error": { "code": "TREE_CYCLE", "opIndex": 2, "id": "c1", "key": null, "message": "…" } }
```

- `message`는 사람과 AI가 읽는 설명이며 계약에 포함하지 않는다. 판단은 `code`로 한다
- `warnings`는 적용된 트랜잭션에서 나온 경고 목록이며 없으면 빈 배열이다. 적합성 fixture의 성공 사례에 포함된다
- `id`는 오류가 난 객체다. `UNKNOWN_OBJECT`에서는 찾지 못한 ID다
- `SCHEMA_INVALID`의 `opIndex`는 위반 위치가 특정 연산 안이면 그 인덱스, 아니면 `null`이다

### Undo

- 서버는 트랜잭션을 적용할 때 각 `(ID, 키)`의 이전 값을 연산 로그에 남긴다. Undo는 그 이전 값으로
  되돌리는 새 트랜잭션이다
- 자기 변경만 되돌린다. 되돌릴 시점에 그 `(ID, 키)`의 현재 값이 자기 트랜잭션이 쓴 값과 다르면
  (다른 참여자가 이후에 바꿨으면) 그 키는 건너뛴다
- 1단계 `LocalSource`도 같은 규칙으로 동작한다

## 10. 검증 오류와 경고

### 오류 (트랜잭션 거부)

| 코드 | 조건 |
|---|---|
| `SCHEMA_INVALID` | 트랜잭션·연산 JSON이 스키마에 맞지 않음 |
| `UNKNOWN_OBJECT` | 대상·부모·참조 ID가 없음 |
| `ID_CONFLICT` | 이미 있는 ID로 생성, 또는 예약 ID 사용 |
| `TYPE_IMMUTABLE` | `type`, `instance.component` 변경 시도 |
| `INVALID_PARENT` | 3절의 부모 규칙 위반 |
| `TREE_CYCLE` | 이동으로 트리 순환 발생, 컴포넌트가 자기 자신의 인스턴스를 포함 |
| `KEY_INVALID` | 키 문법 오류, 조건 순서 오류 |
| `KEY_NOT_ALLOWED` | 그 객체 종류에 없는 키 |
| `CONDITION_NOT_ALLOWED` | 6절의 조건별 허용 키 위반 |
| `CONDITION_TARGET_MISSING` | 조건이 가리키는 BP·속성·옵션이 없거나 범위 밖 |
| `VALUE_INVALID` | 값 형식 또는 키워드 위반, 위치 지정의 기준 노드가 대상 부모의 자식이 아님 |
| `STYLE_NOT_ALLOWED` | 스타일 허용 목록 밖의 CSS 속성 또는 값 |
| `TOKEN_TYPE_MISMATCH` | 바인딩·참조의 타입 불일치 |
| `TOKEN_CYCLE` | 토큰 참조 순환 |
| `TOKEN_IN_USE` | 참조 중인 토큰 삭제 |
| `COMPONENT_IN_USE` | 인스턴스가 있는 컴포넌트 삭제 |
| `NAME_CONFLICT` | 토큰·modifier·componentProp 이름 중복 |
| `STRUCTURE_LOCKED` | 예약 modifier 변경·삭제 |

### 경고 (적용은 한다)

| 코드 | 조건 |
|---|---|
| `TOKEN_DEPRECATED` | `deprecated` 토큰을 바인딩 |
| `RAW_TOKEN_BOUND` | 원시값 토큰(참조가 아닌 토큰)을 노드에 직접 바인딩 |

오버플로·잘림 경고는 문서 검증이 아니라 렌더 결과의 검사이므로 `inspect`가 별도로 제공한다.

## 11. 확정했으나 아직 구현하지 않은 사항

결정 근거는 `../trama-web-todo.md`의 "미확정 사항에서 확정한 결정"이다. 해당 버전에서 위 절들에 반영한다.

- 텍스트 인라인 서식: 1단계는 서식 없는 문자열. 도입 시 `[{ text, marks }]` 구간 배열(marks: `strong`, `em`, `a`)
- 자산: `asset` 객체(mime, name, 크기), ID는 내용 SHA-256 해시. image `src`는 URL 문자열 또는 `{ "asset": ID }`
- enum 옵션 이름 변경 시 `@var` 키를 같은 트랜잭션에서 다시 씀. 현재 `options`에서 빠진 옵션은 이름 변경이 아니라 삭제로 처리한다
- `margin`은 허용하지 않음. grid 트랙 크기는 `layout.columns`의 트랙 크기 배열로 확장(필요 시)
