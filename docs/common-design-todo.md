# common-design todo

저장소: https://github.com/JunhaDex/fabrics-design-system · 로컬: `projects/common-design/`
목적: 테마(빌드 시점)·모드(런타임) 2층위 스타일을 지원하는 fabrics 공통 디자인 시스템 (React, Radix, Tailwind v4, npm)

## 결정 사항
- 스택: TypeScript 6.x(7.x는 tsdown dts 미지원으로 보류), React 19, pnpm workspace + catalog, Turborepo, 통합 `radix-ui`, Tailwind v4 `@theme`, tailwind-variants v3, Style Dictionary v5(DTCG), tsdown, Storybook 10, Vitest, changesets
- 배포: GitHub Packages public(저장소 visibility 상속, 2026-09-22 private→public 변경), 스코프 `@junhadex` 확정(저장소 소유자와 일치). publish는 GitHub Actions + `changesets/action`으로 실행(`GITHUB_TOKEN` 인증, PAT 불필요). main에 changeset이 쌓이면 릴리스 PR이 자동 생성되고, 병합 시 publish·태그가 실행된다
- 구조: `packages/tokens`, `packages/core`, `themes/<name>`, `apps/storybook`
- 테마 = 룩앤필, 빌드 시점 선택, 토큰 + 선택적 스타일 레이어, 밀도 고정. v1: neutral, brutalism, tactile-surface
- 모드 = light/dark/corporate 등, `data-mode` 런타임 전환
- 플랫폼 변형은 반응형으로 대응. 벤토 그리드는 core 레이아웃 컴포넌트
- className 오버라이드는 레이아웃 속성만 허용
- 토큰 SSOT는 코드, Storybook으로 시각화, Figma는 추후
- 소비 프로젝트 계약: Tailwind v4 필수. `@import "tailwindcss"` + `@import "@junhadex/theme-<name>/theme.css"` + `@source "…/@junhadex/core/dist"`
- 컴포넌트 완료 기준(DoD): Storybook 스토리 + a11y 검사 통과(`addon-a11y` `test: 'error'`) + Vitest 상호작용 테스트. 세 가지 모두 갖춰야 체크한다
- 접근성 WCAG 2.2 AA, 브라우저 evergreen 최근 2개 메이저
- 버전 순서: 컴포넌트를 먼저 쌓고 추가 테마는 나중에 만든다(슬롯 부족을 한 번에 발견하기 위해)
- core 제외 대상: Card, Avatar(프로젝트별로 정의할 가능성이 높음). fabrics 도메인 컴포넌트 목록은 첫 소비 프로젝트 기획 시 정의
- Calendar/DatePicker: 실사용 요구사항이 나올 때까지 구현을 연기한다(2026-09-22). 첫 소비 프로젝트에서 요구사항을 구체화한 뒤 다시 디자인한다. `react-day-picker` 의존 결정은 철회
- Storybook: 로컬 `storybook dev` 실행을 기준으로 한다. 자체 호스트 예정(시기 미정). Chromatic 애드온은 제거함
- 저장소 레벨 버전 = `@junhadex/core`의 버전. 세 패키지가 lockstep으로 움직인다는 전제이며, 워크플로가 이 값으로 `vX.Y.Z` 태그를 만든다
- 릴리스 워크플로: `changesets/action@v2` 필수. v1은 `@changesets/cli` v3의 publish 출력을 파싱하지 못해 태그 push와 GitHub Release 생성을 건너뛴다. v2는 입력 이름이 `version-script`/`publish-script`이고 `github-token`을 입력으로 받는다
- 변경 이력: changesets가 `CHANGELOG.md`를 생성. feature 단위 PR + squash merge (`docs/ssot/repo-architecture.md` "버전·변경 이력")
- 컴포넌트 API: props 래핑 단일 컴포넌트로 통일한다. Radix 다중 파트 프리미티브도 `<Select value onValueChange options={[…]} />` 형태로 감싸고, 컴파운드 파트(`Select.Root/Trigger/…`)는 노출하지 않는다
- 아이콘: `lucide` 코어 패키지를 의존한다(프레임워크 무관 데이터, deps 0, `sideEffects: false`, 아이콘 3,696개 개별 모듈). core가 `<Icon node={…} />` 렌더러를 export하고, 컴포넌트의 `icon` prop 타입은 `ReactNode`로 커스텀 SVG도 받는다. `lucide-react`는 쓰지 않는다 — React 종속을 렌더러 한 겹에 가두어 향후 다른 프레임워크 포트에서 아이콘 레이어를 재사용한다
- 모션 토큰화: `sem.duration.*`, `sem.ease.*` 슬롯을 둔다. 테마가 모션을 교체할 수 있어야 한다(v0.5 brutalism 무모션). Tailwind v4는 `--ease-*`·`--animate-*` 네임스페이스만 제공하므로 `duration-*` 유틸은 브리지 CSS에 `@utility`로 직접 추가한다
- 토큰 슬롯 확장 방식: 선행 일괄 정의가 아니라 컴포넌트 작업 중 필요할 때 추가한다. 슬롯 하나 추가 = `packages/tokens/tokens/semantic/slots.json` + `themes/neutral/tokens/semantic/light.json` + `dark.json` 3파일 동시 갱신
- 린트/포맷: ESLint 10 flat config + Prettier 3. oxlint는 제거했다. 설정은 내부 공유 패키지 `packages/eslint-config`(`@repo/eslint-config`, 비배포)가 `./react`·`./storybook` 2종을 export하고, 대상은 `packages/core`와 `apps/storybook`이다. 실행 시간을 위해 type-aware 규칙은 쓰지 않으며(필요해지면 `recommendedTypeChecked` + `projectService` 추가), turbo `lint`는 `^lint`에만 의존해 의존 패키지 빌드를 기다리지 않는다. Prettier는 `prettier-plugin-tailwindcss`로 `tv()` 내부까지 클래스를 정렬하고(Tailwind v4는 `tailwindStylesheet` 필수), Markdown은 표 정렬이 한글 폭을 잘못 계산해 제외한다
- `pnpm format`/`format:check`는 빌드 산출물에 의존한다. prettier-plugin-tailwindcss가 `tailwindStylesheet`를 따라가다 `@junhadex/theme-neutral/theme.css`(토큰 빌드 산출물)를 만나기 때문이다. 깨끗한 체크아웃에서는 `pnpm build`를 먼저 돌려야 한다 — CI도 build → format:check 순이다
- 톤 색은 솔리드(`danger`)와 은은한 면(`danger-subtle` + `on-danger-subtle`)을 나눠 둔다. 솔리드를 subtle 면 위에 얹으면 대비가 모자라기 때문이다. 새 톤을 추가할 때도 두 쌍을 함께 만든다
- Portal을 쓰는 컴포넌트의 스토리는 오버레이를 닫고 exit 애니메이션이 끝날 때까지 기다린 뒤 play를 끝낸다. 열린 채로 두면 Radix가 형제 요소에 걸어 둔 `aria-hidden` 때문에 axe의 `aria-hidden-focus`에 걸린다
- 체크박스·스위치처럼 레이블이 컨트롤 오른쪽에 오는 컨트롤은 자체 `label` prop을 갖는다. Field는 세로(레이블 위) 레이아웃이라 맞지 않으며, Field 안에서 쓸 때는 `label`을 생략하고 Field의 레이블에 연결한다
- 폼 컨트롤의 오류 상태는 별도 prop 없이 `aria-invalid` 하나를 근거로 삼는다. `tv()`에서 `aria-invalid:` 변형으로 스타일을 걸면 단독 사용과 Field 경유가 같은 경로를 탄다
- Tailwind 클래스는 소스에 **완성된 문자열**로 적는다. `` `duration-${d}` `` 처럼 동적으로 조합하면 스캐너가 감지하지 못해 유틸리티가 생성되지 않는다. 컴포넌트의 `tv()` 정의와 스토리 모두 리터럴로 쓴다
- catalog의 `typescript`는 `~6.0.0`으로 고정한다. typescript-eslint의 peer 범위가 `>=4.8.4 <6.1.0`이라 6.1이 나오면 벗어난다
- Toast: Radix Toast 프리미티브 + 자체 명령형 API(`toast.success(…)` + `<ToastProvider>`)로 구현한다. sonner를 쓰지 않는 이유는 (1) Toast는 Radix에 이미 있고 "Radix에 없는 것만 외부로 채운다"는 기준에 걸리며 (2) sonner가 컨테이너 위치·스택·모션 CSS를 소유해 테마 교체와 충돌하고 (3) shadcn이 Radix toast를 deprecate한 근거(큐 관리 보일러플레이트를 사용자 저장소에 떠넘기는 문제)가 라이브러리 저자에게는 해당하지 않기 때문. Radix Toast는 상류에서 deprecate되지 않았다(2026-09-22 공식 문서 확인)
- v0.3 컴포넌트 API는 모두 데이터 주도다. Table/DataTable은 `columns`/`rows`, Tabs/Accordion은 `items` 배열을 받는다. 컴파운드 파트는 노출하지 않는다
- Table과 DataTable을 나눈다. Table은 프레젠테이션 전용(`tv()` slots + 마크업), DataTable은 Table을 감싸 상태를 붙인 래퍼다. 스타일 정의는 한 곳이고, 정적 표 사용처가 상태 코드를 짊어지지 않는다
- 표 시맨틱은 `<table>` + `<th scope="col">`이다. `role="grid"`는 쓰지 않는다 — 2D 방향키 내비게이션 계약까지 떠안게 된다
- DataTable 엔진은 직접 구현한다. TanStack Table(v9.2.4 stable, 2026-08-04)을 쓰지 않는 이유는 (1) 범위인 단일 컬럼 정렬·페이지 단위 선택·페이지네이션이 `useState` + `useMemo`로 끝나고 (2) 필터·그룹핑·가상화는 **서버의 영역**이어서 API 쿼리 인자로 넘기므로 클라이언트 엔진이 필요 없고 (3) `@tanstack/react-store`라는 두 번째 상태 런타임을 디자인 시스템에 들이지 않기 위해서다
- DataTable 상태는 기존 컨트롤과 같은 제어/비제어 양쪽 패턴(`sort`/`defaultSort`/`onSortChange`, `page`/`onPageChange`)을 쓴다. 제어형이 서버 사이드 정렬·페이징의 연결점이다. 행 식별은 `getRowId` 필수 prop으로 받는다 — index 폴백은 정렬 후 선택이 어긋난다
- 정렬 비교는 열마다 `sortValue?: (row) => string | number` 로 받고, **이 함수의 존재가
  정렬 가능 여부**다(`sortable` 플래그를 따로 두지 않는다 — 플래그만 있고 비교값이 없는
  잘못된 조합을 타입에서 없앤다). `cell` 은 `ReactNode` 를 돌려주므로 비교에 쓸 수 없다.
  문자열 비교는 라이브러리가 `localeCompare` 로 한 곳에서 책임진다 — 소비 프로젝트가
  `a > b` 를 쓰면 한글·대소문자 혼용에서 틀린 순서가 나온다. 스칼라로 표현할 수 없는
  열(날짜 객체, nulls-last, 다중 키)이 나오면 그때 `compare?: (a, b) => number` 를
  비파괴적으로 추가한다
