# ADR 0003: 프로젝트 격리에 명시적 permission deny를 쓰지 않는다

## 상태
승인됨 (2026-09-22)

## 배경
`repo-architecture.md`는 프로젝트 `.claude/settings.json`에
`{"permissions": {"deny": ["Edit(../**)", "Write(../**)"]}}`를 두어
프로젝트 밖 수정을 막도록 규정했다. 한편 `docs/<name>-todo.md`(프로젝트별
todo 파일)를 루트에 두고 프로젝트 세션이 갱신하기로 결정하면서, 상위
디렉터리 쓰기가 의도된 동작이 되었다.

## 검증 결과 (헤드리스 세션으로 확인)
- `Write(../**)`는 무효다. Claude Code가 시작 시 "Write(../**) is not matched
  by file permission checks — only Edit(path) rules are"라고 경고한다.
- `Edit(../**)`도 상위 디렉터리를 막지 못한다. 상대 경로 규칙은 현재
  디렉터리 아래만 매칭한다("A rule only matches files under its anchor").
  `--add-dir`로 접근 권한을 준 뒤 `../../docs/` 아래 파일을 Edit하자
  차단되지 않았다.
- `!` 부정 패턴은 디렉터리 전체를 막은 규칙에서 내부 파일 하나를
  다시 열 수 없다.

즉 실제 격리는 deny 규칙이 아니라 "작업 디렉터리 밖은 승인 필요"라는
Claude Code 기본 동작이 담당하고 있었다.

## 결정
- 프로젝트 `.claude/settings.json`에 permission deny 블록을 두지 않는다.
  `new-project` 스킬도 이 파일을 생성하지 않는다.
- 프로젝트 밖 수정 방지는 작업 디렉터리 경계에 맡긴다.
- 루트 `docs/<name>-todo.md` 갱신은 필요 시 세션에서 승인하는 방식으로
  허용한다.

## 영향받는 문서
- `docs/ssot/repo-architecture.md`: "프로젝트 격리 규칙" 절을 "프로젝트 격리"로 개정
- `.claude/skills/new-project/SKILL.md`: 4단계에서 settings.json 생성 단계 제거
- `projects/common-design/.claude/settings.json`: 삭제
