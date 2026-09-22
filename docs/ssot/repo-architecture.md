# 저장소 아키텍처 (SSOT)

## 배경
하나의 git 저장소에 모든 프로젝트를 담으면(모노레포) 프로젝트 수가 늘어날수록
저장소가 비대해지고, clone/체크아웃 비용이 커지며, 프로젝트별로 다른 CI/CD,
접근 권한, 배포 주기를 관리하기 어려워진다. 반면 `0_pjt_fabrics` 루트 자체
(CLAUDE.md, .claude 설정, SSOT 문서, 프로젝트 색인)는 여러 로컬 기기에서
동일하게 유지·동기화되어야 한다. 이 문서는 두 요구를 분리해서 만족시키는
구조를 정의한다.

## 구조

### 1. 메타 저장소 (control repo)
`0_pjt_fabrics/` 자체가 하나의 작고 독립적인 git 저장소다. 여기에는 다음만 포함한다.
- `CLAUDE.md`, `.claude/`
- `docs/ssot/*`
- `docs/PROJECTS.md`, `docs/TODO.md`, `docs/<name>-todo.md` (프로젝트별 todo 파일)

비공개(private) 원격 저장소(GitHub/GitLab 등)에 두고, 각 로컬 기기에서 동일
경로(`0_pjt_fabrics/`)로 clone한다.

### 2. 프로젝트 저장소 (독립)
`projects/<name>/`은 각각 별도의 git 저장소다. 메타 저장소의 하위 디렉터리처럼
보이지만, 메타 저장소의 git 히스토리에는 포함되지 않는다(`.gitignore`로 제외).
- 프로젝트가 시작되면, 별도 원격 저장소를 만들고 `projects/<name>/`에 clone한다.
- `docs/PROJECTS.md`에 저장소 URL을 기록해, 다른 기기에서도 어떤 프로젝트를
  어디서 clone해야 하는지 알 수 있게 한다.

#### 프로젝트 CLAUDE.md 필수 구성
루트 CLAUDE.md의 "조직 공통 원칙"이 말하는 "상속"은 문서로만 안내하는 것이
아니라, 프로젝트 자체 `CLAUDE.md`에 아래 3줄을 실제로 추가해 Claude Code가
런타임에 로드하도록 만드는 것을 뜻한다.
```
@../../CLAUDE.md
@../../docs/ssot/org-principles.md
@../../docs/ssot/repo-architecture.md
```
이렇게 하면 별도 승인 절차 없이(헤드리스 모드 기준 확인됨) 조직 원칙이
항상 컨텍스트에 포함된다.

#### 프로젝트 격리
프로젝트 세션이 프로젝트 밖(다른 프로젝트, SSOT 문서 등)을 수정하는 것은
Claude Code의 **작업 디렉터리 경계**가 막는다(작업 디렉터리 밖 파일은 별도
승인 없이는 읽기·쓰기가 되지 않는다). 프로젝트 `.claude/settings.json`에
명시적인 permission deny 규칙은 두지 않는다. 상대 경로 deny 패턴은 상위
디렉터리를 매칭하지 못해 실효가 없기 때문이다. 결정 근거는
`docs/ssot/decisions/0003-no-explicit-permission-deny.md` 참고.

예외로 루트 `docs/`는 프로젝트 세션에 열어 둔다. 프로젝트 세션이
`docs/<name>-todo.md`를 실시간으로 갱신하고 SSOT 문서를 컨텍스트로 읽을 수
있어야 하기 때문이다. 프로젝트 `.claude/settings.json`은 아래 내용만 담는다.
```json
{
  "permissions": {
    "additionalDirectories": ["../../docs"]
  }
}
```
상대 경로는 프로젝트 루트 기준으로 해석된다(헤드리스 세션으로 확인됨).
이 설정은 워크스페이스를 trust한 뒤에만 적용되므로, 새 기기에서는 해당
프로젝트에서 대화형 세션을 한 번 열어 trust 대화상자를 수락해야 한다.
결정 근거는 `docs/ssot/decisions/0004-todo-two-scopes-in-one-file.md` 참고.