- 열 정의를 `value` 접근자 하나로 통일해 정렬·필터·내보내기가 공유하는 설계는 택하지
  않았다. 필터·그룹핑은 서버의 영역으로 이미 결정했으므로 재사용 상대가 오지 않고,
  `value`/`cell` 두 렌더 경로와 "둘 중 하나는 반드시 있어야 한다"는 불변식만 남는다
- 현재 정렬 상태는 `TableColumn.ariaSort`(`'none' | 'ascending' | 'descending'`)로
  Table 이 `<th>` 에 싣는다. `headerProps` 범용 통과 경로는 쓰지 않는다 — 그것이
  서비스할 기능(열 리사이즈·순서, sticky header, 다중 정렬, 열 그룹)이 전부 v0.3 범위
  밖이고, `headerProps.className` 이 className 정책을 우회하는 구멍이 된다. v0.4 에서
  sticky header 가 들어오면 타입을 넓히는 방향으로 승격한다
- 제어 판정은 `sort !== undefined` 다. `null` 이 "정렬 없음" 이라는 유효한 제어값이므로
  `!= null` 로 판정하면 제어형이 깨진다
- 정렬은 단일 컬럼 3-state(asc→desc→none)다. 트리거는 `<th>` 안의 `<button>`이고, `aria-sort`와 함께 `aria-live="polite"` 안내 영역을 둔다. `aria-sort` 변경만으로는 대부분의 스크린 리더가 즉시 읽지 않는다
- 선택은 다중 체크박스만 지원하고, 헤더 전체선택 범위는 현재 페이지다. 행 클릭 선택은 넣지 않는다 — 행 안의 링크·버튼과 충돌한다
- **`<tr>` 에 `aria-selected` 를 쓸 수 없다.** `role="grid"`/`treegrid` 안의 row 에만 허용되는
  속성이라 일반 표에서는 axe `aria-allowed-attr` 위반이다. 선택 상태의 전달은 행 체크박스의
  checked 가 담당하고, 행 틴트는 순수 시각 표현(`data-selected` + `brand-subtle`)이다
