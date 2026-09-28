@../../CLAUDE.md
@../../docs/ssot/org-principles.md
@../../docs/ssot/repo-architecture.md

# app-pocket

웹앱 주소만 바꿔 끼우면 새 앱이 되는 OS별 웹뷰 컨테이너("pocket"). 웹앱에
기기 기능 브릿지를 제공한다.

## 디렉터리 구조

이 디렉터리는 **git 저장소가 아니다**. 독립 저장소 두 개를 담는 컨테이너다
(`../../docs/ssot/decisions/0005-multi-repo-project-container-directory.md`).

```
app-pocket/          # .git 없음. 세션의 작업 디렉터리
  aos/               # fabrics-pocket-aos (Kotlin)
  ios/               # fabrics-pocket-ios (Swift)
```

- **git 명령은 대상을 명시한다**: `git -C aos status`, `git -C ios commit`.
  컨테이너에서 `git` 명령을 그냥 실행하면 저장소를 찾지 못한다.
- 이 파일과 `.claude/settings.json`은 메타 저장소가 `.gitignore` 예외로
  추적한다. 두 하위 저장소에는 포함되지 않는다.
- 릴리스는 저장소마다 한 번씩 수행한다.

## 작업 방식

한 세션이 양 플랫폼을 함께 지휘한다. 추상 수준의 계획을 세운 뒤 서브에이전트가
`aos/`와 `ios/`의 코드를 각각 수정하는 방식을 기본으로 한다. 두 구현체는 동일한
브릿지 계약을 구현하므로, 한쪽만 바꾸고 다른 쪽을 두면 계약이 어긋난다.

## 버전

버전이 두 종류이며 **서로 연동하지 않는다**. 혼동하지 않도록 항상 구분해
부른다.

- **앱 버전**: 스토어에 배포되는 각 앱의 버전. 앱별로 상이하다.
- **런타임 버전**: pocket 래퍼 자체의 버전. git tag(`vX.Y.Z`)로 관리하며,
  공개 API는 브릿지 계약이다. MAJOR는 계약의 파괴적 변경, MINOR는 하위 호환
  기능 추가, PATCH는 계약이 바뀌지 않는 수정이다. 두 저장소는 **minor까지
  동일한 번호를 유지**하고, 공통 설정이 바뀌면 patch가 아니라 minor를 올린다.

## 설계 원칙

- **웹앱의 환경 판단은 버전 비교가 아니라 기능 탐지로 한다.** 스토어 빌드
  주기와 웹앱 배포 주기가 달라 구버전 앱이 상존하는 것이 정상이다.
- **capability 목록이 브릿지 주입값과 OS 권한 선언의 단일 근거다.** 앱이 쓰지
  않는 권한은 선언되지 않는다.
- **인증의 주체는 네이티브 하나다.** 웹뷰 안에서 로그인을 처리하지 않는다.
  SSO는 임베디드 웹뷰에서 차단되므로 시스템 브라우저를 경유해야 한다.
- **2단계(다중 앱 빌드)를 위해, 나중에 외부 주입으로 바뀔 값은 플랫폼마다 한
  곳에 모아 둔다.** 안드로이드는 product flavor, iOS는 xcconfig다. 소스 곳곳에
  흩어 놓으면 2단계가 전면 수정이 된다.

결정의 근거와 전체 목록은 `../../docs/app-pocket-todo.md`의 "결정 사항"에 있다.

## 변경 이력

앱이므로 git-cliff를 쓴다. 저장소마다 `cliff.toml` 하나를 두고, 릴리스 시
`git cliff --tag vX.Y.Z -o CHANGELOG.md`를 실행한다. 상세는
`../../docs/ssot/repo-architecture.md`의 "버전·변경 이력" 참고.

## todo 관리

작업이 진행되면 루트 `../../docs/app-pocket-todo.md`를 실시간으로 갱신한다.
구조와 릴리스 시 처리는 `../../docs/TODO.md`의 "프로젝트 todo 파일" 절을
따른다. 시행착오는 기록하지 않고 최종 결정만 남긴다.

브릿지 계약을 npm 패키지로 분리하는 작업은 별도 프로젝트이며
`../../docs/app-bridge-todo.md`가 담당한다. 이 프로젝트의 네이티브 구현이
계약을 안정시킨 뒤에 착수한다.
