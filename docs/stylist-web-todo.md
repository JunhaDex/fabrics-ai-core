# stylist-web todo

저장소: https://github.com/JunhaDex/fabrics-stylist-web · 로컬: `projects/stylist-web/`
Slack: `C0C6MR046MV`
목적: 옷장을 등록하고 그날의 TPO에 맞는 코디를 추천받는 웹앱. pocket 컨테이너에 처음 탑재되는 웹앱이다 (Next.js, Turborepo, Multi-Zones)

## 결정 사항

### 정체성과 착수 범위
- `fabrics-stylist-web`은 저장소용 가칭이다. 실제 앱 이름은 별도로 정한다
- 이 todo는 bridge 연동 전에 pocket에 띄울 화면을 먼저 만드는 범위다. app-pocket
  S3가 블로커에 걸려 있어 bridge 개발이 끝나지 않았으므로, 기능 개발(a 옷장 목록,
  b 옷 상세, c 옷 등록, d TPO 입력과 추천 결과)은 bridge 개발 후 별도 TODO로 진행한다
- 추천, 인증, 데이터 저장은 이 todo에서 설계하지 않는다. 기능 없이 UI만 구성한다
- 배포 범위는 로컬 실행 검증까지다

### 저장소 구조
- Turborepo monorepo 단일 저장소. Backend는 다른 TODO에서 별도로 구성한다
- MFA는 Next.js Multi-Zones로 구성한다. `@module-federation/nextjs-mf`는 App Router를
  지원하지 않고 지원 종료 단계이므로 쓰지 않는다
- zone 분할 (같이 방문하는 페이지를 같은 zone에 묶어 hard navigation을 줄인다)
  - `apps/shell`: 기본 zone. `/`(개인화 홈), `/login`, `/.well-known/*`. 다른 zone으로
    보내는 rewrites를 소유한다. assetPrefix 없음
  - `apps/closet`: `/closet/*`, assetPrefix `/closet-static`. 옷장 목록·상세·등록
    (라우트 접두사는 `basePath` 대신 공식 가이드대로 `app/closet/` 디렉터리로 둔다)
  - `apps/styling`: `/styling/*`, assetPrefix `/styling-static`. 해시태그 TPO 입력과 추천 결과
- 공유 패키지 (내부 비배포, `@repo/*`)
  - `@repo/ui`: 이 프로젝트 전용 재사용 컴포넌트. `@junhadex/core` 위에 AppShell,
    BottomTabBar(모바일), SideNav(PC), TopBar, ItemCard, OutfitCard, HashtagInput 등을
    둔다. Tailwind 진입 CSS를 여기서 한 번만 정의한다
  - `@repo/contracts`: zod 스키마와 타입. mock과 이후 Backend 계약이 공유한다
  - `@repo/mock`: fixture와 mock adapter (`server-only`)
  - `@repo/eslint-config`, `@repo/typescript-config`
- 개인화 홈의 위젯은 `@repo/ui`에 두고 빌드 시점에 결합한다. Multi-Zones는 다른 zone의
  컴포넌트를 런타임에 끼워 넣을 수 없다

### BFF
- 별도 BFF 앱을 두지 않는다. 각 zone의 Next 서버가 자기 영역의 BFF다
- 서버 컴포넌트는 자기 서버로 HTTP를 보내지 않고 zone 내부 `server/` 데이터 계층을
  직접 호출한다. 이 계층이 지금은 `@repo/mock`을, 이후에는 Backend를 호출한다
- 클라이언트 발 변경 요청은 자기 경로 아래 Route Handler(`/closet/api/*` 등)로 받는다.
  Server Actions를 쓰면 `serverActions.allowedOrigins`에 사용자 대면 origin을 지정한다

### 화면과 디자인 시스템
- mobile first. PC는 반응형으로 대응한다 (모바일 BottomTabBar → PC SideNav)
- 내비게이션 탭은 홈(`/`), 옷장(`/closet`), 스타일링(`/styling`) 3개다
- BottomTabBar → SideNav 전환 기준은 Tailwind `md`(768px)다. 전환은 CSS 반응형 클래스로만 한다
- pocket WebView는 edge-to-edge 전체 화면이고 safe area는 웹이 CSS로 처리한다. 레이아웃은 `viewport-fit=cover`로 `env(safe-area-inset-*)`를 활성화하고, TopBar는 상단, BottomTabBar는 하단 inset을 패딩으로 둔다. 가로 모드(iPad 등)도 지원하므로 TopBar, SideNav, BottomTabBar, 본문 영역이 좌우 inset도 처리한다
- inset은 `env()`만 쓴다. 네이티브가 `--safe-area-inset-*` 값을 주입하는 방식은 쓰지 않고, Android는 WebView M144 이상을 지원 조건으로 둔다. 네이티브 쪽 규약은 `architecture/app-pocket-webview-layout.md`가 정본이다
- TopBar는 왼쪽에 임시 앱 이름 텍스트, 오른쪽에 모드 토글 자리를 둔다. 앱 이름이 정해지면 텍스트를 교체하고, 토글 동작은 모드 쿠키 step에서 구현한다
- 테마 `neutral`, 모드 light/dark 모두 지원한다
- 모드는 쿠키에 저장하고 각 zone의 서버 레이아웃이 `<html data-mode>`로 SSR한다.
  모든 zone이 같은 origin이라 zone을 넘나들어도 쿠키가 공유되고 깜박임이 없다
- zone 경계를 넘는 링크는 `<Link>` 대신 `<a>`를 쓴다. 모든 zone이 같은 AppShell을
  SSR해 hard navigation 시 시각적 연속성을 유지한다
