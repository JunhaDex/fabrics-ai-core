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
- 정렬은 단일 컬럼 3-state(asc→desc→none)다. 트리거는 `<th>` 안의 `<button>`이고, `aria-sort`와 함께 `aria-live="polite"` 안내 영역을 둔다. `aria-sort` 변경만으로는 대부분의 스크린 리더가 즉시 읽지 않는다
- 선택은 다중 체크박스만 지원하고, 헤더 전체선택 범위는 현재 페이지다. 행 클릭 선택은 넣지 않는다 — 행 안의 링크·버튼과 충돌한다
- 페이지네이션 UI는 prev/next + `x–y / z` + 페이지 크기 `Select`다. 페이지 번호 버튼은 말줄임 로직이 붙어 제외하고, `Pagination` 독립 export도 하지 않는다
- Table의 접근 가능한 이름(`caption`/`aria-label`)은 선택 prop이다. 이름이 있으면 가로 스크롤 래퍼에 `tabIndex={0}` + `role="region"`을 붙여 키보드 스크롤을 지원하고, 없으면 `role="region"`을 생략한다 — 이름 없는 region 자체가 axe 위반이기 때문이다
- 시각 variant는 컴포넌트당 1종으로 시작한다(Tabs underline, Accordion bordered). 표의 줄무늬·테두리는 prop으로 열지 않고 테마가 결정한다. prop으로 열면 brutalism·tactile-surface가 룩앤필을 뒤집을 수 없다
- Badge는 tone 6종(neutral/brand/success/warning/danger/info) × appearance(solid/subtle/outline) × size다. 토큰은 `<tone>`/`on-<tone>`/`<tone>-subtle`/`on-<tone>-subtle` 4키를 6톤에 균일하게 적용한 24키 매트릭스로 고정한다. 슬롯 이름과 `tv()` variant 키를 테마 간 동일하게 유지해, 테마를 추가할 때 같은 키 집합의 **값만 다시 선언**하면 되게 한다. outline은 테두리 `<tone>` + 텍스트 `on-<tone>-subtle`로 새 슬롯 없이 만든다
- 24키 매트릭스를 채우기 위한 신규 슬롯 10개: `neutral`, `on-neutral`, `neutral-subtle`, `on-neutral-subtle`, `brand-subtle`, `on-brand-subtle`, `on-success`, `on-warning`, `info`, `on-info`
- 표 전용 색 슬롯은 만들지 않는다. 헤더 면과 행 호버는 `surface-raised`, 선택 행은 `brand-subtle`/`on-brand-subtle`을 재사용한다. 신설하는 것은 셀 패딩 `sem.spacing.cell-x`/`cell-y`뿐이다 — 표는 컨트롤보다 촘촘하고 밀도는 테마 고정 대상이다
- Accordion은 `--radix-accordion-content-height` 기반 height 전환을 쓴다. `motion.css`에 `accordion-down`/`accordion-up` keyframes와 `--animate-*` 2개를 추가하고 지속 시간은 `--sem-duration-base`를 참조한다. 제목 레벨은 `headingLevel` prop으로 받는다 — Radix `Header` 기본값 `<h3>`이 페이지 제목 구조와 어긋날 수 있다
- Tabs는 `activationMode`를 prop으로 노출하고 기본값은 `automatic`(APG 기본)이다. 무거운 콘텐츠 탭에서 `manual`이 필요해진다. horizontal/vertical 모두 지원하고, 탭이 넘치면 가로 스크롤한다. `forceMount`는 노출하지 않는다
- Separator는 Radix props를 통과시키는 데서 멈춘다. 가운데 라벨이 들어가는 구분선은 마크업이 달라 별도 컴포넌트감이고, 간격은 `layoutClass()`가 이미 통과시키는 `className`의 margin에 위임한다

## 진행 중: v0.3 데이터 표시
- 컨텍스트(2026-09-29 착수): v0.2로 폼·피드백이 갖춰졌다. 데이터 표시 계층을 채워
  v0.5 테마 작업 전에 슬롯 부족을 드러낸다. 브랜치는 `feat/v0.3-components` 하나이며,
  새 컴포넌트 추가를 연속적인 변경으로 취급해 순차 커밋한다.
- 핵심 기능 (모두 완료되면 릴리스). DoD 3요건(스토리 + `addon-a11y` 통과 + Vitest
  상호작용 테스트)을 갖춘 뒤 체크한다:
  - [ ] Badge
  - [ ] Separator
  - [ ] Tabs
  - [ ] Accordion
  - [ ] Table (정적)
  - [ ] DataTable (정렬·선택·페이지네이션)
