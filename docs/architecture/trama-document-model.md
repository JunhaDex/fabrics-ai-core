# trama 문서 모델과 연산 계약 (초안)

trama 문서의 데이터 구조, 속성 키, override 키 문법, `apply_ops` 연산, 검증 규칙,
오류 코드의 현행 명세다. web(편집기, TypeScript)과 server(언어 미정)의 두 구현,
그리고 MCP로 접속하는 AI가 이 문서를 그대로 따른다. 요구사항의 정본은
`../references/fabrics-tala-requirements.md`이고, 결정의 근거는 `../trama-web-todo.md`의
"결정 사항"에 있다. HTML/CSS 변환 규칙은 `trama-html-conversion.md`(작성 예정)가 담당한다.

- 상태: 초안. 승인 전이며 v0.2 구현 중에 확정한다
- 기계 판독용 계약: `trama-ops.schema.json`(web의 zod 스키마에서 생성),
  `trama-ops-conformance/`(두 구현이 모두 통과해야 하는 사례 묶음). v0.2에서 만든다

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

- 정규식 `^[A-Za-z0-9_-]{6,32}$`. 생성하는 쪽(편집기, AI)이 충돌 확률이 무시할 만한
  랜덤 문자열로 만든다. 편집기는 21자 nanoid를 쓴다
- 이미 있는 ID로 생성하면 `ID_CONFLICT`로 거부한다
- 예약 ID: `mode`(기본 제공 modifier). 다른 예약 ID는 `_`로 시작하며 사용자 생성에 쓸 수 없다

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
- 이동으로 순환이 생기면 `TREE_CYCLE`로 거부한다

### order (fractional index)

- base62 문자열 키다. 두 키 사이에 항상 새 키를 만들 수 있어, 동시에 삽입해도 다른 형제의 키가 바뀌지 않는다
- 알고리즘은 David Greenspan의 "Implementing Fractional Indexing"을 따른다(npm
  `fractional-indexing`과 같은 결과). 서버 구현도 같은 결과를 내야 하며 적합성 fixture로 검증한다
- 연산은 `order`를 직접 받지 않고 위치 지정(`first`, `last`, `{ before: id }`, `{ after: id }`)을
  받는다. 서버가 키를 계산한다. AI는 fractional index를 다루지 않는다

## 4. 값 형식

| 형식 | 예 | 비고 |
|---|---|---|
| Dimension | `{ "value": 16, "unit": "px" }` | unit: `px`, `rem`, `%`(스타일 원시값만) |
| Color | `{ "colorSpace": "oklch", "components": [0.62, 0.19, 259], "alpha": 1 }` | DTCG 2025.10 color 객체 |
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
- `container`: `div`, `ul`, `ol`, `li`, `figure`, `a`, `button`, `form`, `label`
- `text`: `p`, `h1`~`h6`, `span`, `strong`, `em`, `small`, `label`, `a`, `button`, `li`

### 레이아웃 (`frame`, `component`, `section`, `container`)

| 키 | 값 | 기본값 |
|---|---|---|
| `layout.mode` | `flex-row`, `flex-column`, `grid`, `absolute` | `flex-column` |
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
| `abs.x`, `abs.y` | number(px) | 부모가 `absolute` |
| `abs.h` | `left`, `right`, `left-right`, `center`, `scale` | 부모가 `absolute`. 기본 `left` |
| `abs.v` | `top`, `bottom`, `top-bottom`, `center`, `scale` | 부모가 `absolute`. 기본 `top` |

- 유효 조건을 벗어난 키는 지우지 않고 보존하며 변환기가 무시한다. 부모의 레이아웃 모드를
  바꿨다가 되돌려도 자식의 배치 정보가 남는다
- 자식 sizing의 기본값은 부모 방향의 주축이 `hug`, 교차축이 `fill`이다(정확한 CSS 대응은 변환 규칙 문서)

### 스타일

- 키는 `style.<CSS 속성 이름>`이다. 예: `style.background-color`, `style.padding-top`, `style.font-size`
- 허용 속성은 계약 파일의 스타일 허용 목록에 있는 것만이다(`STYLE_NOT_ALLOWED`). 레이아웃 모델을
  우회하는 속성(`display`, `position`, `flex-*`, `grid-*`, `width`, `height`, `top`, `left`, `float`,
  `margin*` 등)은 목록에 넣지 않는다. 값은 Baseline Widely available 허용 목록 안에 있어야 한다
- 값은 속성별 형식(Dimension, Color, 키워드) 또는 토큰 바인딩이다

### 종류별 고유 속성

