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

## 진행 중: v0.2 폼/피드백
- 컨텍스트: DoD를 적용하는 첫 버전. 컴포넌트 18개를 쌓아 v0.5의 추가 테마가 검증할 슬롯 표면을 만든다. Calendar/DatePicker는 제외되어 외부 의존 0을 유지한다
- 핵심 기능 (모두 완료되면 릴리스):
  - [x] 선행 인프라 4건 (DoD를 실제로 강제할 수 있는 상태 만들기)
  - [x] 기반 레이어 2건 (아이콘, 모션 토큰)
  - [x] 폼 11종
  - [x] 피드백 7종
- 세부 step:
  - 선행 인프라
    - [x] ESLint + Prettier 공통 설정 도입, oxlint 제거 (`packages/eslint-config`). 린트 대상이 `apps/storybook` 한 곳에서 `core`까지 넓어졌고 포매터가 처음 생겼다
    - [x] `a11y.test`를 `'todo'` → `'error'`로 전환. 기존 스토리는 수정 없이 통과했고, axe가 실제로 게이트 역할을 하는지 의도적 위반(image-alt)으로 확인했다
    - [x] Button에 `play` 상호작용 테스트 추가. Primary(클릭→onClick 1회)와 Disabled 스토리 신설(강제 클릭으로 핸들러 미호출 검증). Button이 DoD 3요건을 모두 충족하는 첫 컴포넌트가 되었다
    - [x] PR CI 워크플로 신설(`.github/workflows/ci.yml`). format/lint/typecheck/build/test를 PR에서만 돌린다(main은 squash merge 결과라 중복). playwright 설치는 `--filter fabrics-storybook`로 실행해야 한다 — pnpm strict 레이아웃에서 루트는 resolve하지 못한다
    - [x] Storybook decorator Portal 대응. 면·전경색을 래퍼 div가 아니라 `index.css`의 `body`에 건다
  - 기반 레이어
    - [x] 아이콘: `lucide` catalog 추가, `<Icon node size />` 렌더러 구현·export. 기본 크기는 `1em`(주변 글자 크기를 따라가므로 별도 크기 토큰이 불필요). `aria-label`이 없으면 `aria-hidden`, 있으면 `role="img"`
    - [x] 모션: 원시 `primitives/motion.json` + 의미 슬롯 `sem.duration.*`·`sem.ease.*`. 브리지가 duration 슬롯에 한해 `@utility`를 출력하도록 확장, `src/motion.css`에 enter/exit `@keyframes` + `--animate-*`, `dist/reduced-motion.css`로 `prefers-reduced-motion` 처리(테마 값보다 뒤에 병합해야 이긴다)
  - 폼 11종
    - [x] Label(Radix Label.Root), Input(size 3종), Textarea(`tv({ extend: input })`)
    - [x] Field — `useId`로 컨트롤 id를 만들어 레이블과 잇고, 설명/오류를 `aria-describedby`로 묶는다. `cloneElement`로 children에 주입한다
    - [x] Checkbox, Switch(둘 다 오른쪽 `label` prop. Field 안에서는 생략), RadioGroup(`options` 배열)
    - [x] Select(options 배열, Portal + animate-enter/exit), Slider(손잡이 개수 = value 길이, `sem.color.track` 슬롯 추가)
    - [x] Toggle, ToggleGroup(항목 스타일 공유. `type` 판별 유니온 유지를 위해 분배되는 Omit 사용)
  - 피드백 7종
    - [x] Alert (tone 4종. danger는 role=alert, 나머지는 role=status)
    - [x] Toast — Radix Toast + `useSyncExternalStore` 큐 store + 명령형 `toast()` + `<ToastProvider>`. 동시 3개 제한, 중복 병합 없음. 메서드는 `toast.danger`(라이브러리 어휘 통일)
    - [x] Tooltip(Provider 내장, `surface-inverse` 슬롯 추가), Popover(상호작용 가능, 포커스 트랩)
    - [x] Progress(track 슬롯 공유), Spinner(currentColor), Skeleton(감싼 영역이 role=status + aria-busy로 상태를 알린다)
  - [x] changeset 작성 → PR #3 생성, CI 통과
  - [ ] PR squash merge → 릴리스 PR 자동 생성 → 병합 시 publish·태그
- 다음 행동: PR #3(https://github.com/JunhaDex/fabrics-design-system/pull/3)을 squash merge한다. 병합하면 changesets가 릴리스 PR을 만들고, 그 PR을 병합할 때 publish와 `v0.2.0` 태그가 실행된다. 이후 이 파일의 '진행 중' 절을 '완료'로 옮긴다

## 다음 버전 (계획)
- v0.3 데이터 표시: Table(정적), DataTable(정렬·선택·페이지네이션), Tabs, Accordion, Badge, Separator
- v0.4 레이아웃: Dialog(모달), Footer, TopNav, SideNav, Columns, BentoGrid
- v0.5 테마: brutalism, tactile-surface (v0.2~0.4 컴포넌트로 슬롯·스타일 레이어 검증)
- v0.6 fabrics 도메인 컴포넌트: 목록은 첫 소비 프로젝트 기획 시 확정

## 완료
- v0.1.1 (2026-09-22) 패키지 README: 레지스트리 페이지용 README 3종 추가. 릴리스 워크플로를 `changesets/action@v2`로 전환해 패키지별 태그·GitHub Release 자동 생성 복구, 저장소 레벨 `vX.Y.Z` 태그 생성 step 추가
- v0.1.0 (2026-09-22) 최초 골격: 토큰→테마→코어→Storybook 파이프라인 연결. `packages/tokens`(DTCG primitives/semantic, `@theme` CSS 변수), `packages/core`(Button variant 4·size 3·`asChild`, `layoutClass`, tsdown), `themes/neutral`(light/dark 단일 번들), `apps/storybook`(`data-mode` 툴바). changesets → CHANGELOG → 태그 → GitHub Packages publish 파이프라인 검증 완료

## 미확정 사항
- 로컬 설치 검증(`npm view @junhadex/core`): `.zshrc`에 `GITHUB_TOKEN_PKG`(classic PAT, `read:packages`) 설정 후 확인 필요. 0.1.1 tarball에 README가 포함된 것은 `npm pack --dry-run`으로 확인함
- fabrics 도메인 컴포넌트 v1 목록 (첫 소비 프로젝트 기획 시)
- DataTable의 헤드리스 라이브러리 선택 (TanStack Table 후보, v0.3 착수 시 결정)
- Calendar/DatePicker 설계 전반. 착수 조건은 실사용 프로젝트의 요구사항 확정(선택 모드(단일/범위/다중), 시간대 취급, 입력 포맷, 로캘, 주 시작일)
- `packages/tokens`·`themes/neutral`(빌드 스크립트 JS)을 린트 대상에 넣을지. 현재는 제외했고, 필요해지면 `@repo/eslint-config`에 base 설정을 추가한다
- `layoutClass()`를 거치지 않은 className 전달을 잡는 커스텀 ESLint 규칙. 컴포넌트가 쌓인 뒤 작성한다
- Field + RadioGroup 조합. Field는 `<label htmlFor>`를 쓰는데 radiogroup은 div라 레이블이 걸리지 않는다. 그룹 레이블은 `aria-labelledby`나 fieldset/legend가 필요하므로 Field에 그룹 모드를 넣을지 판단해야 한다
- Select의 옵션 그룹(optgroup) 지원과 Slider의 범위(2-thumb) 지원 여부. props 래핑 API의 경계이며, 실제 요구가 생길 때 추가한다
- Storybook 자체 호스트 위치와 시기
