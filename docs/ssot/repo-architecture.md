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
- `docs/PROJECTS.md`

비공개(private) 원격 저장소(GitHub/GitLab 등)에 두고, 각 로컬 기기에서 동일
경로(`0_pjt_fabrics/`)로 clone한다.

### 2. 프로젝트 저장소 (독립)
`projects/<name>/`은 각각 별도의 git 저장소다. 메타 저장소의 하위 디렉터리처럼
보이지만, 메타 저장소의 git 히스토리에는 포함되지 않는다(`.gitignore`로 제외).
- 프로젝트가 시작되면, 별도 원격 저장소를 만들고 `projects/<name>/`에 clone한다.
- `docs/PROJECTS.md`에 저장소 URL을 기록해, 다른 기기에서도 어떤 프로젝트를
  어디서 clone해야 하는지 알 수 있게 한다.

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

자동화 스크립트로 만들 수도 있지만, 프로젝트마다 상황이 달라 지금은 수동
체크리스트로 유지한다. 필요성이 명확해지면 그때 스크립트화를 검토한다.

## .gitignore 핵심
```
projects/*
!projects/.gitkeep
.claude/settings.local.json
.DS_Store
```

## 민감정보 처리
`~/.claude/`(사용자 전역 설정, 인증 토큰)는 메타 저장소에 절대 포함하지 않는다.
메타 저장소가 다루는 것은 비밀이 아닌 루트/프로젝트 범위의
`.claude/settings.json`(권한 규칙 등)뿐이다.