프로젝트 CLAUDE.md의 `@import` 구성은 `.claude/skills/new-project/SKILL.md`의
스캐폴딩 단계에서 자동으로 반영된다.

#### 버전·변경 이력
프로젝트 저장소의 진행 상황은 README나 프로젝트 내부 `docs/`로 관리하지
않는다. README는 사용법 안내가 목적이고, 진행 상황과 이력은 루트
`docs/<name>-todo.md`(`docs/TODO.md` "프로젝트 todo 파일" 절)와 아래 규칙으로
생성되는 `CHANGELOG.md`가 담당한다.

- **버전 단위 개발**: 라이브러리와 앱 모두 기능을 버전으로 나눈다. 새 feature에
  착수할 때 핵심 기능을 정의하고, 핵심 기능이 모두 완성되면 릴리스한다.
- **버전 번호**: [Semantic Versioning 2.0.0](https://semver.org). 초기 개발은
  `0.y.z`로 시작해 feature 릴리스마다 minor, 수정만 있으면 patch를 올린다.
  `1.0.0`은 외부에 공개 API·동작을 보장할 수 있을 때 사용자가 판단한다.
  태그는 `vX.Y.Z`.
- **브랜치와 병합**: 브랜치는 자유롭게 분기한다. 해당 버전의 기능이 완성되면
  PR을 열고 **squash merge**한다. main에는 feature당 커밋 하나만 남으므로
  `git log --first-parent --oneline`이 feature 목록이 된다.
- **PR 제목**: [Conventional Commits 1.0.0](https://www.conventionalcommits.org)
  형식(`feat: ...`, `fix: ...`, `chore: ...`, `refactor: ...`)으로 쓴다.
  squash 커밋 제목이 PR 제목이 되고, CHANGELOG 생성기가 이 형식을 읽는다.
- **CHANGELOG.md**: [Keep a Changelog 1.1.0](https://keepachangelog.com)
  형식(역순, `Unreleased` 절, Added/Changed/Fixed 등 분류)으로 저장소 루트에
  둔다. 손으로 쓰지 않고 릴리스 시 생성한다.
  - 라이브러리(npm 패키지): changesets. `.changeset/*.md`가 `changeset version`
    으로 CHANGELOG에 병합된다.
  - 앱: [git-cliff](https://git-cliff.org). 저장소 루트 `cliff.toml` 하나만
    추가하고, 릴리스 시 `git cliff --tag vX.Y.Z -o CHANGELOG.md`를 실행해
    태그와 함께 커밋한다.
- **릴리스 절차**: `docs/TODO.md`의 "릴리스 시 처리 순서"를 따른다.
  CHANGELOG 생성과 태그 이후, 루트 `docs/<name>-todo.md`의 "진행 중" 절을
  "완료" 절로 옮긴다.

### 3. 조직 도구 (org tooling)
fabrics 업무 산출물이 아니라, 메타 저장소 자체의 운영을 보조하는 도구
(예: `slack-worker`)는 `tools/<name>/` 경로에 두고 메타 저장소의 git
히스토리에 직접 포함한다. `projects/<name>/`과 달리 독립 저장소로 분리하지
않는다. 결정 근거는 `docs/ssot/decisions/0001-org-tooling-in-control-repo.md`
참고. 토큰/API 키 등 민감 정보는 `.env`(아래 `.gitignore` 핵심의 패턴으로
보호됨) 또는 `secrets/`에 두고, 실제 값 대신 `.env.example`만 커밋한다.

### 왜 git submodule을 쓰지 않는가
submodule은 커밋 해시를 고정(pin)하는 방식이라 "정확한 버전이 고정된 라이브러리
의존성"에 적합하다. 프로젝트 간 버전 고정이 필요 없는 이 구조에서는 detached
HEAD, 동기화 실수 같은 submodule 특유의 마찰만 늘어난다. 대신
`docs/PROJECTS.md`를 가벼운 매니페스트(저장소 URL 목록)로 사용한다.

## 기기 간 동기화

### 메타 저장소
- 일반적인 `git pull`/`git push`로 동기화한다.
- 세션 시작 전 `git pull`, 의미 있는 변경(원칙 수정, 프로젝트 색인 갱신) 후에는
  즉시 `git push`하는 것을 습관화한다.
- 현재는 1인 다기기 사용이므로 메인 브랜치 직접 push로 충분하다. 협업자가
  늘어나면 PR 리뷰 흐름으로 전환한다.

### 프로젝트 저장소
- 기기마다 필요한 프로젝트만 선택적으로 clone한다. 모든 기기가 모든 프로젝트를
  가질 필요는 없다.

## 새 기기 부트스트랩 (수동 체크리스트)
1. 메타 저장소를 clone한다: `git clone <control-repo-url> 0_pjt_fabrics`
2. `docs/PROJECTS.md`를 읽고, 이 기기에서 작업할 프로젝트를 선택한다.
3. 선택한 프로젝트만 `projects/<name>/`에 개별 clone한다.
4. 루트에서 Claude Code를 실행해 `CLAUDE.md`가 정상적으로 로드되는지 확인한다.
5. `tools/slack-worker`를 쓰는 경우, `tools/slack-worker/README.md`를 따라
   로컬 전용 파일(`.env`, `channels.local.json`)을 채운다.
6. 사용자 전역 스킬을 설치한다. `~/.claude/skills/`는 git으로 동기화되지
   않으므로 기기마다 수행한다. Python 3.x가 필요하다.
   ```
   npx ui-ux-pro-max-cli@latest init --ai claude --global
   rm -r ~/.claude/skills/design ~/.claude/skills/banner-design
   ```
   `design`과 `banner-design`은 Gemini API 키와 미포함 스킬(`ai-artist`,
   `ai-multimodal`)에 의존해 동작하지 않으므로 설치 직후 삭제한다.
   `uipro update --global`로 갱신하면 두 폴더가 복원되므로 삭제를 반복한다.
   ```
   npx skills@latest add emilkowalski/skills -g -a claude-code -s '*' -y
   npx skills@latest remove animate-expo write-swift ask-sonner pick-ui-library -g -y
   ```
   emilkowalski/skills(애니메이션·UI 판단 기준)는 skills.sh CLI로 설치하며,
   갱신은 `npx skills@latest update -g`로 한다. `animate-expo`(React Native),
   `write-swift`(Swift), `ask-sonner`(Sonner 토스트), `pick-ui-library`(외부
   라이브러리 추천)는 fabrics 스택과 무관하거나 필요성이 낮아 제외한다.
   ```
   npx skills@latest add nutlope/hallmark -g -a claude-code -y
   ```
   nutlope/hallmark(Together AI 제작 anti-AI-slop 디자인 스킬. 21개 테마,
   `audit`/`redesign`/`study` 동사)도 같은 CLI로 설치한다. 실행 시 프로젝트에
   `.hallmark/log.json`(테마·구조 다양화 이력)을 생성할 수 있다.

자동화 스크립트로 만들 수도 있지만, 프로젝트마다 상황이 달라 지금은 수동
체크리스트로 유지한다. 필요성이 명확해지면 그때 스크립트화를 검토한다.

## .gitignore 핵심
```
projects/*
!projects/.gitkeep
.claude/settings.local.json
.DS_Store
*.local.json
tools/slack-worker/state/
```

## 민감정보 처리
`~/.claude/`(사용자 전역 설정, 인증 토큰)는 메타 저장소에 절대 포함하지 않는다.
메타 저장소가 다루는 것은 비밀이 아닌 루트/프로젝트 범위의
`.claude/settings.json`(권한 규칙 등)뿐이다.
