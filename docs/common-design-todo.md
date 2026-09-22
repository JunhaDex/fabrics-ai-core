# common-design todo

저장소: https://github.com/JunhaDex/fabrics-design-system · 로컬: `projects/common-design/`
목적: 테마(빌드 시점)·모드(런타임) 2층위 스타일을 지원하는 fabrics 공통 디자인 시스템 (React, Radix, Tailwind v4, npm)

## 결정 사항
- 스택: TypeScript 6.x(7.x는 tsdown dts 미지원으로 보류), React 19, pnpm workspace + catalog, Turborepo, 통합 `radix-ui`, Tailwind v4 `@theme`, tailwind-variants v3, Style Dictionary v5(DTCG), tsdown, Storybook 10, Vitest, changesets
- 배포: GitHub Packages private, 스코프 `@junhadex` 확정(저장소 소유자와 일치). publish는 GitHub Actions + `changesets/action`으로 실행(`GITHUB_TOKEN` 인증, PAT 불필요). main에 changeset이 쌓이면 릴리스 PR이 자동 생성되고, 병합 시 publish·태그가 실행된다
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
- Calendar/DatePicker: `react-day-picker` v9 의존. DatePicker는 Radix Popover + Calendar + Input 조합
- Storybook: 로컬 `storybook dev` 실행을 기준으로 한다. 자체 호스트 예정(시기 미정). Chromatic 애드온은 제거함
- 변경 이력: changesets가 `CHANGELOG.md`를 생성. feature 단위 PR + squash merge (`docs/ssot/repo-architecture.md` "버전·변경 이력")

## 진행 중: v0.1 최초 골격
- 컨텍스트: 토큰→테마→코어→Storybook 파이프라인이 끝까지 연결되는지 검증하는 버전. 컴포넌트는 Button 하나만 포함하고, 릴리스 파이프라인(changesets → CHANGELOG → 태그 → GitHub Packages publish)을 함께 검증한다
- 핵심 기능 (모두 완료되면 릴리스):
  - [x] `packages/tokens`: primitives/semantic 구조, `@theme` 커스텀 format으로 CSS 변수 생성 (`primitives.css`, `bridge.css`)
  - [x] `packages/core`: radix-ui + tailwind-variants 기반 `Button`(variant 4, size 3, `asChild`) + `layoutClass`, tsdown 빌드 (`dts: true`, react peer)
  - [x] `themes/neutral`: semantic light/dark + theme.json + `dist/theme.css` 단일 번들
  - [x] `apps/storybook`: `data-mode` 전환 툴바, Button·tokens 스토리
  - [x] `pnpm build` (turbo) 통과
  - [ ] GitHub Actions 릴리스 워크플로로 `@junhadex/*` publish 성공
- 세부 step:
  - [x] npm 스코프 확정: `@junhadex` 유지
  - [x] Chromatic 애드온 제거 (`main.ts`, `package.json`, lock 갱신, 빌드·테스트 통과 확인)
  - [x] 작업 트리 커밋 후 `git push -u origin main`
  - [ ] `pnpm exec changeset init` (대화형) 후 `.changeset/config.json`에 `access: restricted`, `baseBranch: main` 확인
  - [ ] `.github/workflows/release.yml`: `changesets/action` + `actions/setup-node`(`registry-url: https://npm.pkg.github.com`), `permissions: contents: write, packages: write, pull-requests: write`
  - [ ] 저장소 Settings → Actions → "Allow GitHub Actions to create and approve pull requests" 활성화
  - [ ] 첫 changeset 작성(tokens·core·theme-neutral 모두 minor) → 릴리스 PR 자동 생성 확인 → 병합 → publish·태그 확인
  - [ ] 릴리스 후 이 절을 "완료"로 이동
- 다음 행동 (사용자): changeset init → 워크플로 작성 → Actions 설정 순으로 진행

## 다음 버전 (계획)
- v0.2 폼/피드백 (DoD 적용 첫 버전. 첫 step으로 `addon-a11y` `test: 'error'` 전환과 Button 상호작용 테스트 보강)
  - 폼: Input, Textarea, Label, Field(label+control+오류 메시지), Checkbox, RadioGroup, Switch, Select, Slider, Toggle, ToggleGroup, Calendar, DatePicker
  - 피드백: Toast, Alert, Tooltip, Popover, Progress, Spinner, Skeleton
- v0.3 데이터 표시: Table(정적), DataTable(정렬·선택·페이지네이션), Tabs, Accordion, Badge, Separator
- v0.4 레이아웃: Dialog(모달), Footer, TopNav, SideNav, Columns, BentoGrid
- v0.5 테마: brutalism, tactile-surface (v0.2~0.4 컴포넌트로 슬롯·스타일 레이어 검증)
- v0.6 fabrics 도메인 컴포넌트: 목록은 첫 소비 프로젝트 기획 시 확정

## 완료
_(없음)_

## 미확정 사항
- fabrics 도메인 컴포넌트 v1 목록 (첫 소비 프로젝트 기획 시)
- DataTable의 헤드리스 라이브러리 선택 (TanStack Table 후보, v0.3 착수 시 결정)
- Storybook 자체 호스트 위치와 시기
