# trama HTML/CSS 변환 규칙

trama 문서를 HTML/CSS로 바꾸는 규칙의 현행 명세다. 편집기(web)의 `src/render`가 이 규칙을
구현하고, 서버는 같은 구현을 헤드리스 Chromium에서 불러 쓴다(하나의 렌더 경로). 문서 구조와
속성 키는 `trama-document-model.md`가 정본이다. 요구사항은 `../references/fabrics-tala-requirements.md`의
"레이아웃 모델과 HTML 변환 규칙" 절이다.

- 상태: v0.2. base 구간만 다룬다. BP override, 토큰, 컴포넌트, 스타일 허용 목록은 해당 버전에서 추가한다
- 검증: web 저장소의 golden 테스트(`src/render/__golden__/`)가 이 문서의 출력 형식을 바이트 단위로 고정한다

## 1. 변환 단계

```
문서 ──build(doc, frameId)──▶ 중간 트리(Page) ──직렬화──▶ export | srcdoc | annotated
```

- Frame 하나가 HTML 문서 하나다
- 중간 트리는 요소 트리와 CSS 규칙 목록이다. 세 출력이 같은 중간 트리에서 나온다
- 변환은 순수 함수다. 같은 문서와 Frame ID는 항상 같은 바이트열을 만든다

## 2. 출력 3종

| 출력 | 용도 | 형태 | 요소 속성 |
|---|---|---|---|
| `export` | 내보내기 | HTML 문서 + `style.css` | `class` |
| `srcdoc` | 편집기 iframe | HTML 문서, CSS는 `<style>`로 인라인 | `class`, `data-id` |
| `annotated` | AI 읽기 | `<body>` 마크업만, CSS 없음 | `class`, `data-id`, `data-layout` |

- `data-id`는 노드 ID, `data-layout`은 레이아웃을 갖는 노드(frame, section, container)의 `layout.mode`다
- 속성 순서는 `class`, (image의 `src`, `alt`), `data-id`, `data-layout`이다

HTML 문서의 고정 골격:

```html
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{Frame name}</title>
{export: <link rel="stylesheet" href="style.css"> | srcdoc: <style>…</style>}
</head>
<body …>
…
</body>
</html>
```

- Frame의 `safeArea`가 `true`이면 viewport에 `, viewport-fit=cover`를 덧붙인다
- 파일은 개행(`\n`)으로 끝난다

## 3. 요소

| 노드 | 태그 | 내용 |
|---|---|---|
| frame | `body` | 자식 |
| section | `tag`, 기본 `section` | 자식 |
| container | `tag`, 기본 `div` | 자식 |
| text | `tag`, 기본 `p` | `content`(이스케이프) |
| image | `img` | 없음. `src`, `alt`는 없으면 빈 문자열 |

- 모든 요소는 `class="n-<노드 ID>"`를 가진다. 이름 변경은 출력에 영향을 주지 않는다
- 자식 순서는 형제 정렬 규칙(`(order, id)` 사전순)을 따른다
- 이스케이프: 텍스트는 `&`, `<`, `>`, 속성값은 여기에 `"`를 더한다
- 들여쓰기는 깊이당 공백 2칸이다. 자식이 없는 요소와 text는 한 줄로 닫는다. `img`는 닫지 않는다

## 4. CSS 규칙

### 형식과 순서
- 첫 규칙은 고정 리셋이다

  ```css
  *, ::before, ::after {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }
  ```

- 이후 노드마다 `.n-<ID>` 규칙 하나를 트리 전위 순회 순서로 낸다. 선언이 없는 노드는 규칙을 내지 않는다
- 규칙 안의 선언은 속성 이름의 코드 단위 사전순으로 정렬한다
- shorthand를 쓰지 않는다. 사전순 정렬에서 shorthand와 longhand의 적용 순서가 뒤집히는 일을 막기 위해서다
- 규칙 사이는 빈 줄 하나, 선언은 공백 2칸 들여쓰기에 `속성: 값;`이다
- 숫자는 JavaScript `String(n)` 표기이며 `-0`은 `0`으로 낸다. 길이는 `{값}{단위}`이고 0에도 단위를 붙인다
- 속성이 없는 것과 기본값은 같은 출력을 낸다. CSS 초기값과 같은 선언은 내지 않는다

