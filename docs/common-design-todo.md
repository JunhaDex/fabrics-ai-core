# common-design todo

저장소: https://github.com/JunhaDex/fabrics-design-system · 로컬: `projects/common-design/`
목적: 테마(빌드 시점)·모드(런타임) 2층위 스타일을 지원하는 fabrics 공통 디자인 시스템 (React, Radix, Tailwind v4, npm)

## 결정 사항 (2026-09-22)
- 스택: TypeScript 6.x(7.x는 tsdown dts 미지원으로 보류), React 19, pnpm workspace + catalog, Turborepo, 통합 `radix-ui`, Tailwind v4 `@theme`, tailwind-variants v3, Style Dictionary v5(DTCG), tsdown, Storybook 10, Vitest, changesets
- 배포: GitHub Packages private, 스코프 `@junhadex` (저장소 소유자와 일치해야 함)
- 구조: `packages/tokens`, `packages/core`, `themes/<name>`, `apps/storybook`
- 테마 = 룩앤필, 빌드 시점 선택, 토큰 + 선택적 스타일 레이어, 밀도 고정. v1: neutral, brutalism, tactile-surface
- 모드 = light/dark/corporate 등, `data-mode` 런타임 전환
- 플랫폼 변형은 반응형으로 대응. 벤토 그리드는 core 레이아웃 컴포넌트
- className 오버라이드는 레이아웃 속성만 허용
- 토큰 SSOT는 코드, Storybook으로 시각화, Figma는 추후
- 초기 컴포넌트: 기본 폼/피드백, 데이터 표시, 레이아웃(모달, 푸터, top nav, side nav, columns), fabrics 도메인 컴포넌트

## 부트스트랩 마무리
- 컨텍스트: `new-project` 스킬 5단계까지 완료. 워크스페이스 루트 파일 생성 완료
- 상태: in-progress
- 다음 행동 (사용자):
  - [ ] `git push -u origin main`
  - [ ] `pnpm exec changeset init` (대화형)
  - [ ] npm 스코프 확정: `@junhadex` 유지 또는 GitHub org 생성 후 `@fabrics`

## 최초 골격 생성
- 컨텍스트: 프레임워크 CLI 우선. 상세 절차는 프로젝트 세션에서 진행
- 상태: not-started
- 다음 행동:
  - [ ] `packages/tokens`: `style-dictionary init basic` 후 primitives/semantic 구조로 정리, `@theme` 커스텀 format
  - [ ] `packages/core`: radix-ui + tailwind-variants + tsdown(`dts: true`, react peer)
  - [ ] `themes/neutral`: semantic light/dark + theme.json + `dist/theme.css`
  - [ ] `apps/storybook`: `create vite` → `storybook init --features docs test a11y`, 모드 전환 툴바
  - [ ] `pnpm build` (turbo) 통과

## 미확정 사항
- fabrics 도메인 컴포넌트 v1 목록
- Storybook 호스팅 위치
- 접근성 기준(WCAG 2.2 AA 가정), 브라우저 지원 범위(evergreen 최근 2개 메이저 가정)
