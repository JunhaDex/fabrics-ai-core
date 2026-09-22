---
name: new-project
description: fabrics 신규 프로젝트 착수 요청 시 사용한다. 필요한 리소스를 먼저 안내하고, 스택별 공식 Get Started 문서로 가이드하며, 사용자가 저장소 생성과 push를 직접 마치면 로컬 스캐폴딩과 루트 SSOT·색인 갱신을 진행한다.
---

# 신규 프로젝트 생성 가이드

CLAUDE.md의 "가이드 우선(Guide, not Generate)" 원칙을 따른다. 사용자가
직접 만들고, Claude는 안내·리뷰·후속 스캐폴딩을 담당한다.

## 1단계: 필요한 리소스 안내

신규 프로젝트 착수 요청을 받으면, 먼저 아래를 체크리스트로 안내한다.
이 시점에는 어떤 파일/디렉터리도 만들지 않는다.

- GitHub 저장소 (독립 저장소 — `docs/ssot/repo-architecture.md` 원칙)
- 로컬 clone 경로: `projects/<name>/`
- 전용 Slack 채널 (채널당 프로젝트 1개 — A안, `tools/slack-worker` 연동)
- CodeButler 봇을 해당 채널에 초대 (`/invite @CodeButler`)

체크리스트를 안내한 직후, 루트 `docs/<name>-todo.md`를 생성한다. 이 파일은
프로젝트 todo의 정본이며, 프로젝트 세션도 이 파일을 갱신한다. 구조와 절별
규칙은 `docs/TODO.md`의 "프로젝트 todo 파일" 절을 따른다. 초기에는 헤더(이름,
저장소, 목적), "결정 사항", "진행 중: v0.1 최초 골격"(3단계 체크리스트를 세부
step으로), "미확정 사항"만 채우고, "다음 버전 (계획)"과 "완료"는 빈 절로 둔다.

## 2단계: 스택 확인 및 공식 문서 가이드

사용할 라이브러리/프레임워크를 사용자에게 질문한다. 답변을 받으면
WebSearch/WebFetch로 해당 스택의 **최신 공식 Get Started 문서**를 찾아
안내한다. 이 문서를 그대로 따라가며 기본 설정을 사용자가 직접 진행하도록
안내하고, 코드나 설정 파일을 대신 생성하지 않는다.

grill me로 확정된 결정과 미확정 사항은 `docs/<name>-todo.md`에 누적한다.
시행착오 이력(검토했다가 버린 대안, 중간 질문)은 기록하지 않고 **최종
결정 사항만** 남긴다.

## 3단계: 사용자가 직접 진행 (대기)

사용자가 아래를 직접 완료한다.

- `projects/<name>/`에 로컬 프로젝트 생성 (공식 문서 기준)
- CHANGELOG 생성기 설정 (`docs/ssot/repo-architecture.md` "버전·변경 이력"):
  라이브러리는 `changeset init`, 앱은 `git cliff --init` 으로 `cliff.toml` 생성
- Slack 채널 생성 및 봇 초대
- first commit
- 원격 저장소로 push

완료 확인을 받기 전까지 다음 단계로 진행하지 않는다.

## 4단계: 완료 확인 후 로컬 스캐폴딩

사용자가 완료를 알리면, `projects/<name>/`에 아래를 추가한다.

- `CLAUDE.md`에 SSOT 참조 3줄 추가
  ```
  @../../CLAUDE.md
  @../../docs/ssot/org-principles.md
  @../../docs/ssot/repo-architecture.md
  ```
- `CLAUDE.md`에 프로젝트 고유 규칙(스택, 구조, 도메인 규칙)을 기술한다.
  todo 성격의 내용(미확정 사항, 다음 작업, 진행 상황)은 CLAUDE.md에 두지 않고
  `docs/<name>-todo.md`에 둔다. 대신 CLAUDE.md에 아래 절을 추가한다.
  ```
  ## todo 관리
  작업이 진행되면 루트 `../../docs/<name>-todo.md`를 실시간으로 갱신한다.
  구조와 릴리스 시 처리는 `../../docs/TODO.md`의 "프로젝트 todo 파일" 절을 따른다.
  시행착오는 기록하지 않고 최종 결정만 남긴다.
  ```
- `.claude/settings.json`을 아래 내용만으로 생성한다. 루트 `docs/`를
  프로젝트 세션에 열어 todo 갱신과 SSOT 읽기를 허용하기 위해서다.
  permission deny 규칙은 두지 않는다
  (`docs/ssot/decisions/0003-no-explicit-permission-deny.md`,
  `docs/ssot/decisions/0004-todo-two-scopes-in-one-file.md`).
  ```json
  {
    "permissions": {
      "additionalDirectories": ["../../docs"]
    }
  }
  ```

## 5단계: 루트 색인·SSOT·브릿지 갱신

동시에 아래를 갱신한다 (필요한 항목만, 없으면 생략).

- `docs/<name>-todo.md`: "진행 중: v0.1 최초 골격" 절의 핵심 기능과 세부
  step을 확정하고, 미확정 사항을 정리한다
- `docs/PROJECTS.md`: 신규 행 추가, 상태 "구축중"
- `CLAUDE.md`의 "프로젝트 색인" 표: 요약 반영
- `tools/slack-worker/channels.local.json`에 `{채널ID: "<name>"}` 추가
  (이 파일은 로컬 전용이라 git에는 없다 — `docs/ssot/decisions/0002-channel-project-mapping-local-only.md`
  참고. 채널 ID를 모르면, 매핑 없이 해당 채널에서 아무 멘션이나 한 번
  시켜 보면 브릿지가 채널 ID를 회신해준다)
- 이번 결정으로 SSOT 원칙 자체가 바뀌면 `docs/ssot/decisions/`에 ADR 추가
  (사용자 승인 후)

## 완료 보고

무엇을 만들었는지, 무엇을 갱신했는지 간결히 요약하고 끝맺는다.