- 범용 컴포넌트가 common-design에 없으면 `@repo/ui`에 로컬로 먼저 만들고, 검증되면
  common-design으로 승격한다. 도메인 컴포넌트(카드 등)는 이 프로젝트가 정의한다
- 로컬 AppShell의 TopBar, SideNav, BottomTabBar는 common-design v0.4에서 core로 승격한다
  (2026-10-06). v0.4 릴리스 후 `@repo/ui`의 로컬 구현을 core 컴포넌트로 교체하고, 탭 목록과
  활성 판정(`isActive`), AppShell 조합, md 전환 클래스는 이 프로젝트에 남긴다
- 로그인 화면 수단: Google, Apple, Naver, Kakao. iOS에서 서드파티 소셜 로그인을
  제공하면 App Store 가이드라인 4.8에 따라 Sign in with Apple 같은 동등 옵션이 필요하다
- 예시 이미지는 플레이스홀더로 대체한다

### 로컬 실행
- `turbo dev`로 shell(3000), closet(3001), styling(3002)을 함께 띄운다. shell이 env의
  localhost 포트로 rewrite한다
- pocket은 shell(3000) 하나만 바라본다. `adb reverse` 사용 시 Host가 `localhost:3000`이라
  `allowedDevOrigins`를 설정하지 않는다 (`app-pocket-todo.md`와 동일)

### 빌드 설정
- 의존성 버전은 캐럿(`^`)으로 표기한다(`lucide`처럼 core와 같은 패키지를 직접 의존할 때도 동일). pnpm 기본값이라 이후 추가분과 섞이지 않고, 재현성은 `pnpm-lock.yaml`이 보장한다
- 런타임과 도구는 템플릿 값을 따른다: Node `>=24`, pnpm 11, TypeScript 7.0.2. TS 7에서 build, check-types, lint가 모두 통과한다
- Tailwind 진입 CSS는 `@import "tailwindcss" source(none)`으로 자동 탐지를 끈다. 스캔 대상은 `@repo/ui`의 `@source`(core dist, ui 소스)와 각 앱 globals.css의 `@source "./"`로만 지정한다
- `@repo/ui`는 빌드 단계 없이 CSS와 소스를 그대로 export한다. CSS 안의 import가 `packages/ui` 기준으로 해석되므로 `tailwindcss`와 `@junhadex/theme-neutral`은 ui의 dependencies에 둔다
- turbo는 Strict 환경변수 모드다. rewrites 목적지는 빌드 시점에 결정되므로 `CLOSET_URL`, `STYLING_URL`을 `apps/shell/turbo.json`의 `env`에 선언해 전달하고 캐시 해시에 포함한다

### 변경 이력
- 앱이므로 CHANGELOG 생성기는 git-cliff다 (`docs/ssot/repo-architecture.md` "버전·변경 이력")

## 진행 중: v0.1 최초 골격
- 컨텍스트: bridge 연동 전에 pocket에 보여줄 화면을 만들고, monorepo와 Multi-Zones
  구조를 실제로 검증한다. 구조 결함을 기능 개발 TODO 이전에 발견하는 것이 목적이다
- 핵심 기능 (모두 완료되면 릴리스):
  - [ ] Turborepo monorepo와 공유 패키지 골격
  - [x] Multi-Zones 라우팅 (shell → closet, styling) 로컬 동작
  - [ ] 개인화 홈 레이아웃 (모바일, PC 반응형)
  - [ ] 로그인 화면 (UI만)
  - [ ] light/dark 모드 전환이 zone 간에 유지됨
- 세부 step:
  - [x] 부트스트랩: GitHub 저장소 생성, `projects/stylist-web/`에 clone
  - [x] 부트스트랩: 공식 문서 기준으로 Turborepo 생성
  - [x] 부트스트랩: `cliff.toml` 생성
  - [x] 부트스트랩: Slack 채널 생성, CodeButler 초대
  - [x] 부트스트랩: first commit, 원격 push
  - [x] 부트스트랩: 프로젝트 CLAUDE.md, `.claude/settings.json` 스캐폴딩, 루트 색인 갱신
  - [x] GitHub Packages 인증(`.npmrc`) 후 `@junhadex/core`, `@junhadex/theme-neutral` 설치
  - [x] `@repo/ui`에 Tailwind 진입 CSS
  - [x] `@repo/ui`에 AppShell(BottomTabBar, SideNav, TopBar). 첫 컴포넌트를 추가할 때 템플릿에서 제거한 `check-types` 스크립트와 `"./*"` export를 되살린다
  - [ ] `@repo/contracts`, `@repo/mock`에 홈 화면용 스키마와 fixture
  - [ ] shell: 홈(인사, 해시태그 입력 진입점, 오늘의 코디, 최근 등록한 옷, 카테고리 요약)
  - [ ] shell: 로그인(Google, Apple, Naver, Kakao 버튼)
  - [x] closet, styling: 페이지 1개짜리 zone, assetPrefix, shell rewrites
  - [ ] 모드 쿠키와 SSR `data-mode`, 토글 UI
- 작업 브랜치: `feat/v0.1`. 핵심 기능이 모두 완료되면 main으로 PR을 열어 squash merge한다
- 다음 행동: `@repo/contracts`, `@repo/mock`에 홈 화면용 스키마와 fixture를 만든다. 이후 홈과 로그인 화면을 진행한다

## 다음 버전 (계획)

## 완료

## 미확정 사항
- 실제 앱 이름
- 쿠키가 없을 때의 기본 모드. light 고정으로 할지, 시스템 설정을 따를지
  (SSR 단계에서는 시스템 설정을 알 수 없다)
- zone 간 hard navigation을 부드럽게 할 cross-document View Transitions 도입 여부
