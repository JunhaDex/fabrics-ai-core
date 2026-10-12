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
- `@repo/contracts` 도메인 스키마 (zod 4)
  - `Category`: `top`, `bottom`, `outer`, `dress`, `shoes`, `accessory`. 가방은 `accessory`에 포함한다
  - `Item`: `id`, `name`, `category`, `imageUrl`, `createdAt`. 색상·계절·브랜드 등은 기능 개발 TODO에서 정한다. `imageUrl`이 null이면 UI가 플레이스홀더를 보여준다. 날짜는 서버→클라이언트 직렬화를 거치므로 ISO 문자열로 둔다
  - `Outfit`: `id`, `tags`, `items`. item을 id가 아닌 객체로 담는다. 태그는 `#` 없이 저장하고 UI가 붙인다
  - `User`: `id`, `name`
  - 화면 단위 집계 스키마는 두지 않는다. 화면별 조합은 각 zone의 `server/` 계층이 맡는다
- `@repo/mock`은 Backend 호출로 교체할 수 있게 async 함수로 노출하고, 반환 전에 contracts 스키마로 `parse`한다. 카테고리 개수는 fixture 옷 목록에서 계산한다
- `@repo/contracts`, `@repo/mock`도 `@repo/ui`처럼 빌드 없이 TS 소스를 export한다. 소비하는 앱은 `transpilePackages`에 추가한다
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
- 모드 쿠키는 `mode`(`light`|`dark`, `path=/`, 1년, `SameSite=Lax`)다. 서버는 `@repo/ui/mode`의 `getMode()`로 읽고, 다른 값이거나 없으면 light로 SSR한다
- 쿠키가 없으면 시스템 설정을 따른다. `<head>`의 `ModeScript`가 첫 페인트 전에 `prefers-color-scheme: dark`면 `data-mode="dark"`로 바꾼다. 이 때문에 `<html>`에 `suppressHydrationWarning`을 둔다. 판단할 수 없으면 light다
- 토글(`ModeToggle`, TopBar 오른쪽)은 쿠키를 쓰고 `data-mode`를 즉시 바꾼다. 아이콘(Moon/Sun)은 `dark:` variant로 전환해 hydration 결과를 같게 둔다. 한 번 토글하면 이후로는 쿠키가 시스템 설정보다 우선한다
- 레이아웃이 쿠키를 읽으므로 모든 라우트는 요청 시 렌더링(ƒ)이다
- `[data-mode="dark"] { color-scheme: dark }`를 `@repo/ui` 진입 CSS에 둔다. theme-neutral에 제안했고(`common-design-todo.md` 미확정 사항), 반영되면 로컬 정의를 지운다
- zone 경계를 넘는 링크는 `<Link>` 대신 `<a>`를 쓴다. 모든 zone이 같은 AppShell을
  SSR해 hard navigation 시 시각적 연속성을 유지한다
- 범용 컴포넌트가 common-design에 없으면 `@repo/ui`에 로컬로 먼저 만들고, 검증되면
  common-design으로 승격한다. 도메인 컴포넌트(카드 등)는 이 프로젝트가 정의한다
- 로컬 AppShell의 TopBar, SideNav, BottomTabBar는 common-design v0.4에서 core로 승격한다
  (2026-10-06). v0.4 릴리스 후 `@repo/ui`의 로컬 구현을 core 컴포넌트로 교체하고, 탭 목록과
  활성 판정(`isActive`), AppShell 조합, md 전환 클래스는 이 프로젝트에 남긴다
- 홈 위젯(`ItemCard`, `OutfitCard`, `CategorySummary`, `HashtagEntry`)은 `@repo/ui`에 두고 데이터는 props로만 받는다. 카테고리 한글 라벨(상의/하의/아우터/원피스/신발/액세서리)도 `@repo/ui`가 소유한다
- 아이템 이미지가 없으면 `@repo/ui`의 인라인 SVG 플레이스홀더를 그린다. 파일 asset이 아니므로 zone별 assetPrefix의 영향을 받지 않는다
- 홈의 해시태그 진입점은 입력창 모양의 `/styling` 링크다. 실제 입력은 styling zone이 맡는다
- 홈의 "최근 등록한 옷"에 `/closet` 전체 보기 링크를 둔다. 카테고리 요약은 closet 필터가 생기기 전까지 링크하지 않는다
- 로그인 화면 수단: Google, Apple, Naver, Kakao. iOS에서 서드파티 소셜 로그인을
  제공하면 App Store 가이드라인 4.8에 따라 Sign in with Apple 같은 동등 옵션이 필요하다
- 로그인 화면은 AppShell 밖이다. shell의 홈은 `app/(main)/` route group의 레이아웃이 AppShell을 두르고, `/login`은 safe area를 직접 처리한다
- 소셜 로그인 버튼 (`apps/shell/app/login/social-buttons.tsx`)
  - 순서는 카카오, 네이버, Apple, Google. 높이 44px(Apple 기본값), 너비 동일, radius 12px(Kakao 규정)로 통일한다
  - 색상·글꼴·글자 크기는 각 공식 가이드를 따른다. Kakao `#FEE500`·레이블 85% 16px, Naver `#03A94D`·흰 N 16px, Apple light black·dark white·시스템 글꼴 19px(버튼 높이의 43%), Google light/dark 테마·Google Sans Medium 14/20·안쪽 1px 테두리(inset ring)
  - 아이콘은 Apple Left-aligned md 로고 폭(31px) 슬롯 중앙에 두어 네 버튼의 아이콘 중심을 맞춘다
  - 아이콘 파일은 `apps/shell/public/social/`에 공식 리소스에서 아이콘만 추출해 둔다. Apple 로고는 HIG에 따라 자르지 않고 배경만 제거한다
- dark 모드 스타일은 Tailwind `dark:` variant로 쓴다. `@repo/ui` 진입 CSS에 `[data-mode="dark"]` 기준 `@custom-variant dark`를 정의한다
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
  - [x] Turborepo monorepo와 공유 패키지 골격
  - [x] Multi-Zones 라우팅 (shell → closet, styling) 로컬 동작
  - [x] 개인화 홈 레이아웃 (모바일, PC 반응형)
  - [x] 로그인 화면 (UI만)
  - [x] light/dark 모드 전환이 zone 간에 유지됨
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
  - [x] `@repo/contracts`, `@repo/mock`에 홈 화면용 스키마와 fixture
  - [x] shell: 홈(인사, 해시태그 입력 진입점, 오늘의 코디, 최근 등록한 옷, 카테고리 요약)
  - [x] shell: 로그인(Google, Apple, Naver, Kakao 버튼)
  - [x] closet, styling: 페이지 1개짜리 zone, assetPrefix, shell rewrites
  - [x] 모드 쿠키와 SSR `data-mode`, 토글 UI
- 작업 브랜치: `feat/v0.1`. 핵심 기능이 모두 완료되면 main으로 PR을 열어 squash merge한다
- 다음 행동: 핵심 기능 5개 완료. PR #1(https://github.com/JunhaDex/fabrics-stylist-web/pull/1) squash merge 후 `git cliff --tag v0.1.0 -o CHANGELOG.md`, 태그 v0.1.0을 만들고 이 절을 "완료"로 옮긴다

## 다음 버전 (계획)

## 완료

## 미확정 사항
- 실제 앱 이름
- zone 간 hard navigation을 부드럽게 할 cross-document View Transitions 도입 여부