| type | 키 | 값 |
|---|---|---|
| `frame` | `boardX`, `boardY` | 보드 좌표(px) |
| `frame` | `previewWidth`, `previewHeight` | 미리보기 뷰포트 크기. 출력에 영향 없음 |
| `frame` | `baseLabel` | base 구간의 표시 이름. 기본 `"Mobile"` |
| `frame` | `minWidth` | number(px). 기본 320 |
| `frame` | `safeArea` | boolean. safe area inset 처리 여부. 기본 `false` |
| `component` | `boardX`, `boardY` | 보드 좌표(px) |
| `text` | `content` | 문자열(서식 없는 텍스트) |
| `image` | `src`, `alt` | 자산, 문자열 |
| `image` | `style.object-fit` | `cover`, `contain`, `fill` |
| `instance` | `component` | 원본 `component` ID. 생성 후 변경 불가 |
| `instance` | `props.<componentProp ID>` | 선택한 옵션 값 |
| `instance` | `node.<원본 노드 ID>.<키>` | 인스턴스 override (아래 8절) |
| `breakpoint` | `minWidth` | number(px). 같은 Frame 안에서 유일, Frame `minWidth`보다 커야 함 |
| `breakpoint` | `name` | 표시 이름 |

## 6. BP와 override 키 문법

```
키        := 기본키 ( "@" 조건 )*
조건      := "bp:" BP_ID
           | "var:" componentProp_ID "=" 옵션값
           | "state:" ( "hover" | "pressed" | "focus" | "disabled" )
```

- 예: `layout.mode@bp:bp2`, `style.font-size@bp:bp2`, `style.background-color@var:cp1=danger`,
  `style.background-color@var:cp1=danger@state:hover`
- 조건은 종류마다 최대 1개이고 `bp → var → state` 순서로만 쓴다. 다른 순서는 `KEY_INVALID`로
  거부한다. 같은 의미의 키가 두 가지로 저장되는 일을 막아 결정성을 지킨다
- 조건 없는 키가 base 값이다. base 구간은 Frame의 가장 작은 BP보다 좁은 폭이며, mobile-first로
  BP의 `minWidth` 오름차순으로 덮어쓴다
- BP를 ID로 참조하므로 BP의 `minWidth`를 바꿔도 override 키는 그대로다. Frame 생성 시 BP 2개
  (768, 1280)를 함께 만들어 base까지 기본 3구간이 된다

### 조건별 허용 키

| 기본키 | `@bp` | `@var` | `@state` |
|---|---|---|---|
| `layout.*`, `size.*`, `grid.*`, `abs.*` | 허용 | 허용 | 불허 |
| `style.*` | 허용 | 허용 | 허용 |
| `hidden` | 허용 | 허용 | 불허 |
| `src` (image) | 허용 (`<picture>`로 출력) | 불허 | 불허 |
| `content`, `tag`, `name`, `parent`, `order` 등 구조·텍스트 | 불허 | 불허 | 불허 |

- `layout.mode`의 BP override는 `flex-row`, `flex-column`, `grid` 사이의 전환만 허용한다.
  `absolute`로 또는 `absolute`에서 바꾸는 override는 거부한다(`CONDITION_NOT_ALLOWED`).
  자식 배치 정보(좌표 대 순서)가 BP마다 달라지는 것을 막기 위해서다
- `@bp`의 BP는 그 노드가 속한 Frame의 것이어야 한다. 컴포넌트 원본 안의 노드는 `@bp`를 쓸 수
  없다(원본에는 Frame이 없다). 컴포넌트의 반응형 처리 방식은 미확정이다
- `@var`, `@state`는 컴포넌트 원본 안의 노드에만 쓸 수 있고, `var`의 속성은 그 컴포넌트의 것이어야 한다
- BP나 `componentProp`을 삭제하면 그것을 참조하는 override 키가 같은 트랜잭션 안에서 함께 삭제된다

## 7. 토큰과 modifier

### modifier

| 키 | 값 |
|---|---|
| `name` | 식별자. CSS `data-<name>` 속성 이름이 된다. 전역 유일 |
| `contexts` | 문자열 배열. 예: `["light", "dark"]` |
| `default` | `contexts` 중 하나 |

- 예약 modifier `mode`(`contexts: ["light", "dark"]`, `default: "light"`)는 항상 존재하고 삭제할 수 없다
- `contexts`는 배열 하나가 LWW 단위다. 두 사람이 동시에 컨텍스트를 추가하면 한쪽이 사라질 수 있다.
  빈도가 낮아 허용한다

### token

| 키 | 값 |
|---|---|
| `name` | 점 경로(`color.action.primary`). 전역 유일 |
| `tokenType` | DTCG 타입(`color`, `dimension`, `fontFamily`, `fontWeight`, `number`, `duration`, `shadow`, `typography` 등) |
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

## 8. 컴포넌트와 인스턴스

### componentProp

| 키 | 값 |
|---|---|
| `name` | 식별자. 출력 `data-<name>` 속성 이름 |
| `kind` | `enum`, `boolean` |
| `options` | `enum`일 때 옵션 값 배열(식별자). `boolean`은 `["true", "false"]`로 고정 |
| `default` | 옵션 값 하나 |
| `order` | 속성 정의 순서. 같은 노드·같은 키를 두 속성이 바꾸면 뒤의 것이 이긴다 |

### 인스턴스 override

