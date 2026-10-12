# dev-env

로컬 dev 서버와 에뮬레이터를 launchd LaunchAgent로 관리하는 기기 단위 운영 도구다.
Slack 워커가 메시지마다 실행하는 `claude -p`는 길어야 600초 만에 끝나므로, 서버를
Claude 세션 안에서 띄우면 세션과 함께 정리되거나 출력 파이프를 붙잡아 응답이
타임아웃된다. 그래서 서버의 수명은 launchd가 맡고, 세션은 `devctl`로 상태 확인과
재시작만 한다.

## 원칙

- **dev 서버는 launchd만 관리한다.** Claude 세션은 `pnpm dev`, `next dev`, `nohup ... &`
  등으로 서버를 직접 띄우지 않고 `devctl`을 쓴다.
- **`KeepAlive` 서버를 `kill`로 종료하지 않는다.** launchd가 즉시 다시 띄운다. 정지는
  `devctl down`, 영구 정지는 `devctl uninstall`이다.
- `KeepAlive`는 `servers`에만 켠다. 에뮬레이터 같은 `tasks`는 필요할 때 `devctl up`으로
  띄운다.

## 자주 쓰는 명령

```bash
tools/dev-env/devctl ls                 # 등록 항목, 적재 여부, PID, 포트 LISTEN 여부
tools/dev-env/devctl ports              # 등록 포트의 점유 주체, 레지스트리 내부 중복
tools/dev-env/devctl logs <name> [-f]   # state/logs/<name>.log (기본 100줄)
tools/dev-env/devctl restart <name>     # 재시작 (launchctl kickstart -k)
tools/dev-env/devctl up <name>          # 시작. plist가 없으면 install까지 한다
tools/dev-env/devctl down <name>        # 정지 (적재 해제, plist 유지)
tools/dev-env/devctl install [name..]   # plist 생성 후 적재. 이름 생략 시 전체
tools/dev-env/devctl uninstall [name..] # 적재 해제 후 plist 삭제
tools/dev-env/devctl reverse            # 실행 중인 서버 포트 전체에 adb reverse
```

| 명령 | 서버(`servers`) | 작업(`tasks`) |
|---|---|---|
| `install` | 적재와 동시에 시작 (`RunAtLoad`) | 정지 상태로 적재 |
| `down` | 정지. plist가 남아 있으므로 다음 로그인 때 다시 시작 | 정지 |
| 프로세스가 죽으면 | launchd가 재시작 (`ThrottleInterval` 30초) | 재시작하지 않음 |

`up`과 `install`은 등록 포트가 외부 프로세스에 점유되어 있으면 시작을 거부한다.

## 레지스트리

`registry.json`이 서버·작업 목록과 포트의 정본이다. plist는 기기마다 절대 경로가
달라 커밋하지 않고 `devctl install`이 `~/Library/LaunchAgents/com.fabrics.dev.<name>.plist`로
생성한다.

```json
{
  "servers": {
    "<name>": {
      "dir": "저장소 루트 기준 작업 디렉터리",
      "command": ["실행 파일", "인자", "..."],
      "ports": [3000],
      "env": { "KEY": "value" }
    }
  },
  "tasks": { "<name>": { "dir": "...", "command": ["..."], "env": {} } }
}
```

- `command[0]`에 `/`가 없으면 아래 PATH에서 찾고, 있으면 `dir` 기준 상대 경로로 해석한다
- launchd는 로그인 셸의 PATH를 상속하지 않는다. plist에는 `/opt/homebrew/bin`,
  `/usr/local/bin`, 시스템 경로, Android SDK의 `platform-tools`·`emulator`가 들어간다
- plist가 주입하는 공통 env: `PATH`, `ANDROID_HOME`, `DEVCTL`(이 CLI의 경로)
- 기기별로 값을 바꿀 때는 `registry.local.json`(gitignore 대상)에 같은 구조로 쓴다.
  항목 단위로 덮어쓴다
- 레지스트리를 고친 뒤에는 `devctl install <name>`으로 plist를 다시 만든다

## 포트 할당

웹서비스마다 10개 단위 블록을 할당한다. Multi-Zones처럼 포트를 여러 개 쓰는 서비스가
서로 침범하지 않게 하고, 모든 dev 서버를 동시에 띄울 수 있게 하기 위해서다. 현재 할당은
`registry.json`과 `devctl ports`가 정본이다.

| 블록 | 서비스 |
|---|---|
| 3000–3009 | stylist-web |
| 3010–3019 | 다음 서비스 |

