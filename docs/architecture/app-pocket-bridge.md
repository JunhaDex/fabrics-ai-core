# app-pocket 브릿지 계약 (잠정)

웹앱과 네이티브(Android, iOS)가 주고받는 브릿지의 현행 명세다. 두 플랫폼
구현체는 이 문서를 그대로 따른다. 결정의 근거는 `../app-pocket-todo.md`의
"결정 사항"에 있고, 이 문서는 지켜야 할 내용만 서술한다.

- 상태: v0.1 잠정안. 네이티브 구현이 계약을 안정시키면 `app-bridge`
  (`../app-bridge-todo.md`)로 이관한다
- 이 문서의 계약이 바뀌면 런타임 버전 규칙을 따른다. 메서드·이벤트·코드를
  추가하면 MINOR, 이름을 바꾸거나 제거하면 MAJOR이며, 제거 전 최소 한 MAJOR
  주기 동안 폐기 예고를 유지한다

## 1. 노출 원칙

- **공통 래퍼의 존재를 웹·네트워크 층에 드러내지 않는다.** 아래에 정의된 모든
  이름(전역 객체, 메시지 채널, 헤더, UA 토큰, 코드)에 `pocket`·`fabrics`를 쓰지
  않는다. 네이티브는 웹에 사람이 읽는 오류 메시지를 보내지 않는다
- 브릿지는 **내부 표시 허용 도메인의 메인 프레임에만** 노출한다. 목록 밖의
  origin이나 하위 프레임에서 온 메시지는 응답 없이 무시한다

## 2. 웹에 노출되는 API

페이지 스크립트보다 먼저 주입되므로, 웹은 준비 완료 이벤트를 기다리지 않는다.
`window.nativeBridge`가 없으면 앱 밖(일반 브라우저)이다.

```ts
interface NativeBridge {
  readonly capabilities: readonly string[]; // 지원 메서드 이름 목록
  readonly runtimeVersion: string;          // 진단용. 기능 판단에 쓰지 않는다
  call<T>(method: string, params?: object): Promise<BridgeResult<T>>;
  on(event: string, handler: (data: unknown) => void): () => void; // 반환값은 구독 해제
}

type BridgeResult<T> =
  | { status: "ok"; data: T }
  | { status: "canceled"; code: CancelCode }
  | { status: "error"; code: ErrorCode };
```

- `call`은 **reject하지 않는다.** 취소와 오류도 `status`로 구분되는 정상 결과다
- 기능 탐지는 `capabilities.includes(method)`로 한다. 버전 비교를 하지 않는다
- 타임아웃은 네이티브가 두지 않는다. 사용자 조작을 기다리는 메서드가 있으므로
  필요하면 웹 측 헬퍼가 메서드별로 둔다

## 3. 전송 계층

| 항목 | Android | iOS |
|---|---|---|
| 웹 → 네이티브 | `WebViewCompat.addWebMessageListener` (androidx.webkit). JS 객체 이름 `nativeBridgeChannel` | `WKScriptMessageHandler`. 핸들러 이름 `nativeBridgeChannel` |
| origin·프레임 검사 | `allowedOriginRules`에 내부 표시 허용 도메인을 지정하고, `onPostMessage`의 `isMainFrame`이 false면 무시 | `message.frameInfo.isMainFrame`과 `securityOrigin`을 검사 |
| 네이티브 → 웹 | `JavaScriptReplyProxy.postMessage` → 채널 객체의 `onmessage` | `evaluateJavaScript`로 주입 스크립트의 수신 함수 호출 |
| 주입 스크립트 | `WebViewCompat.addDocumentStartJavaScript` (허용 도메인 규칙 동일) | `WKUserScript` (`.atDocumentStart`, `forMainFrameOnly: true`) |

주입 스크립트는 두 플랫폼이 같은 내용을 쓴다. `window.nativeBridge`를 정의하고,
요청 식별자 발급과 대기 중인 Promise 관리, 아래 와이어 메시지의 직렬화를
담당한다. 채널 객체(`nativeBridgeChannel`)는 내부용이며 웹앱이 직접 쓰지 않는다.

### 와이어 메시지 (JSON 문자열)

```jsonc
// 웹 → 네이티브: 호출
{ "id": "<요청 식별자>", "method": "camera.capture", "params": { } }

// 네이티브 → 웹: 응답. id로 대기 중인 Promise를 해소한다
{ "id": "<요청 식별자>", "status": "ok", "data": { } }
{ "id": "<요청 식별자>", "status": "canceled", "code": "USER_CANCELED" }
{ "id": "<요청 식별자>", "status": "error", "code": "UNSUPPORTED" }

// 네이티브 → 웹: 이벤트. id가 없다
{ "event": "app.resume", "data": { } }
```

- 요청 식별자는 주입 스크립트가 발급하며, 한 페이지 생명주기 안에서 유일하면 된다
- 네이티브는 알 수 없는 `method`에 `error` / `UNSUPPORTED`로 응답한다.
  무응답으로 두지 않는다
- 페이지가 이동하면 대기 중인 응답은 버린다

## 4. 이름 규칙

- 메서드와 이벤트 이름은 `<도메인>.<동작>`이다. 도메인은 소문자 한 단어,
  동작은 lowerCamelCase다. 예: `camera.capture`, `link.openExternal`
- capability 이름은 **메서드 이름과 같다.** 이벤트는 capability 목록에 넣지 않는다

## 5. v0.1 메서드

