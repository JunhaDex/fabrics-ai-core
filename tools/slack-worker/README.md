# slack-worker

Slack 멘션으로 Claude Code를 원격 트리거하는 조직 도구(org tooling).
배경과 이 위치에 있는 이유는 `docs/ssot/decisions/0001-org-tooling-in-control-repo.md` 참고.

## 세팅 순서

1. Slack App 생성
2. `.env` 작성 (토큰)
3. `channels.local.json` 작성 (채널 ↔ 프로젝트 매핑)
4. 수동 실행으로 동작 확인
5. launchd로 24시간 상시 구동

---

## 1. Slack App 생성

1. api.slack.com/apps → "Create New App" → "From scratch"
2. 좌측 메뉴 "Socket Mode" → 활성화. 이때 App-Level Token 생성 팝업이 뜨면
   `connections:write` 스코프로 생성 → `xapp-...` 값을 이후 `.env`의
   `SLACK_APP_TOKEN`으로 쓴다.
3. 좌측 메뉴 "OAuth & Permissions" → Bot Token Scopes에 추가
   - `app_mentions:read`
   - `chat:write`
   - `channels:history` (공개 채널) 또는 `groups:history` (비공개 채널)
     — 스레드 내 무멘션 후속 메시지 인식에 필요
   - `reactions:write` — 질문 메시지에 처리 중 반응(`:loading:`)을 달고
     답변 후 제거하는 데 필요
4. 좌측 메뉴 "Event Subscriptions" → 활성화 → Subscribe to bot events에 추가
   - `app_mention`
   - `message.channels` (또는 `message.groups`)
5. "Install App" → 워크스페이스에 설치 → `xoxb-...` Bot User OAuth Token을
   `.env`의 `SLACK_BOT_TOKEN`으로 쓴다.
6. 프로젝트 전용 채널을 만들고 `/invite @<봇이름>`으로 초대한다.
7. 워크스페이스 설정 → Customize → Emoji에서 `assets/loading.gif`를 이름
   `loading`으로 등록한다. 다른 이름을 쓰려면 `.env`의
   `SLACK_LOADING_EMOJI`로 지정한다.

## 2. `.env` 작성

`tools/slack-worker/.env`
```
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_LOADING_EMOJI=loading
```
루트 `.gitignore`로 커밋 제외된다. `.env.example`(빈 값)을 복사해 1번에서
발급받은 값을 채운다. `SLACK_LOADING_EMOJI`는 선택값으로, 생략하면
`loading`을 사용한다.

## 3. `channels.local.json` 작성

`channels.example.json`을 참고해 실제 채널 ID를 매핑한다. 채널 ID를
모르면, 매핑 없이 해당 채널에서 아무 멘션이나 한 번 하면 브릿지가
채널 ID를 알려주는 메시지로 회신한다.

```json
{
  "C0XXXXXXXXX": "sandbox-test"
}
```

## 4. 수동 실행으로 확인

```bash
python3 tools/slack-worker/worker.py
```
등록한 채널에서 `@<봇이름>`으로 멘션해 응답이 오는지 확인한다. 확인되면
`Ctrl+C`로 종료하고 5번(launchd)으로 넘어간다.

## 5. launchd로 24시간 상시 구동

### 5-1. plist 작성

`~/Library/LaunchAgents/com.fabrics.slack-worker.plist`를 아래 내용으로
만든다. 경로(`/Users/dex/...`)는 실제 환경에 맞게, `python3`/`claude`
경로는 `which python3` / `which claude`로 확인한 값으로 바꾼다.

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.fabrics.slack-worker</string>

    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/caffeinate</string>
        <string>-s</string>
        <string>/usr/local/bin/python3</string>
        <string>/Users/dex/Developer/professional/0_pjt_fabrics/tools/slack-worker/worker.py</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/dex/Developer/professional/0_pjt_fabrics/tools/slack-worker</string>

    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin</string>
    </dict>

    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>

    <key>StandardOutPath</key>
    <string>/Users/dex/Developer/professional/0_pjt_fabrics/tools/slack-worker/state/worker.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/dex/Developer/professional/0_pjt_fabrics/tools/slack-worker/state/worker.err.log</string>
</dict>
</plist>
```

launchd는 로그인 셸의 `PATH`(`.zshrc` 등)를 상속받지 않는다. 그래서
`EnvironmentVariables`의 `PATH`에 `claude`/`python3`가 있는 디렉터리를
직접 넣어줘야 한다. `WorkingDirectory`를 이 디렉터리로 지정해야
`python-dotenv`가 `.env`를 찾는다.

### 5-2. caffeinate가 하는 일

`ProgramArguments`에서 `worker.py`를 `caffeinate -s`로 감싸 실행한다.
`-s`는 "시스템이 슬립 모드로 들어가는 것을 막는" macOS 기본 내장
유틸리티(`/usr/bin/caffeinate`, Apple 서명)다. 별도 설치가 필요 없다.
Mac이 절전 모드로 들어가면 Socket Mode 연결이 끊기므로, `worker.py`가
살아있는 동안만 절전을 막는 용도로 붙였다.

### 5-3. 등록 및 실행

```bash
plutil -lint ~/Library/LaunchAgents/com.fabrics.slack-worker.plist  # 문법 검증
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.fabrics.slack-worker.plist
launchctl kickstart -k gui/$(id -u)/com.fabrics.slack-worker  # 즉시 시작
```

### 5-4. 상태 확인 / 중지

```bash
# 상태 확인
launchctl list | grep fabrics
launchctl print "gui/$(id -u)/com.fabrics.slack-worker"

# 완전히 중지 (재부팅해도 다시 안 뜸)
launchctl bootout gui/$(id -u)/com.fabrics.slack-worker
rm ~/Library/LaunchAgents/com.fabrics.slack-worker.plist
```

화면 잠금 상태에서는 계속 동작한다(로그인 세션 자체는 유지되므로).
완전 로그아웃하거나 재부팅 후 아무도 로그인하지 않으면 멈춘다 —
자동 로그인 설정 여부는 보안 트레이드오프가 있어 별도로 직접 결정한다.

## 파일 구성

- `worker.py` — 본 워커. Slack `app_mention`/`message` 이벤트를 받아
  `claude -p`를 서브프로세스로 실행하고 결과를 스레드에 회신한다.
- `state/threads.json` — `{thread_ts: {session_id, project}}` 매핑
  (런타임 상태, `.gitignore`의 `tools/slack-worker/state/`로 커밋 제외됨)
- `assets/loading.gif` — 처리 중 반응용 커스텀 이모지 원본. 1단계 7번에서
  워크스페이스에 등록한다.