### Frame (`body`)
- `min-width: {minWidth}px` (기본 320)
- `safeArea`가 `true`이면 `padding-top|right|bottom|left: env(safe-area-inset-*)`
- 레이아웃은 아래 컨테이너 규칙과 같다

### 레이아웃 (frame, section, container)

| 키 | flex-row / flex-column | grid |
|---|---|---|
| `layout.mode` | `display: flex`, `flex-direction: row\|column` | `display: grid` |
| `layout.columns` | — | `grid-template-columns: repeat(N, minmax(0, 1fr))` |
| `layout.gap` | `column-gap`, `row-gap` 둘 다 | 같음 |
| `layout.rowGap` | `row-gap`만 덮어씀 | 같음 |
| `layout.justify` | `justify-content`. `start`→`flex-start`, `end`→`flex-end`. 기본 `start`는 내지 않음 | 컨테이너에는 내지 않음(자식 규칙 참고) |
| `layout.align` | `align-items`. `start`→`flex-start`, `end`→`flex-end`. 기본 `stretch`는 내지 않음 | 컨테이너에는 내지 않음 |
| `layout.wrap` | `true`이면 `flex-wrap: wrap` | — |
| `layout.clip` | `true`이면 `overflow: hidden` | 같음 |

- 자식 중 `position: absolute`인 노드가 있으면 `position: relative`를 낸다. 노드 자신이 absolute이면 내지 않는다

### 자식 배치: 흐름 (`position`이 `static`)

flex 부모. 주축은 `flex-row`에서 폭, `flex-column`에서 높이다. 기본 sizing은 주축 `hug`, 교차축 `fill`이다.

| sizing | 주축 | 교차축 |
|---|---|---|
| `fill` | `flex-grow: 1`, `flex-basis: 0%`, `min-{width\|height}: 0`(해당 min 키가 없을 때) | 부모 `layout.align`이 `stretch`가 아니면 `align-self: stretch` |
| `hug` | 없음 | 부모 `layout.align`이 `stretch`이면 `align-self: flex-start` |
| 고정 | `{width\|height}: 값`, `flex-shrink: 0` | `{width\|height}: 값` |

grid 부모. 기본 sizing은 두 축 모두 `fill`(셀을 채움)이다.

| sizing | 폭 | 높이 |
|---|---|---|
| `fill` | 없음 | 없음 |
| `hug` | `justify-self: {부모 justify}` | `align-self: {부모 align}` |
| 고정 | `justify-self: {부모 justify}`, `width: 값` | `align-self: {부모 align}`, `height: 값` |

- 부모 값 대응: `start`, `center`, `end`, `baseline`은 그대로, `stretch`와 `space-*`는 `start`
- `grid.colStart`·`grid.rowStart` → `grid-{column|row}-start: N`, `grid.colSpan`·`grid.rowSpan` →
  `grid-{column|row}-end: span N`

공통: `size.minWidth|maxWidth|minHeight|maxHeight` → `min-width` 등 같은 이름의 속성.

### 자식 배치: 절대 (`position`이 `absolute`)
- `position: absolute`, `left: {x}px`, `top: {y}px`, `w`·`h`가 있으면 `width: {w}px`, `height: {h}px`.
  `x`, `y`가 없으면 0이다
- `size.*`, `grid.*`는 출력하지 않는다

### 그 밖의 속성
- `hidden`이 `true`이면 `display`를 `display: none`으로 바꾼다. 자식은 그대로 출력한다
- `style.<속성>` 키는 `<속성>: 값`으로 낸다. v0.2에서는 image의 `style.object-fit`만 있다