- 선택은 `selectable` 명시 스위치로 켠다. "선택 prop 이 하나라도 있으면 켜짐" 이라는 암묵
  규칙은 `selectedIds` 만 넘기고 스위치를 깜빡한 경우가 조용히 무시된다
- 행 체크박스의 접근 가능한 이름은 `getRowLabel`(기본값 `getRowId`)로 만든다. id 가 UUID 인
  프로젝트에서는 id 를 그대로 읽어 주면 스크린 리더에 쓸모가 없다
- 선택 열은 예약 키 `'__select'` 로 DataTable 이 맨 앞에 끼워 넣는다. Table 은 선택 열의
  존재를 모른다. 스토리에서 열 위치를 index 로 집으면 선택 열 때문에 밀리므로, 헤더
  텍스트로 열을 찾는다
- 페이지네이션 UI는 prev/next + `x–y / z` + 페이지 크기 `Select`다. 페이지 번호 버튼은 말줄임 로직이 붙어 제외하고, `Pagination` 독립 export도 하지 않는다. `<nav aria-label="페이지 이동">` 으로 감싸고 범위 텍스트에 `aria-live="polite"` 를 둔다
- 페이지 번호는 1-based 다. 표시가 `1–2 / 5` 인데 prop 만 0-based 면 혼란이 크다
- 페이지 보정은 **파생값 clamp**(`Math.min(page, lastPage)`)다. 핸들러에서 보정하지 않는
  이유는 (1) 페이지 크기 변경뿐 아니라 `rows` 가 바깥에서 줄어도 범위를 벗어나므로 한
  규칙으로 둘 다 막고 (2) 렌더 중에 `onPageChange` 를 부르는 것은 부작용이기 때문이다.
  제어형에서는 표시만 보정하고 부모의 `page` 값은 그대로 둔다. clamp 를 빼면 범위
  텍스트가 `21–5 / 5` 같은 값이 된다(변이 테스트로 확인)
