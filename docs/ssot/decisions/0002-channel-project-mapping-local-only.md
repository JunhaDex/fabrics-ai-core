# ADR 0002: 채널↔프로젝트 매핑은 로컬 전용 파일로 관리한다

## 상태
승인됨 (2026-09-20)

## 배경
`tools/slack-worker`는 Slack 채널당 프로젝트 1개(A안)로 운영한다.
`bridge.py`가 이 매핑을 알아야 어느 채널의 멘션을 어느
`projects/<name>/`에서 처리할지 결정할 수 있다.

## 결정
이 매핑은 `tools/slack-worker/channels.local.json`에 저장하고,
**메타 저장소에 커밋하지 않는다.** 대신 형태만 보여주는
`channels.example.json`을 커밋해 둔다. `.env`와 동일한 패턴이다.

## 근거
- 채널 ID는 워크스페이스마다 다르다. 같은 `0_pjt_fabrics`를 여러
  Slack 워크스페이스(예: 개인용/팀용)에서 쓰면 매핑 값 자체가 달라져,
  커밋된 값이 오히려 다른 기기에서 오작동의 원인이 된다.
- 이 값은 조직 규칙(SSOT)이 아니라 **특정 기기의 실행 환경 상태**다.
  `docs/ssot/decisions/0001-org-tooling-in-control-repo.md`가 정의한
  "조직 도구는 메타 저장소에 포함한다"는 원칙과는 별개로, 그 도구
  *내부의 로컬 실행 상태*까지 커밋 대상은 아니라는 것을 이번에 함께
  명확히 한다.

## 범위
`tools/slack-worker/channels.local.json`에 한정된 결정이 아니라, 향후
"기기/워크스페이스마다 값이 다른 로컬 실행 설정" 전반에 적용되는
일반 규칙이다. `.gitignore`의 `*.local.json` 패턴이 이를 구현한다.
새로운 조직 도구를 추가할 때도 이 패턴(`<name>.local.json` +
`<name>.example.json`)을 따른다.

## 영향받는 문서
- `.gitignore`: `*.local.json`, `tools/slack-worker/state/` 추가
- `tools/slack-worker/README.md`: 새 환경 세팅 시 채워야 할 파일로 명시
- `docs/ssot/repo-architecture.md`: 부트스트랩 체크리스트, `.gitignore` 핵심 갱신
