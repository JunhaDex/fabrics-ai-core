# ADR 0004: 프로젝트 todo는 두 스코프를 메타 저장소 파일 하나에 담는다

## 상태
승인됨 (2026-09-22)

## 배경
프로젝트 진행 관리에는 수명이 다른 두 종류의 todo가 필요하다.
- **프로젝트 스코프**: 전체 진행 상황과 지금까지 완료된 작업의 요약. 프로젝트와
  함께 계속 누적된다.
- **버전 스코프**: 새 feature/chore/refactoring 하나의 요구사항(핵심 기능)과
  세부 step. 작업 중 실시간으로 갱신되고, 릴리스되면 사라진다.

종전 규칙(`docs/TODO.md`)은 `docs/<name>-todo.md`에 최종 결정과 다음 행동만
남기고 완료 항목은 삭제해 이력을 git log에 맡겼다. 그러나 git log는 그대로
읽기에 가독성이 낮고, 여러 프로젝트의 이력을 한곳에서 볼 수 없었다.

검토한 대안: 프로젝트 저장소 README 상태 표, 프로젝트 저장소 내부
`docs/changes/<slug>.md`(브랜치와 수명을 같이하는 파일), OpenSpec 프레임워크,
GitHub PR 본문 체크리스트.

## 결정
1. **위치**: 두 스코프 모두 메타 저장소 `docs/<name>-todo.md` 한 파일에 둔다.
   모든 프로젝트의 진행 상황과 이력을 루트 세션 한곳에서 보기 위해서다.
   feature에 얽힌 전체 진행 상황을 파일 하나에서 보려는 요구도 충족한다.
2. **완료 절 허용**: 릴리스된 버전은 삭제하지 않고 "완료" 절에 요약으로
   남긴다. 제거 대상은 시행착오뿐이다(A→B→C를 검토해 B로 결정했다면 A, C의
   탐색 이력은 남기지 않는다).
3. **버전 스코프의 소멸 방식**: "진행 중" 절이 릴리스 시 "완료" 절로 이동하며
   1~3줄로 압축된다. 세부 step은 버린다.
4. **프로젝트 저장소 측**: README 상태 표와 프로젝트 내부 `docs/`는 두지
   않는다. 커밋 수준 이력은 feature 단위 squash merge와 자동 생성
   `CHANGELOG.md`(SemVer, Conventional Commits, Keep a Changelog)가 담당한다.
   상세 규칙은 `repo-architecture.md` "버전·변경 이력".
5. **OpenSpec 미도입**: 모든 feature가 디렉터리 단위로 나뉘지 않아
   프레임워크를 그대로 적용하기 어렵다. 규약(제안→적용→아카이브)의 취지만
   위 3번으로 차용한다.
6. **브랜치와 todo 파일을 연동하지 않는다**: 브랜치는 언제든 자유롭게
   분기하며, todo 파일의 생성·삭제와 무관하다.
7. **프로젝트 세션의 접근 권한**: 프로젝트 `.claude/settings.json`에
   `permissions.additionalDirectories: ["../../docs"]`를 둔다. todo 파일을
   실시간 갱신하고 SSOT 문서를 컨텍스트로 읽기 위해서다. 프로젝트 세션은
   auto mode를 기본으로 쓰므로 승인 부담은 크지 않지만, 설정으로 고정해
   컨텍스트 제공을 보장한다. ADR 0003의 "settings.json을 만들지 않는다"는
   이 항목으로 대체되며, "deny 규칙을 두지 않는다"는 유지된다.

## 검증 결과 (헤드리스 세션으로 확인)
- `additionalDirectories`가 없으면 프로젝트 세션에서 `../../docs/PROJECTS.md`
  읽기가 거부된다.
- 상대 경로 `"../../docs"`는 프로젝트 루트 기준으로 해석되어 읽기가 허용된다.
- trust되지 않은 워크스페이스에서는 설정이 무시된다("Ignoring 1
  permissions.additionalDirectories entry ... this workspace has not been
  trusted"). 새 기기에서는 대화형 세션을 한 번 열어 trust를 수락해야 한다.

## 영향받는 문서
- `docs/TODO.md`: "프로젝트 todo 파일" 절을 두 스코프 구조로 개정
- `docs/ssot/repo-architecture.md`: "프로젝트 격리"에 `docs/` 예외 추가,
  "버전·변경 이력" 절 신설
- `docs/ssot/decisions/0003-no-explicit-permission-deny.md`: 보완 각주 추가
- `.claude/skills/new-project/SKILL.md`: 1·4·5단계 갱신
- `docs/common-design-todo.md`: 새 구조로 재배치
- `projects/common-design/.claude/settings.json`: `additionalDirectories`만 담아 재생성
