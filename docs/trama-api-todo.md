# trama-api todo

저장소: (미정) `fabrics-trama-api` · 로컬: `projects/trama-api/`
Slack: (미정)
목적: trama 문서의 원본을 소유하고, 편집기(WebSocket)와 AI(MCP)의 모든 변경을 검증·적용·동기화하는 서버
요구사항 명세: `docs/references/fabrics-tala-requirements.md`

## 결정 사항

### 프로젝트 경계
- trama-web과 별도 프로젝트다. 저장소, Slack 채널, todo 파일을 따로 둔다(2026-11-03)
- 편집기는 trama-web이 맡는다. web 쪽 결정은 `docs/trama-web-todo.md`에 있다
- 서버는 BFF가 아니라 문서의 원본을 소유하는 도메인 서버다. 검증, 순서 부여, 충돌 해소, 연산 로그를 직접 수행한다
- 인증은 아직 다루지 않는다. 참여자는 `actor`를 스스로 밝힌다

### 스택
- Kotlin·Spring Boot다(2026-11-02 확정). auth-api와 스택을 맞춘다(Java 21, Gradle Kotlin DSL, PostgreSQL, Flyway, Testcontainers)
- MCP는 Spring AI MCP Server(MCP Java SDK 기반, Streamable HTTP), 헤드리스 렌더는 Playwright for Java다.
  Spring AI의 MCP 전송 방식은 버전마다 바뀌어 왔으므로 해당 버전 착수 시 버전을 고정한다
- 앱이므로 CHANGELOG 생성기는 git-cliff다

### 계약
- 문서 모델, 연산, 오류 코드: `docs/architecture/trama-document-model.md`. 서버는 `apply_ops` 검증·적용을 Kotlin으로
  구현하고, `trama-ops.schema.json`과 `trama-ops-conformance/`를 모두 통과해 web 구현과의 일치를 보장한다
- HTML 변환: 서버는 변환기를 다시 구현하지 않는다. 헤드리스 Chromium에서 web의 `render.js`를 불러 `annotated` 출력과
  `inspect`를 만든다(하나의 렌더 경로)
- 서버 인터페이스: `docs/architecture/trama-server-interface.md`(2026-11-03 초안)
  - 편집기 쓰기는 WebSocket으로만 받고, 브로드캐스트는 서버가 적용한 `changes`(`[{ id, key, value }]`)로 보낸다
  - 스냅샷 복원과 변경 기록 되돌리기는 새 트랜잭션으로 적용한다. 되돌리기는 작성자와 무관하게 허용한다
  - AI 세션 스냅샷은 세션이 한 문서에 처음 `apply_ops`를 호출하기 직전에 남긴다. AI용 Undo 도구는 두지 않는다

## 진행 중: v0.1 최초 골격
- 컨텍스트: 저장소와 Spring Boot 골격을 만들고 프로젝트 세션을 시작할 수 있게 한다
- 핵심 기능 (모두 완료되면 릴리스):
  - [ ] Spring Boot 프로젝트 골격과 로컬 실행
  - [ ] 프로젝트 `CLAUDE.md`, `.claude/settings.json`, 색인 등록
- 세부 step:
  - [ ] GitHub 비공개 저장소 `fabrics-trama-api` 생성
  - [ ] Spring Initializr로 `projects/trama-api/`에 프로젝트 생성
  - [ ] `git cliff --init keepachangelog`로 `cliff.toml` 생성
  - [ ] Slack 채널 생성과 봇 초대
  - [ ] first commit, push
  - [ ] 프로젝트 `CLAUDE.md`·`.claude/settings.json` 스캐폴딩, `docs/PROJECTS.md`·루트 `CLAUDE.md` 색인, Slack 매핑
- 다음 행동: 사용자가 저장소 생성부터 push까지 진행

## 다음 버전 (계획)
- `apply_ops` 검증·적용(Kotlin). 적합성 fixture 전부 통과
- PostgreSQL 저장(노드 속성 테이블, 연산 로그)과 문서 REST
- WebSocket 동기화(순서 부여, 속성 단위 LWW, fractional index 계산, Undo·Redo·revert·restore, presence)
- Playwright 헤드리스 렌더와 `inspect`(web `render.js` v0.7 필요)
- MCP 도구(`list_documents`, `get_tree`, `get_tokens`, `get_components`, `inspect`, `apply_ops`)와 AI 세션 스냅샷

## 완료

## 미확정 사항
- DB 접근 방식: 평면 속성 맵과 추가 전용 연산 로그 구조라 JPA 대신 JDBC 계열(Spring JDBC 또는 jOOQ)을 검토
- 로컬 dev 서버 운영: `tools/dev-env` 등록 여부, 포트, PostgreSQL을 `compose.yaml`로 띄울지
- 인증: 도입 시점과 auth-api 연동 방식
- infra(terraform): 별도 프로젝트 여부와 배포 대상
- 버전 번호: trama-web과 독립으로 `0.1.0`부터 시작하는 것으로 전제했다. 확인 필요