파라미터와 반환 형식은 S8 이후 구현 단계에서 확정해 이 표에 채운다.

| 메서드 | 반환 `data` | OS 권한 |
|---|---|---|
| `camera.capture` | `{ mimeType, base64, width, height }` | Android `CAMERA`, iOS `NSCameraUsageDescription` |
| `album.pick` | 미정 (`camera.capture`와 같은 항목 형식) | 없음. Photo Picker는 고른 항목만 전달하므로 권한 요청 단계를 만들지 않는다 |
| `file.share` | 미정 | 없음 |
| `clipboard.write` | 미정 | 없음 |
| `haptic.impact` | 미정 | Android `VIBRATE`(설치 시 권한, manifest 선언 필요) |
| `link.openExternal` | 미정 | 없음 |
| `app.openSettings` | 없음(`{}`). 설정 화면을 연 시점에 `ok`로 응답한다 | 없음. Android는 `Settings.ACTION_APPLICATION_DETAILS_SETTINGS`, iOS는 `UIApplication.openSettingsURLString`으로 이 앱의 설정 화면을 연다 |

- 이 표의 권한 열이 OS 권한 선언의 단일 근거다. 앱이 쓰지 않는 메서드의 권한은
  선언하지 않는다
- 바이너리 데이터는 base64 문자열로 반환한다. 크기를 줄이기 위해 네이티브가
  `maxWidth`, `quality` 파라미터로 압축한 뒤 반환한다. 파일 핸들 URL 방식은
  나중에 `params` 옵션으로 추가한다(MINOR)

- `app.openSettings`는 `PERMISSION_BLOCKED`를 받은 웹이 설정 이동을 안내할 때
  쓴다. 사용자가 설정에서 돌아오면 `app.resume` 이벤트가 오므로, 웹은 이때
  원래 기능을 다시 호출할 수 있다

## 5-1. v0.1 이벤트

| 이벤트 | `data` | 발생 시점 |
|---|---|---|
| `app.resume` | 없음(`{}`) | 앱이 백그라운드에서 포그라운드로 돌아왔을 때. 콜드 스타트에는 보내지 않는다 |

## 6. 결과 코드

### 생성 규칙

1. 형식은 UPPER_SNAKE_CASE, 정규식 `^[A-Z][A-Z0-9_]*[A-Z0-9]$`, 32자 이하다
2. `<대상>_<상태>` 순서로 명사를 앞에 둔다. 예: `PERMISSION_DENIED`
3. 도메인을 넣지 않는다. 웹은 자신이 호출한 메서드를 이미 알고 있으므로,
   같은 코드는 메서드와 관계없이 같은 방식으로 처리한다
4. 아래 공통 코드로 표현할 수 없을 때만 메서드 전용 코드를 만들고,
   `<도메인 대문자>_` 접두어를 붙인다. 예: `CAMERA_...`
5. 철자는 미국식 `CANCELED`로 고정한다. `status` 값도 `canceled`다
6. 코드 추가는 MINOR, 이름 변경과 제거는 MAJOR다
7. 웹은 모르는 코드를 받으면 `canceled`는 `USER_CANCELED`로, `error`는
   `INTERNAL`로 취급한다. 앱이 웹보다 새 버전일 때도 웹이 깨지지 않게 한다

### 레지스트리

이 표가 코드의 원본이다. Kotlin `enum`, Swift `enum`, 웹 쪽 상수는 이 표의
이름을 그대로 옮긴다. `app-bridge` 착수 시 레지스트리 파일과 코드 생성으로
전환한다.

| status | code | 의미 |
|---|---|---|
| canceled | `USER_CANCELED` | 사용자가 선택·촬영 화면을 닫았다 |
| canceled | `PERMISSION_DENIED` | 권한을 거부했으나 다시 요청할 수 있다 |
| canceled | `PERMISSION_BLOCKED` | 다시 요청할 수 없다. Android "다시 묻지 않음"·기기 정책, iOS 거부·제한(`restricted`)을 포함한다. 웹은 설정 이동을 안내한다 |
| error | `UNSUPPORTED` | 알 수 없는 메서드다. 구버전 앱이 반환한다 |
| error | `INVALID_PARAMS` | 파라미터 검증에 실패했다 |
| error | `BUSY` | 같은 기능이 이미 실행 중이다 |
| error | `UNAVAILABLE` | 기기에 해당 하드웨어나 기능이 없다 |
| error | `INTERNAL` | 그 밖의 네이티브 오류다 |

## 7. User-Agent와 HTTP 헤더

- UA: 기본 UA를 교체하지 않고 끝에 ` <앱 토큰>/<앱 버전>`을 덧붙인다.
  Android는 기본 `userAgentString`에 이어 붙이고, iOS는
  `applicationNameForUserAgent`를 쓴다. 런타임 버전은 넣지 않는다
- 커스텀 헤더는 내부 표시 허용 도메인으로 가는 요청에만 붙인다

| 헤더 | 값 |
|---|---|
| `X-App-Id` | Android `applicationId`, iOS 번들 식별자 |
| `X-App-Version` | 앱 버전 |
| `X-App-Platform` | `android` 또는 `ios` |

- 앱 토큰은 앱마다 다르므로 빌드 설정 집약 지점(Android flavor, iOS
  `Pocket.xcconfig`)에 둔다

## 8. 미정 사항

- `album.pick`의 다중 선택 여부와 메서드별 파라미터·반환 형식. 각 메서드를
  구현하는 step(S8~S10)에서 확정해 5절 표에 채운다