- 키 형식: `node.<원본 노드 ID>.<기본키>`. 예: `node.n13.content`, `node.n20.src`,
  `node.n13.style.color`, `node.n21.hidden`
- 허용: `content`, `src`, `alt`, `hidden`, 그리고 원본 값이 토큰 바인딩인 `style.*`·
  `layout.gap`·`size.*`의 다른 토큰 바인딩. 조건(`@bp` 등)은 붙일 수 없다
- 구조 변경(자식 추가·삭제·이동)은 인스턴스 안에서 할 수 없다(`STRUCTURE_LOCKED`). 필요하면 `detach`한다
- 노드 ID가 모든 변형에서 같으므로, `props.*`를 바꿔도 `node.*` override가 유지된다
- 원본 노드가 삭제되면 그 노드를 가리키는 override 키는 무시되며, 다음 쓰기 때 서버가 정리한다

## 9. apply_ops

### 트랜잭션

```json
{
  "txId": "tx_9f2…",
  "actor": "user:dex",
  "ops": [
    { "op": "create", "id": "c1", "type": "container", "parent": "s1", "position": "last",
      "props": { "layout.mode": "flex-row", "layout.gap": { "token": "tk2" } } },
    { "op": "set", "id": "t1", "props": { "content": "요금 안내", "style.font-size@bp:bp2": { "token": "tk9" } } },
    { "op": "move", "id": "t1", "parent": "c1", "position": "first" }
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
| `create` | `id`, `type`, `parent`, `position`, `props` | 객체 생성. 노드가 아닌 객체는 `position`을 생략한다 |
| `set` | `id`, `props` | 속성 설정. 값 `null`은 삭제. 레이아웃, 스타일, 토큰 바인딩, 인스턴스 속성 변경이 모두 여기에 해당 |
| `move` | `id`, `parent`, `position` | 부모와 순서 변경 |
| `delete` | `id` | 객체와 하위 노드, 그리고 그것을 참조하는 조건 키를 삭제 |
| `detach` | `id` | 인스턴스를 일반 노드로 전환. 새 노드 ID 생성 규칙은 v0.6에서 정한다 |

`position`은 `"first"`, `"last"`, `{ "before": ID }`, `{ "after": ID }` 중 하나다.

### 응답

```json
{ "ok": true, "seq": 1042, "warnings": [{ "code": "TOKEN_DEPRECATED", "id": "t1", "key": "style.color" }] }
{ "ok": false, "error": { "code": "TREE_CYCLE", "opIndex": 2, "id": "c1", "key": null, "message": "…" } }
```

- `message`는 사람과 AI가 읽는 설명이며 계약에 포함하지 않는다. 판단은 `code`로 한다

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
| `TREE_CYCLE` | 이동으로 트리 순환 발생 |
| `KEY_INVALID` | 키 문법 오류, 조건 순서 오류 |
| `KEY_NOT_ALLOWED` | 그 객체 종류에 없는 키 |
| `CONDITION_NOT_ALLOWED` | 6절의 조건별 허용 키 위반 |
| `CONDITION_TARGET_MISSING` | 조건이 가리키는 BP·속성·옵션이 없거나 범위 밖 |
| `VALUE_INVALID` | 값 형식 또는 키워드 위반 |
| `STYLE_NOT_ALLOWED` | 스타일 허용 목록 밖의 CSS 속성 또는 값 |
| `TOKEN_TYPE_MISMATCH` | 바인딩·참조의 타입 불일치 |
| `TOKEN_CYCLE` | 토큰 참조 순환 |
| `TOKEN_IN_USE` | 참조 중인 토큰 삭제 |
| `NAME_CONFLICT` | 토큰·modifier·componentProp 이름 중복 |
| `STRUCTURE_LOCKED` | 인스턴스 내부 구조 변경, 예약 modifier 삭제 |

### 경고 (적용은 한다)

| 코드 | 조건 |
|---|---|
| `TOKEN_DEPRECATED` | `deprecated` 토큰을 바인딩 |
| `RAW_TOKEN_BOUND` | 원시값 토큰(참조가 아닌 토큰)을 노드에 직접 바인딩 |

오버플로·잘림 경고는 문서 검증이 아니라 렌더 결과의 검사이므로 `inspect`가 별도로 제공한다.

## 11. 이 문서의 미확정 사항

- 텍스트 인라인 서식: `content`를 서식 없는 문자열로 둘지, 서식 구간을 가진 구조로 바꿀지
- 자산(`asset`) 객체의 저장 방식과 속성
- 컴포넌트 원본의 반응형: 원본에 `@bp`를 둘 수 없으므로, 원본에 자체 BP를 둘지 컨테이너 쿼리를 쓸지
- 중첩 인스턴스(컴포넌트 안의 인스턴스)의 override 경로 표기
- `detach` 시 새 노드 ID 생성 규칙, enum 옵션 이름 변경 시 `@var` 키 일괄 갱신 방식
- grid 트랙 크기 지정(현재는 균등 열 수만), `margin` 허용 여부