- 세부 step (한 사이클 = 한 커밋. 종료 게이트는 CI 순서 그대로
  `pnpm lint && pnpm build && pnpm format:check && pnpm typecheck && pnpm test`):
  - [ ] 의미 슬롯 12개 추가 — 색 10개 + `sem.spacing.cell-x`/`cell-y`. 슬롯마다
        `slots.json` + `themes/neutral/tokens/semantic/light.json` + `dark.json` 3파일 동시 갱신.
        `tokens.stories.tsx`에 스와치를 추가해 light/dark 대비(solid 4.5:1, outline 테두리 3:1) 확인
  - [ ] `motion.css`에 `accordion-down`/`accordion-up` keyframes +
        `--animate-accordion-down`/`-up` 추가
  - [ ] Separator — 가장 작은 컴포넌트로 빌드·테스트 경로를 먼저 뚫는다
  - [ ] Badge — 24키 매트릭스를 전부 소비하므로 슬롯 정합성이 여기서 드러난다
  - [ ] Tabs — `activationMode` 양쪽, horizontal/vertical, 넘침 시 가로 스크롤
  - [ ] Accordion — `type` 판별 유니온, `headingLevel`, height 전환,
        `prefers-reduced-motion`
  - [ ] Table — 접근 가능한 이름이 있는 경우와 없는 경우를 각각 스토리로 만들어
        `role="region"` 분기가 axe를 통과함을 증명한다
  - [ ] DataTable 정렬 — 3-state 순환, `aria-sort` 전이, `aria-live` 안내. 비제어·제어 스토리 2개
  - [ ] DataTable 선택 — 헤더 indeterminate, 현재 페이지 범위. **정렬 후 선택 유지**를
        `getRowId` 기준으로 테스트에 고정한다
  - [ ] DataTable 페이지네이션 — 페이지 크기 변경 시 현재 페이지 보정, 마지막 페이지
        경계, `loading`(Skeleton 행) + `emptyMessage`
  - [ ] 릴리스: changeset 작성 → PR squash merge(main에 커밋 하나) → 릴리스 PR 병합
- v0.3 범위 밖: 컬럼 필터, 그룹핑·집계, 가상화, 컬럼 리사이즈·순서 변경, sticky header,
  다중 컬럼 정렬, 단일 선택(라디오) 행, 모바일 카드 전환
- 다음 행동: `feat/v0.3-components` 브랜치 생성 완료. 의미 슬롯 12개 추가부터 시작한다

## 다음 버전 (계획)
- v0.4 레이아웃: Dialog(모달), Footer, TopNav, SideNav, Columns, BentoGrid
- v0.5 테마: brutalism, tactile-surface (v0.2~0.4 컴포넌트로 슬롯·스타일 레이어 검증)
- v0.6 fabrics 도메인 컴포넌트: 목록은 첫 소비 프로젝트 기획 시 확정

## 완료
- v0.2.0 (2026-09-28) 폼/피드백 컴포넌트: 폼 11종(Label, Input, Textarea, Field, Checkbox, RadioGroup, Switch, Select, Slider, Toggle, ToggleGroup)과 피드백 7종(Alert, Toast, Tooltip, Popover, Progress, Spinner, Skeleton)을 DoD 3요건으로 완성. 기반 레이어로 아이콘(`lucide` + `<Icon>`)과 모션 토큰을 추가하고, 의미 슬롯을 22 → 41개로 늘렸다. 도구 정비로 ESLint+Prettier 공통 설정(oxlint 제거), `a11y.test: 'error'` 승격, PR CI 워크플로를 도입했다. 테스트 6 → 81개
- v0.1.1 (2026-09-22) 패키지 README: 레지스트리 페이지용 README 3종 추가. 릴리스 워크플로를 `changesets/action@v2`로 전환해 패키지별 태그·GitHub Release 자동 생성 복구, 저장소 레벨 `vX.Y.Z` 태그 생성 step 추가
- v0.1.0 (2026-09-22) 최초 골격: 토큰→테마→코어→Storybook 파이프라인 연결. `packages/tokens`(DTCG primitives/semantic, `@theme` CSS 변수), `packages/core`(Button variant 4·size 3·`asChild`, `layoutClass`, tsdown), `themes/neutral`(light/dark 단일 번들), `apps/storybook`(`data-mode` 툴바). changesets → CHANGELOG → 태그 → GitHub Packages publish 파이프라인 검증 완료

## 미확정 사항
- 로컬 설치 검증(`npm view @junhadex/core`): `.zshrc`에 `GITHUB_TOKEN_PKG`(classic PAT, `read:packages`) 설정 후 확인 필요. 0.1.1 tarball에 README가 포함된 것은 `npm pack --dry-run`으로 확인함
- fabrics 도메인 컴포넌트 v1 목록 (첫 소비 프로젝트 기획 시)
- v0.3에서 제외한 표 기능(다중 컬럼 정렬, 단일 선택 행, sticky header, 모바일 카드 전환, 독립 `Pagination` export). 실제 요구가 생길 때 추가한다
- Calendar/DatePicker 설계 전반. 착수 조건은 실사용 프로젝트의 요구사항 확정(선택 모드(단일/범위/다중), 시간대 취급, 입력 포맷, 로캘, 주 시작일)
- `packages/tokens`·`themes/neutral`(빌드 스크립트 JS)을 린트 대상에 넣을지. 현재는 제외했고, 필요해지면 `@repo/eslint-config`에 base 설정을 추가한다
- `layoutClass()`를 거치지 않은 className 전달을 잡는 커스텀 ESLint 규칙. 컴포넌트가 쌓인 뒤 작성한다
- Field + RadioGroup 조합. Field는 `<label htmlFor>`를 쓰는데 radiogroup은 div라 레이블이 걸리지 않는다. 그룹 레이블은 `aria-labelledby`나 fieldset/legend가 필요하므로 Field에 그룹 모드를 넣을지 판단해야 한다
- Select의 옵션 그룹(optgroup) 지원과 Slider의 범위(2-thumb) 지원 여부. props 래핑 API의 경계이며, 실제 요구가 생길 때 추가한다
- Storybook 자체 호스트 위치와 시기