- Table 의 `loading` 은 Skeleton 행 **3개 고정**이고 `<table aria-busy>` 가 된다. 행 수를
  prop 으로 열지 않는다. `emptyMessage` 는 `colSpan` 셀 하나로 그리므로 열 수를 아는
  Table 이 가진다
- 선택 열이 켜지면 `loading`/`emptyMessage`/`caption` 은 DataTable 이 따로 선언하지 않고
  `TableProps` 상속 + spread 로 Table 에 흘러간다
- Table의 접근 가능한 이름(`caption`/`aria-label`)은 선택 prop이다. 이름이 있으면 가로 스크롤 래퍼에 `role="region"`을 붙이고, 없으면 생략한다. `tabIndex={0}`은 **이름과 무관하게 항상** 붙인다 (아래 측정 결과 참고)
- `<caption>`은 테이블의 이름이지 스크롤 래퍼의 이름이 아니다. `caption`만 준 경우 래퍼
  region 은 `useId()` 로 만든 `aria-labelledby` 로 caption 을 가리켜야 이름을 갖는다
- Table 셀은 `whitespace-nowrap` 이다. 줄바꿈을 허용하면 `w-full` 표가 컨테이너에 맞춰
  줄어들어 가로 스크롤이 발생하지 않고, 스크롤 래퍼와 `role="region"` 분기 전체가
  무의미해진다 (288px 컨테이너에서 `scrollWidth === clientWidth` 로 확인)