- pocket이 어느 서비스를 띄울지는 pocket의 Debug 시작 URL(Android flavor, iOS xcconfig)로
  고른다. 다른 서비스를 탑재하려고 3000을 비울 필요가 없다
- 그래도 포트를 옮겨야 하면 두 서비스의 `ports`와 `env`를 고치고 `devctl install`을
  다시 실행한다. 프로젝트가 env로 포트를 받아야 한다. stylist-web은 현재
  `package.json`에 포트가 고정되어 있으므로, 옮길 때 stylist-web 쪽에서 env 수신을 추가한다

## 서버 추가 절차

1. 포트 블록을 고른다
2. `registry.json`의 `servers`에 항목을 추가한다. `command`는 TTY 없이 동작해야 한다
   (turbo는 `--ui=stream`)
3. `devctl install <name>` 후 `devctl ls`, `devctl logs <name>`으로 확인한다

## 에뮬레이터·시뮬레이터

### Android (`android-emulator` 작업)

```bash
tools/dev-env/devctl up android-emulator   # headless 기동, 부팅 완료 후 devctl reverse 자동 실행
tools/dev-env/devctl logs android-emulator
tools/dev-env/devctl down android-emulator
```

- AVD 이름과 포트는 레지스트리 `env`의 `ANDROID_AVD`, `EMULATOR_PORT`다. 시리얼은
  `emulator-<EMULATOR_PORT>`다
- 화면 확인: `adb -s emulator-5554 exec-out screencap -p > shot.png`
- `adb reverse`는 에뮬레이터를 재부팅하면 사라진다. 서버를 나중에 띄웠다면
  `devctl reverse`를 다시 실행한다
- WebView 버전 확인: `adb shell dumpsys webviewupdate | grep "Current WebView"`.
  safe area 계약은 M144 이상을 요구한다(`docs/architecture/app-pocket-webview-layout.md`)

### iOS 시뮬레이터

CoreSimulator가 부팅 상태를 유지하므로 별도 작업으로 등록하지 않는다. 시뮬레이터는
호스트와 네트워크를 공유하므로 `localhost`가 그대로 서버에 닿는다.

```bash
xcrun simctl list devices booted
xcrun simctl boot "<기기 이름 또는 UDID>"
xcrun simctl install booted <App.app>
xcrun simctl launch booted <bundle id>
xcrun simctl io booted screenshot shot.png
```

## 수동 복구 (재부팅·로그아웃 후)

FileVault가 켜져 있으므로 재부팅하면 로그인 전까지 아무 agent도 실행되지 않는다.
무인 복구는 하지 않는다.

1. 로그인한다. slack-worker와 `servers` 항목은 `RunAtLoad`로 자동 기동된다
2. `tools/dev-env/devctl ls`로 서버가 `running`이고 포트가 `✓`인지 확인한다
3. 필요하면 `devctl up android-emulator`를 실행한다

## 문제 해결

| 증상 | 확인과 조치 |
|---|---|
| `STATE`가 `running`인데 포트가 `✗` | 기동 중이거나 서버가 오류로 멈췄다. `devctl logs <name>` |
| PID가 계속 바뀐다 | 크래시 루프다. `devctl logs <name>`으로 원인을 보고, 고칠 때까지 `devctl down <name>` |
| `up`이 포트 점유로 거부된다 | `devctl ports`에서 `← 외부 프로세스` 행의 pid를 확인해 정리한다 |
| `devctl` 자체가 동작하지 않는다 | `launchctl print gui/$(id -u)/com.fabrics.dev.<name>`, `lsof -nP -iTCP -sTCP:LISTEN`, 정지는 `launchctl bootout gui/$(id -u)/com.fabrics.dev.<name>` |
| 로그의 `Failed to replace env in config: ${GITHUB_TOKEN_PKG}` | `.npmrc`의 토큰 변수가 launchd 환경에 없다는 경고다. dev 서버 실행에는 영향이 없다. 패키지 설치는 로그인 셸에서 한다 |

## 파일 구성

- `devctl`: 관리 CLI (Python 표준 라이브러리만 사용)
- `registry.json`: 서버·작업 목록 정본
- `registry.local.json`: 기기별 덮어쓰기 (선택, 커밋 제외)
- `scripts/android-emulator.sh`: headless 에뮬레이터 기동과 `adb reverse`
- `state/logs/`: 항목별 로그 (커밋 제외)
