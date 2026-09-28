# ADR 0005: 복수 저장소 프로젝트는 `.git` 없는 컨테이너 디렉터리를 쓴다

## 상태
승인됨 (2026-09-29)

## 배경
`repo-architecture.md`는 `projects/<name>/` 하나가 곧 독립 저장소 하나라고
전제해 왔다. 그러나 `app-pocket`은 안드로이드(Kotlin)와 iOS(Swift) 구현을
각각 별도 저장소로 두면서도, 하나의 프로젝트로 다뤄야 한다.

- 두 구현체는 동일한 브릿지 계약을 구현하므로 결정 사항이 거의 전부 공통이다.
- 하나의 세션이 양 플랫폼을 함께 지휘하고, 서브에이전트가 각 플랫폼의 코드를
  수정하는 작업 방식이 필요하다.
- Slack 채널과 todo 파일을 하나로 유지하려는 요구가 있다.

기존 전제를 그대로 두면 아래 문제가 발생한다.
- 서브에이전트는 부모 세션의 작업 디렉터리와 권한을 상속하므로,
  `projects/app-pocket-aos/`에서 시작한 세션은 `projects/app-pocket-ios/`를
  수정할 수 없다.
- `worker.py`의 `project_dir_for()`가 채널 하나를 디렉터리 하나에 대응시키므로,
  채널 하나로 두 디렉터리를 지시할 수 없다.
- todo 파일명 규칙(`docs/<프로젝트 디렉터리명>-todo.md`)을 만족시킬 수 없다.

검토한 대안: (1) 두 구현을 하나의 저장소에 담는 모노레포, (2) 두 저장소를
형제 디렉터리로 두고 `additionalDirectories`로 교차 접근을 여는 방식.
(2)는 프로젝트 격리 원칙에 예외를 하나 더 만들고, SSOT·스킬·레지스트리까지
일곱 건의 변경을 요구했다.

## 결정
1. **컨테이너 디렉터리를 도입한다**: 프로젝트 하나가 복수 저장소를 가질 때,
   `projects/<name>/`은 `.git`을 갖지 않는 평범한 디렉터리로 두고, 그 하위에
   각 저장소를 clone한다. `app-pocket`의 경우 `projects/app-pocket/aos/`와
   `projects/app-pocket/ios/`다.
2. **프로젝트 등록 단위는 컨테이너다**: `docs/PROJECTS.md`의 행,
   `docs/<name>-todo.md`, Slack 채널이 각각 하나씩이다. 기존 명명 규칙과
   `worker.py`가 무수정으로 동작한다.
3. **컨테이너 설정 파일은 메타 저장소가 추적한다**: 컨테이너의 `CLAUDE.md`와
   `.claude/settings.json`은 어느 프로젝트 저장소에도 속하지 않아 버전 관리
   대상에서 누락된다. 메타 저장소 `.gitignore`에 예외를 두어 이 두 개만
   추적한다. git은 상위 디렉터리가 제외된 상태에서 하위 파일을 되살리지
   못하므로, 디렉터리를 먼저 예외 처리한 뒤 내용을 다시 제외하는 순서를
   지켜야 한다.
   ```
   projects/*
   !projects/.gitkeep
   !projects/<name>/
   projects/<name>/*
   !projects/<name>/CLAUDE.md
   !projects/<name>/.claude/
   ```
   예외는 해당 프로젝트 이름으로 명시한다. `projects/*/` 형태의 와일드카드를
   쓰면 자체 저장소를 가진 기존 프로젝트의 `CLAUDE.md`까지 메타 저장소가
   중복 추적하게 된다.
4. **프로젝트 격리 원칙은 유지된다**: 작업 디렉터리 경계가 다른 프로젝트를
   막는다는 ADR 0003의 전제는 그대로다. 컨테이너 방식은 경계를 넓히는 것이
   아니라, 함께 다뤄야 할 저장소들을 경계 안에 모으는 것이다.
5. **단일 저장소를 기본으로 유지한다**: 이 패턴은 플랫폼별 툴체인이 달라
   저장소 분리가 불가피한 경우에 한정한다. 저장소를 나눌 이유가 없으면
   `projects/<name>/` 자체를 저장소로 두는 기존 방식을 쓴다.

## 검증 결과
임시 저장소에서 3번의 `.gitignore` 규칙을 확인했다. `git add -A` 이후 추적
대상은 `projects/app-pocket/CLAUDE.md`와
`projects/app-pocket/.claude/settings.json` 둘뿐이었고, 하위 저장소의 파일과
`settings.local.json`은 제외되었다(`*.local.json` 패턴이 예외 규칙보다 뒤에
있어 우선한다).

## 알려진 비용
- 컨테이너 디렉터리가 git 저장소가 아니므로, 세션에서 git 명령을 쓸 때 대상을
  명시해야 한다(`git -C aos status`). 프로젝트 `CLAUDE.md`에 기재한다.
- 릴리스가 저장소마다 한 번씩 수행된다. CHANGELOG 생성과 태그 작업이
  저장소별로 필요하며, 버전 번호의 정합성은 사람이 관리한다.
- 새 기기 부트스트랩이 한 단계 늘어난다. 컨테이너를 만든 뒤 하위에 각각
  clone해야 한다.

## 영향받는 문서
- `docs/ssot/repo-architecture.md`: "프로젝트 저장소" 절에 컨테이너 패턴 추가,
  "새 기기 부트스트랩" 체크리스트 보강, ".gitignore 핵심" 갱신
- `.gitignore`: `app-pocket` 예외 규칙 추가
- `.claude/skills/new-project/SKILL.md`: **갱신하지 않는다**(2026-09-29 결정).
  모든 예외를 스킬에 반영하면 스킬이 비대해진다. 복수 저장소가 필요한
  경우 이 ADR을 참조해 그때 판단한다
- `docs/PROJECTS.md`: 저장소 URL과 로컬 경로를 복수로 표기하는 규칙