- axe 측정 결과(axe-core 4.13, 넘치는 표 기준): `tabIndex` 를 빼면 **위반**
  (`scrollable-region-focusable`, "Scrollable region must have keyboard access")이므로
  이름 없는 경우에도 `tabIndex={0}` 이 필요하다. 반면 이름 없는 `role="region"` 은 axe 가
  **잡지 않는다** — region 생략은 ARIA 규범(이름 없는 region 은 랜드마크로 노출되지 않음)에
  근거한 선택이며, 그 동작은 우리 테스트(`queryByRole('region')` 가 null)가 고정한다
- 시각 variant는 컴포넌트당 1종으로 시작한다(Tabs underline, Accordion bordered). 표의 줄무늬·테두리는 prop으로 열지 않고 테마가 결정한다. prop으로 열면 brutalism·tactile-surface가 룩앤필을 뒤집을 수 없다
- Badge는 tone 6종(neutral/brand/success/warning/danger/info) × appearance(solid/subtle/outline) × size다. 토큰은 `<tone>`/`on-<tone>`/`<tone>-subtle`/`on-<tone>-subtle` 4키를 6톤에 균일하게 적용한 24키 매트릭스로 고정한다. 슬롯 이름과 `tv()` variant 키를 테마 간 동일하게 유지해, 테마를 추가할 때 같은 키 집합의 **값만 다시 선언**하면 되게 한다. outline은 테두리 `<tone>` + 텍스트 `on-<tone>-subtle`로 새 슬롯 없이 만든다
- 24키 매트릭스를 채우기 위한 신규 슬롯 10개: `neutral`, `on-neutral`, `neutral-subtle`, `on-neutral-subtle`, `brand-subtle`, `on-brand-subtle`, `on-success`, `on-warning`, `info`, `on-info`
- 표 전용 색 슬롯은 만들지 않는다. 헤더 면과 행 호버는 `surface-raised`, 선택 행은 `brand-subtle`/`on-brand-subtle`을 재사용한다. 신설하는 것은 셀 패딩 `sem.spacing.cell-x`/`cell-y`뿐이다 — 표는 컨트롤보다 촘촘하고 밀도는 테마 고정 대상이다
- Accordion은 `--radix-accordion-content-height` 기반 height 전환을 쓴다. `motion.css`에 `accordion-down`/`accordion-up` keyframes와 `--animate-*` 2개를 추가하고 지속 시간은 `--sem-duration-base`를 참조한다. 제목 레벨은 `headingLevel` prop으로 받는다 — Radix `Header` 기본값 `<h3>`이 페이지 제목 구조와 어긋날 수 있다
- Tabs는 `activationMode`를 prop으로 노출하고 기본값은 `automatic`(APG 기본)이다. 무거운 콘텐츠 탭에서 `manual`이 필요해진다. horizontal/vertical 모두 지원하고, 탭이 넘치면 가로 스크롤한다. `forceMount`는 노출하지 않는다
- Separator는 Radix props를 통과시키는 데서 멈춘다. 가운데 라벨이 들어가는 구분선은 마크업이 달라 별도 컴포넌트감이고, 간격은 `layoutClass()`가 이미 통과시키는 `className`의 margin에 위임한다
- Radix Accordion 은 Content 파트의 **인라인 스타일**로
  `--radix-accordion-content-height: var(--radix-collapsible-content-height)` 를 선언한다
  (`@radix-ui/react-accordion@1.2.20` dist 확인). 변수가 Content 요소에만 있으므로
  height keyframes 도 Content 에 직접 걸어야 하고, 자식 래퍼에 걸면 해석되지 않는다
- 24키 매트릭스에 대비 기준(solid·subtle 텍스트 4.5:1, outline 테두리 3:1)을 적용하면서
  기존 값 4개를 바꿨다. light `success` green.600→green.700(흰 글자 3.30→5.02),
  light `warning` amber.500→amber.600(테두리 2.15→3.19), dark `on-brand`·`on-danger`
  white→gray.950(3.68·3.76→5.41·5.29). 어두운 면 위에서는 밝은 톤 + 어두운 on-color가
  대비를 만드는 유일한 조합이다. `warning`은 두 모드 모두 `on-warning`이 gray.950이다
- Tailwind v4 `@theme inline` 로 선언한 변수는 런타임 CSS에 **출력되지 않는다**. 브리지가
  만드는 `--color-<슬롯>` 은 유틸리티 안에서 `var(--sem-color-<슬롯>)` 로 인라인될 뿐이므로,
  스토리에서 `var(--color-brand)` 를 직접 참조하면 값이 비어 투명하게 렌더된다. 스와치는
  유틸리티 클래스(`bg-brand text-on-brand`)를 쓰거나 원본 `var(--sem-color-*)` 를 참조한다
- Tailwind `@theme` 의 `--animate-*` 는 해당 유틸리티를 쓰는 소스가 없으면 CSS 에
  출력되지 않는다. 컴포넌트보다 토큰을 먼저 추가하는 사이클에서는 스토리가 그 클래스를
  한 번 써 줘야 산출물에 남고 검증도 가능하다
- Radix prop 이 동시에 `tv()` variant 키인 컴포넌트(Separator 의 `orientation`)는
  `VariantProps` 를 상속하지 않는다. 같은 이름이 두 경로로 들어와 타입이 충돌하므로
  Radix 의 prop 타입을 그대로 variant 키로 쓴다
- `layoutClass()` 계약을 고정하는 테스트를 Separator 스토리에 뒀다. `className` 에
  `my-8 bg-danger` 를 넘기면 `my-8` 만 남는다. 우회하면 tailwind-merge 가 `bg-border` 를
  밀어내고 룩앤필이 뚫린다는 것을 변이 테스트로 확인했다
- Badge 의 밀도(padding)는 토큰이 아니라 고정 유틸리티(`px-1.5 py-0.5` / `px-2 py-0.5`)다.
  배지 전용 밀도 슬롯은 두지 않았으므로 테마가 바꿀 수 없다. 모양은 `sem.radius.control`
  을 따르므로(알약 고정이 아니다) brutalism 이 각진 배지를 만들 수 있다. size 는 sm/md
  2종이다 — `text-lg` 배지는 쓸 자리가 없어 lg 는 요구가 생길 때 추가한다
- 유틸리티 클래스가 의도한 슬롯으로 해석되는지 보려면, 같은 슬롯을 인라인
  `var(--sem-color-*)` 로 참조하는 `hidden` 요소를 옆에 두고 계산색을 비교한다.
  `hidden`(display:none) 요소도 계산색은 읽힌다. 다만 neutral 테마에서 `brand` 와 `info`
  가 같은 blue.600 이므로 이 둘을 서로 바꾼 오타는 이 검사로 잡히지 않는다
- Radix Tabs 의 `activationMode="manual"` 에서 선택을 일으키는 것은 Enter/Space 와
  mousedown 이다. `automatic` 은 Trigger 의 `onFocus` 에서 선택한다. List 는 vertical·
  horizontal 양쪽 모두 `aria-orientation` 을 명시하고, Content 는 `tabIndex={0}` 이라
  패널 자체가 포커스를 받는다(그래서 content 슬롯에 focus-visible 링을 둔다)
- 탭 넘침은 리스트의 `overflow-x-auto` 로 처리한다. 스크롤 영역 안에 포커스 가능한
  트리거가 있으므로 axe 의 `scrollable-region-focusable` 을 위해 `tabIndex` 를 더할
  필요가 없다
- `--animate-*` 안의 `var()` 는 그 변수가 **선언된 요소**(`:root`)에서 치환된다. 따라서
  모션 슬롯을 하위 요소에서 덮어써도 애니메이션 길이는 바뀌지 않는다 — 테마는 모션을
  서브트리 단위로 바꿀 수 없다. `reduced-motion.css` 가 통하는 이유도 그것이 같은
  `:root` 를 덮기 때문이다(미디어 쿼리 블록이 unlayered 로 테마 선언보다 뒤에 온다).
  reduced-motion 테스트는 미디어 쿼리를 에뮬레이션하지 않고 `:root` 에 같은 덮어쓰기를
  직접 넣어 확인한다
- Accordion 은 `type` 에 기본값을 주지 않는다. 기본값을 주면 판별 유니온이 무너져
  `onValueChange` 의 인자가 `string | string[]` 로 뭉개진다. `type="single"` 의
  `collapsible` 기본값은 `false` 이므로(열린 항목을 닫을 수 없다) 대개 함께 넘겨야 한다
- Radix Accordion Header 는 `Primitive.h3` 고정이다. `headingLevel` 은 `asChild` 로
  요소를 갈아끼워 구현하고 2~6만 허용한다(h1 은 페이지 제목 자리다). height 전환
  애니메이션은 Content 에, 패딩은 그 안쪽 `body` 에 둔다 — Content 에 패딩을 두면
  전환이 패딩만큼 튄다
- Radix Collapsible 은 **마운트 직후 한 프레임 동안** 애니메이션을 억제한다
  (`isMountAnimationPrevented` 가 rAF 에서 풀린다). 열림 전환을 검증하는 테스트는 클릭
  전에 프레임을 넘겨야 하고, 그러지 않으면 `animationName` 이 `none` 으로 읽혀 간헐적으로
  실패한다. 실제 사용자는 한 프레임 안에 클릭할 수 없어 제품 동작과는 무관하다

## 다음 버전 (계획)
- v0.4 레이아웃: Dialog(모달), Footer, TopNav, SideNav, Columns, BentoGrid
- v0.5 테마: brutalism, tactile-surface (v0.2~0.4 컴포넌트로 슬롯·스타일 레이어 검증)
- v0.6 fabrics 도메인 컴포넌트: 목록은 첫 소비 프로젝트 기획 시 확정

## 완료
- v0.3.0 (2026-10-05) 데이터 표시 컴포넌트: Badge, Separator, Tabs, Accordion, Table, DataTable(단일 열 정렬·다중 선택·클라이언트 페이지네이션)을 DoD 3요건으로 완성. 톤 매트릭스(6톤 × solid/subtle/outline)와 셀 패딩 슬롯으로 의미 슬롯 41 → 53개, 대비 기준(텍스트 4.5:1·테두리 3:1) 적용으로 기존 테마 값 4개 변경(dark Button primary·danger 글자색 반전). 테스트 81 → 118개
- v0.2.0 (2026-09-28) 폼/피드백 컴포넌트: 폼 11종(Label, Input, Textarea, Field, Checkbox, RadioGroup, Switch, Select, Slider, Toggle, ToggleGroup)과 피드백 7종(Alert, Toast, Tooltip, Popover, Progress, Spinner, Skeleton)을 DoD 3요건으로 완성. 기반 레이어로 아이콘(`lucide` + `<Icon>`)과 모션 토큰을 추가하고, 의미 슬롯을 22 → 41개로 늘렸다. 도구 정비로 ESLint+Prettier 공통 설정(oxlint 제거), `a11y.test: 'error'` 승격, PR CI 워크플로를 도입했다. 테스트 6 → 81개
- v0.1.1 (2026-09-22) 패키지 README: 레지스트리 페이지용 README 3종 추가. 릴리스 워크플로를 `changesets/action@v2`로 전환해 패키지별 태그·GitHub Release 자동 생성 복구, 저장소 레벨 `vX.Y.Z` 태그 생성 step 추가
- v0.1.0 (2026-09-22) 최초 골격: 토큰→테마→코어→Storybook 파이프라인 연결. `packages/tokens`(DTCG primitives/semantic, `@theme` CSS 변수), `packages/core`(Button variant 4·size 3·`asChild`, `layoutClass`, tsdown), `themes/neutral`(light/dark 단일 번들), `apps/storybook`(`data-mode` 툴바). changesets → CHANGELOG → 태그 → GitHub Packages publish 파이프라인 검증 완료

## 미확정 사항
- **`@junhadex/core`가 `tailwind-merge`를 의존성으로 선언하지 않는다** (stylist-web에서 발견, 2026-10-06). `tailwind-variants`는 이를 선택적 peer로 두므로, 소비 프로젝트에 설치되지 않으면 className conflict resolution이 꺼진다. `layoutClass()` 변이 테스트는 이 동작을 전제한다. core의 dependencies에 선언하는 방향으로 이 세션에서 처리한다
- 로컬 설치 검증(`npm view @junhadex/core`): `.zshrc`에 `GITHUB_TOKEN_PKG`(classic PAT, `read:packages`) 설정 후 확인 필요. 0.1.1 tarball에 README가 포함된 것은 `npm pack --dry-run`으로 확인함
- fabrics 도메인 컴포넌트 v1 목록 (첫 소비 프로젝트 기획 시)
- v0.3에서 제외한 표 기능(다중 컬럼 정렬, 단일 선택 행, sticky header, 모바일 카드 전환, 독립 `Pagination` export). 실제 요구가 생길 때 추가한다
- **서버 사이드 페이징·정렬은 v0.3에서 동작하지 않는다.** 페이지네이션은 클라이언트
  사이드 전용이다 — `rows` 전체를 받아 잘라 쓰므로, 서버가 이미 잘라 준 한 페이지를
  넘기면 다시 잘려 빈 표가 된다. 서버 페이징에는 `totalRows`(또는 `manualPagination`)
  prop 이 필요하다. 정렬도 같은 성질이 약하게 있다: 제어형이어도 DataTable 이
  `sortValue` 로 다시 로컬 정렬하므로, 서버가 다른 기준(다중 키·다른 콜레이션)으로
  정렬했다면 그 순서를 덮는다. `page`/`sort` 제어 자체는 URL 동기화 용도로 유효하다.
  첫 소비 프로젝트가 서버 페이징을 요구할 때 함께 설계한다
- Calendar/DatePicker 설계 전반. 착수 조건은 실사용 프로젝트의 요구사항 확정(선택 모드(단일/범위/다중), 시간대 취급, 입력 포맷, 로캘, 주 시작일)
- `packages/tokens`·`themes/neutral`(빌드 스크립트 JS)을 린트 대상에 넣을지. 현재는 제외했고, 필요해지면 `@repo/eslint-config`에 base 설정을 추가한다
- `layoutClass()`를 거치지 않은 className 전달을 잡는 커스텀 ESLint 규칙. 컴포넌트가 쌓인 뒤 작성한다
- Field + RadioGroup 조합. Field는 `<label htmlFor>`를 쓰는데 radiogroup은 div라 레이블이 걸리지 않는다. 그룹 레이블은 `aria-labelledby`나 fieldset/legend가 필요하므로 Field에 그룹 모드를 넣을지 판단해야 한다
- Select의 옵션 그룹(optgroup) 지원과 Slider의 범위(2-thumb) 지원 여부. props 래핑 API의 경계이며, 실제 요구가 생길 때 추가한다
- Storybook 자체 호스트 위치와 시기
