# app-pocket todo

저장소: https://github.com/JunhaDex/fabrics-pocket-aos · https://github.com/JunhaDex/fabrics-pocket-ios · 로컬: `projects/app-pocket/aos/`, `projects/app-pocket/ios/`
Slack: `C0C52CS9QFK`
목적: 웹앱 주소만 바꿔 끼우면 새 앱이 되는 OS별 웹뷰 컨테이너("pocket"). 웹앱에 기기 기능 브릿지를 제공한다 (Kotlin / Swift)

## 결정 사항

### 사용자층
- 외부 고객 대상. 주 시장은 한국, 미국, 일본이며 20~30대 digital native,
  tech savvy 계층이다
- 최소 지원 OS 결정(minSdk 31, iOS 18.0)의 근거가 된 전 세계 커버리지 통계는
  구형 기기 비중이 높은 신흥 시장을 포함한다. 위 세 시장은 모두 기기 기반이
  최신이므로 실제 커버리지는 통계보다 높다
- 다국어 대응이 필요하다. config의 앱 표시 이름, 권한 사용 목적 문자열,
  오프라인 화면 문구가 로캘별 값을 갖는다

### 저장소와 세션 구조
- 컨테이너 디렉터리 `projects/app-pocket/`에는 `.git`을 두지 않는다. 하위 `aos/`와
  `ios/`가 각각 독립 저장소(`fabrics-pocket-aos`, `fabrics-pocket-ios`)다
- 프로젝트 등록 단위는 `app-pocket` 하나다. todo 파일, Slack 채널,
  `docs/PROJECTS.md` 행이 각각 하나씩이다
- 컨테이너의 `CLAUDE.md`와 `.claude/settings.json`은 어느 프로젝트 저장소에도
  속하지 않으므로 메타 저장소가 `.gitignore` 예외로 추적한다. 상위 디렉터리를
  먼저 예외 처리한 뒤 내용을 다시 제외하는 순서가 필요하다
- 세션은 `projects/app-pocket/`에서 시작한다. 두 플랫폼이 모두 작업 디렉터리
  안에 있으므로 서브에이전트가 각각을 수정할 수 있다. 컨테이너가 git 저장소가
  아니므로 git 명령은 `git -C aos` 형태로 대상을 명시한다
- 릴리스는 저장소마다 수행한다. CHANGELOG 생성기는 앱이므로 git-cliff이며,
  `cliff.toml`을 저장소마다 하나씩 둔다

### 브릿지 계약의 위치
- 계약은 별도 저장소 `app-bridge`(`fabrics-pocket-bridge`)에서 TypeScript
  타입과 런타임 헬퍼를 담은 npm 패키지로 관리한다. 상세는
  `docs/app-bridge-todo.md` 참고
- 다만 **패키지 작성은 이 프로젝트의 네이티브 구현이 시행착오를 거쳐 계약을
  안정시킨 뒤에 착수한다.** 계약이 흔들리는 동안 패키지를 먼저 만들면 MAJOR
  승급이 반복되어 버전 번호가 의미를 잃는다
- 그동안 계약의 잠정 정의는 루트 메타 저장소의
  `docs/architecture/app-pocket-bridge.md` 한 파일에 두고, 안정화 시점에
  `app-bridge`로 이관한다. 두 네이티브 저장소에 각각 복사본을 두면 동기화가
  깨지므로 양쪽이 같은 파일 하나를 참조한다. 이 폴더의 역할은
  `docs/ssot/repo-architecture.md`의 "아키텍처 설계 문서" 절이 정의한다
- 의존 순서: app-pocket 네이티브 구현 → app-bridge 패키지 배포 → 웹앱 개발.
  웹앱은 `common-design`과 `app-bridge`가 모두 완성된 뒤에 착수 가능하다

### 버전 체계
- 버전은 두 종류이며 서로 연동하지 않는다
  - **앱 버전**: 스토어에 배포되는 각 앱의 버전. 앱별로 상이하며 스토어 계정
    권한을 가진 사용자가 직접 빌드한다
  - **런타임 버전**: pocket 래퍼 자체의 버전. git tag(`vX.Y.Z`)로 관리한다
- 런타임 버전의 공개 API는 **브릿지 계약**이다. MAJOR는 계약의 파괴적 변경,
  MINOR는 하위 호환되는 기능 추가, PATCH는 계약이 바뀌지 않는 수정이다
- 두 저장소는 minor까지 동일한 번호를 유지한다. patch는 갈릴 수 있으나,
  공통 설정이 변경되면 patch가 아니라 minor를 올린다
- MAJOR 승급 시 이벤트를 즉시 제거하지 않고 최소 한 MAJOR 주기 동안 폐기
  예고를 유지한다. 구버전 앱이 항상 사용자 기기에 남아 있기 때문이다

### 산출물 정체성 (래퍼 비노출)
- 이 앱 빌더의 산출물은 pocket이 아니라 각 앱 그 자체다. **공통 래퍼가
  존재한다는 사실을 웹·네트워크 층에 드러내지 않는다**
- 적용 범위는 웹과 네트워크에서 관찰되는 층이다: UA, HTTP 헤더, JS 전역 객체,
  브릿지 메시지, 오류 메시지, 콘솔 로그. 이 층에는 `pocket`·`fabrics`를 쓰지
  않고, 앱별 이름 또는 특정 제품을 가리키지 않는 일반명을 쓴다
  - UA 토큰: `<앱 토큰>/<앱 버전>` (아래 "웹과 앱의 호환성 판단")
  - JS 전역 객체: 일반명(예: `window.nativeBridge`). 여러 앱에서 같은 이름이
    보이지만 특정 제품을 가리키지 않으므로 앱별 주입값으로 만들지 않는다
  - 커스텀 헤더: `X-App-Id`, `X-App-Version`, `X-App-Platform`처럼 제품명이
    없는 이름
- 바이너리 층(Android 클래스 경로 `com.fabrics.pocket.*`, iOS 모듈명
  `fabrics_pocket_ios`, Info.plist 키)은 범위 밖이다. 디컴파일해야만 보이고,
  숨기려면 `namespace`와 Product Name 결정을 다시 열어야 한다
- 이 기조는 브랜드 경험을 위한 것이며 스토어 심사 회피 수단이 아니다. App
  Store 심사 지침 4.2.6은 앱 생성 서비스로 만든 앱을 콘텐츠 제공자가 직접
  제출한 경우에만 허용하므로, 각 앱은 클라이언트 본인의 개발자 계정으로
  제출한다

### 웹과 앱의 호환성 판단
- 실행 시점의 판단은 버전 비교가 아니라 기능 탐지로 한다. 스토어 빌드 주기와
  웹앱 배포 주기가 다르므로 구버전 앱이 상존하는 것이 정상 상태다
- 거친 판단(앱 안인지 여부)은 User-Agent 토큰 `<앱 토큰>/<앱 버전>`으로
  한다. JavaScript 실행 전과 서버 렌더링 단계에서도 판별할 수 있다. 일반 PC
  브라우저에서 앱 다운로드 페이지로 리다이렉트하는 fallback도 이 신호를 쓴다
  - 기본 UA를 교체하지 않고 끝에 덧붙인다. 교체하면 서버와 라이브러리의
    브라우저 판별이 깨진다
  - 각 산출물은 자기 웹앱과 짝을 이루므로 웹앱은 자기 앱의 토큰 하나만 알면
    된다. `app-bridge` 헬퍼는 토큰 이름을 설정값으로 받는다
  - 런타임 버전은 UA에 넣지 않는다. 기능 판단은 capability가 맡으므로 UA로
    판단할 것은 앱 안인지 여부뿐이다. 진단용 런타임 버전은 브릿지 주입
    데이터에 둔다
  - 앱 토큰은 앱마다 다르므로 빌드 설정 집약 지점의 주입 대상이다
- 세밀한 판단은 브릿지가 주입하는 capability 목록(기능 이름 배열)으로 한다.
  구버전 앱에서는 해당 이름이 없으므로 기능이 조용히 숨겨진다
- 지원하지 않는 브릿지 기능을 호출하면 무응답이 아니라 명시적 오류를 반환해,
  웹앱이 대체 동작이나 앱 업데이트 안내를 실행할 수 있게 한다

### 브릿지 통신 구조
- 양방향으로 설계한다. 카메라, 앨범, 연락처 등 v0.1 후보 기능이 모두 결과를
  웹에 돌려줘야 하므로 일방 주입으로는 성립하지 않는다
- 웹이 기능을 호출할 때 요청 식별자를 붙이고, 네이티브가 같은 식별자로
  응답해 Promise를 해소한다. 동시 호출과 사용자 취소를 구분하기 위해 필요하다
- 사용자 취소(권한 거부, 선택 화면 이탈)는 오류가 아닌 별도 결과 종류로
  구분한다. 오류로 취급하면 웹앱이 불필요한 실패 안내를 띄우게 된다

### 스택과 최소 지원 OS
- Android `minSdk 31`(Android 12, 누적 커버리지 78.8%),
  iOS Deployment Target `18.0`(누적 90.4%)
- Android 31을 택한 근거는 커버리지가 아니라 v0.1 핵심 기능과의 정합성이다.
  API 31부터 시스템 스플래시가 OS에 내장되어 `core-splashscreen` 백포트
  경로와의 분기가 사라지고, Android 12가 웹 인텐트 처리를 바꿔 App Link
  검증 동작이 단일 경로가 된다. "시작 화면 2층 구조"와 "링크 오픈 브릿지"
  두 기능에서 OS 분기와 테스트 조합이 제거된다
- iOS 18은 상향 비용이 2.6%p로 가장 저렴한 지점이며(18→26은 16.7%p),
  Dark/Tinted 앱 아이콘 규격과 일치한다
- `compileSdk`는 최신을 유지한다. Photo Picker는 `minSdk`가 아니라
  `compileSdk` 33 이상을 요구하고, `androidx.activity`의 `PickVisualMedia`가
  가용성을 스스로 확인해 대체 경로로 넘어가므로 minSdk 31에서 분기 코드 없이
  쓸 수 있다. minSdk를 32로 올려도 얻는 것이 없다(API 32는 대형 화면 중심의
  Android 12L이며, 약 9%p를 잃는다)
- **앨범 선택 capability는 런타임 권한을 생성하지 않는다.** Photo Picker는
  사용자가 고른 항목만 전달하므로 `READ_MEDIA_IMAGES`를 요구하지 않는다.
  브릿지 설계 시 이 경로에 권한 요청 단계를 만들지 않는다
- UI 프레임워크는 Jetpack Compose와 SwiftUI, 웹뷰 컴포넌트는 `WebView`와
  `WKWebView`를 쓴다
- 커버리지 출처: apilevels.com(Statcounter 2026-04 데이터), iosref.com
  (Statcounter 2026-08-11). 전 세계 기준이므로 한국의 실제 커버리지는 더
  높다. **재검토 시점은 Play Console의 실사용자 기기 분포를 확보한 이후다**

### 빌드 시점 주입 값
- **application identifier(Android `applicationId`, iOS
  `PRODUCT_BUNDLE_IDENTIFIER`)는 앱마다 다르므로 소스에 리터럴로 적지 않는다.**
  v0.1에서도 플랫폼별 집약 지점에만 둔다. Android는 product flavor의
  `applicationId`, iOS는 xcconfig의 `POCKET_BUNDLE_ID`를
  `PRODUCT_BUNDLE_IDENTIFIER`가 참조하는 형태다. 2단계에서는 그 한 곳의 값을
  config 저장소에서 읽어오도록 교체한다
- **런타임 자체의 이름은 앱마다 바뀌지 않으므로 소스에 고정한다.** Android
  `namespace`는 `com.fabrics.pocket`, iOS 타깃·Product Name은
  `fabrics-pocket-ios`(Swift 모듈명 `fabrics_pocket_ios`)다. `namespace`는
  스토어에 노출되지 않고 `applicationId`와 같을 필요가 없다
  - 주의: flavor에 `applicationId`가 없으면 AGP는 `namespace`를 대신 쓴다.
    2단계에서 주입 값이 비면 오류 없이 `com.fabrics.pocket`으로 빌드되므로,
    그때 값이 비어 있으면 빌드를 실패시킨다
- 파생 영향: App Link 검증은 `applicationId`와 서명 인증서 지문에 묶이므로
  `assetlinks.json`이 앱별로 달라진다. iOS의 Associated Domains entitlement도
  번들 식별자를 참조하므로 entitlements 파일이 변수화 대상이다
- **시작 URL도 같은 집약 지점에 둔다.** v0.1의 요구사항은 "단일 웹 주소"이지만
  검증 환경이 로컬과 외부로 갈리므로 소스에 박으면 환경을 바꿀 때마다 코드를
  수정해야 한다. 환경 구분은 Android의 buildType과 iOS의 build configuration이
  담당하고, flavor와 xcconfig의 앱 차원은 2단계를 위해 비워 둔다
  - Debug 기본값은 `http://localhost:3000`이다
  - Release 값은 외부 HTTPS 도메인이며 **아직 확보되지 않았다**

### 로컬 검증 환경
- 웹뷰가 접근하는 주소는 **반드시 `localhost`여야 한다.** `http://localhost`는
  브라우저 표준에서 신뢰 가능한 출처로 취급되어 HTTPS 없이도 secure context가
  되지만, `10.0.2.2`나 LAN IP는 그렇지 않다. secure context가 아니면 Service
  Worker, Geolocation, 카메라·마이크 접근 등이 비활성화된다. 안드로이드
  에뮬레이터의 `10.0.2.2`는 이 이유로 Google 공식 문서가 WebView 디버깅에
  권장하지 않는다
- Android는 `adb reverse tcp:3000 tcp:3000`으로 기기의 `localhost`를 개발
  머신으로 포워딩한다. 에뮬레이터와 USB 연결 실기기 모두 동작한다. Google
  공식 WebView 문서가 권장하는 방식이며, 같은 문서가 `10.0.2.2`를 secure
  context가 아니라는 이유로 비권장한다고 명시한다
  - **영구 설정이 아니다.** 에뮬레이터 재부팅이나 `adb kill-server` 이후
    사라지므로 개발 스크립트에 넣어 매번 실행한다
  - `next dev`는 기본적으로 `0.0.0.0`에 바인딩하므로 호스트의 `127.0.0.1`에서도
    응답한다. 추가 플래그가 필요하지 않다
  - **Next.js의 `allowedDevOrigins`는 설정하지 않는다.** `adb reverse`를 거치면
    Host 헤더가 `localhost:3000`이라 Next가 동일 출처로 판단한다. LAN IP로
    접속할 때에만 이 설정이 필요해지는데, 그 경로는 secure context를 잃으므로
    애초에 쓰지 않는다
  - HMR 웹소켓도 같은 포트를 쓰므로 함께 터널링된다
  - 대안인 Chrome DevTools 포트 포워딩(`chrome://inspect`)도 `localhost`
    호스트명을 유지한다. GUI에 의존하므로 스크립트화에는 불리하다
- iOS 시뮬레이터는 호스트와 네트워크 스택을 공유하므로 `localhost`가 그대로
  동작한다. **실기기는 `adb reverse`에 해당하는 수단이 없어 localhost를 쓸 수
  없다.** 따라서 로컬 검증은 에뮬레이터와 시뮬레이터 중심으로 하고, 실기기
  검증은 외부 HTTPS 도메인 확보 이후로 미룬다
- 평문 HTTP 허용 설정은 **debug 빌드에만 적용한다.** Android 9(API 28)부터
  평문 트래픽이 기본 차단되고 이 차단이 WebView에도 적용되어, 페이지 내용이
  로드되기 전에 `ERR_CLEARTEXT_NOT_PERMITTED`로 실패한다
  - Android: `src/debug/res/xml/network_security_config.xml`에서 `localhost`와
    `127.0.0.1`만 `cleartextTrafficPermitted="true"`로 열고,
    `src/debug/AndroidManifest.xml`이 이 파일을 가리킨다. release 소스 세트에는
    포함되지 않는다
  - iOS: Debug 구성에 한해 `NSAllowsLocalNetworking`을 쓴다. 이 키는 점이 없는
    호스트명과 `.local` 도메인의 ATS를 해제하므로 `localhost`를 포함하지만
    **IP 리터럴에는 효과가 없다.** `127.0.0.1`을 쓰려면 `NSExceptionDomains`가
    따로 필요하므로, 설정을 단순하게 유지하기 위해 호스트명 `localhost`를 쓴다
  - `NSAllowsArbitraryLoads`는 전역으로 ATS를 꺼 스토어 심사에서 소명을
    요구받으므로 쓰지 않는다
- 테스트 페이지는 정적 HTML 하나로 충분하다. 브릿지 호출 결과와 오류를
  **화면에 렌더링하는 로그 영역**을 반드시 둔다. 실기기에서는 콘솔 확인이
  번거롭다. 원격 설정 JSON도 같은 서버에 정적 파일로 둔다
- 외부 HTTPS 도메인을 확보하면 포트 포워딩과 평문 예외가 모두 불필요해지고
  실기기 검증 경로가 열린다. 에뮬레이터와 시뮬레이터는 호스트를 경유해 그대로
  접속하므로 추가 설정이 없다. 전제 조건은 세 가지다
  - 공개 CA가 발급한 인증서여야 한다. 사설 CA를 쓰면 Android debug 설정의
    `<debug-overrides>`에 `<certificates src="user"/>`를 넣어야 한다
  - 에뮬레이터는 호스트의 DNS를 그대로 쓰지 않고 자체 DNS 프록시를 거치므로,
    공개 DNS에 등재되지 않은 도메인은 `-dns-server` 지정이 필요하다
  - 이 도메인을 커스텀 HTTP 헤더 부착 대상인 내부 표시 허용 도메인 목록에
    등록해야 서버 측 분기를 검증할 수 있다

### v0.1 범위 선정 기준
- 카메라와 앨범을 v0.1에 넣는다. 권한 요청, 사용자 취소, 바이너리 데이터 반환
  이라는 세 경로를 한 번에 통과시켜야 계약의 형태가 확정된다. 이 검증 없이
  계약을 고정하면 이후 MAJOR 승급을 부른다
- 별도 인프라(Firebase 프로젝트, 인증 설계, 스토어 승인 절차)가 필요한 기능은
  v0.1에서 제외한다
- 개별 기능의 OS별 실현 가능성은 사전 조사하지 않고 구현 시점에 점검한다

### 권한과 capability
- capability 목록이 브릿지 주입값과 OS 권한 선언의 **단일 근거**다. 앱이 쓰지
  않는 권한은 선언되지 않도록 빌드 시점에 가려낸다
- 권한별 사용 목적 문자열(iOS `NS*UsageDescription`, Android 요청 사유 문구)은
  앱마다 다르게 작성한다

### 인증과 세션 (v0.2에서 구현)
로그인은 자체 ID/PW와 SSO 두 가지를 지원하며, 웹과 앱 양쪽에서 동작해야 하고
앱에서는 자동 로그인을 지원한다.

**제약 (조사로 확인)**
- SSO를 웹뷰 안에서 처리할 수 없다. Google은 2017년부터 임베디드 웹뷰의
  OAuth 요청을 차단했고 2023년 7월부터 `disallowed_useragent` 403으로
  실패시킨다. 차단 대상에 `android.webkit.WebView`와 `WKWebView`가 명시되어
  있다. User-Agent 변조는 약관 위반이며, RFC 8252도 임베디드 웹뷰를 금지한다
- 시스템 브라우저의 로그인 결과를 웹뷰가 물려받을 수 없다.
  `ASWebAuthenticationSession`은 Safari가, `WKWebView`는 앱이 관리해 쿠키를
  공유하지 않는다. Android의 Custom Tabs도 앱의 WebView와는 공유하지 않는다
- 쿠키를 웹뷰에 직접 주입하는 방식은 타이밍 문제가 있다. iOS는 `setCookie`
  완료 후에도 첫 요청에 실리지 않는 사례가 있고, Android는
  `CookieManager.flush()` 없이는 앱 종료 시 메모리 쿠키가 유실된다
- 네이티브와 웹뷰가 각자 세션을 갱신하면 서로를 무효화하는 경쟁 상태가 생긴다

**설계: 인증의 주체를 네이티브 하나로 둔다**
- 웹뷰 안에서는 로그인을 처리하지 않는다
- 자체 ID/PW는 네이티브 화면에서 입력받아 서버 토큰 엔드포인트를 직접 호출한다
- SSO는 시스템 브라우저를 경유한다. iOS는 `ASWebAuthenticationSession`,
  Android는 Custom Tabs를 쓰고 Authorization Code + PKCE 방식을 쓴다. 네이티브
  앱은 공개 클라이언트이므로 바이너리의 비밀값은 비밀이 아니며 PKCE가 그
  역할을 대신한다. 앱 복귀 경로는 v0.1의 App Link/Universal Link를 재사용한다
- refresh token은 Keychain과 EncryptedSharedPreferences에 보관한다
- **웹뷰 세션 부트스트랩**: 쿠키를 주입하지 않고 일회용 교환 토큰을 쓴다.
  네이티브가 refresh token으로 수명 수 초의 일회용 토큰을 받아 시작 URL로
  POST 전송하고, 서버가 검증 후 `Set-Cookie`로 세션 쿠키를 내려준다. 타이밍
  문제를 우회하고, 쿠키 속성(`HttpOnly`, `Secure`, `SameSite`, 만료)을 서버가
  통제하며, 노출되어도 피해가 제한적이다. URL 로그에 남지 않도록 쿼리
  파라미터가 아닌 POST 본문으로 보낸다
- **세션 갱신 권한은 네이티브가 독점한다**. 웹뷰가 401을 받으면 브릿지로
  갱신을 요청하고, 네이티브가 새 일회용 토큰으로 재부트스트랩한다. 웹뷰가
  독자적으로 갱신을 시도하지 않는다
- **로그아웃은 브릿지 호출 대상이다**. 웹뷰 쪽 세션 쿠키만 지우면 다음 실행
  때 자동 로그인이 동작해 로그아웃되지 않은 것처럼 보인다. 네이티브 보안
  저장소의 refresh token까지 지워야 한다. 계정 전환과 회원 탈퇴도 같다

### 앱→웹 데이터 채널 (쿠키는 쓰지 않는다)
쿠키는 4KB 제한이 있고 매 요청에 실려 나가며 주입 타이밍 문제를 떠안는다.
User-Agent 토큰이 쿠키보다 이른 시점(JS 실행 전, 서버 렌더링 단계)에 읽히므로
대체 가능하다. 채널을 네 층으로 나눈다.

| 채널 | 담는 내용 |
|---|---|
| User-Agent 토큰 | 앱 안인지 여부, 앱 버전 (`<앱 토큰>/<앱 버전>`) |
| 커스텀 HTTP 헤더 | 서버가 첫 요청부터 알아야 할 앱 정보(앱 식별자, 앱 버전, 플랫폼) |
| 브릿지 주입 | capability 목록 등 구조화된 데이터 |
| 쿠키 | 서버가 발급하는 세션 쿠키만. 앱은 읽지도 쓰지도 않는다 |

- 커스텀 HTTP 헤더는 **내부 표시 허용 도메인에만** 붙인다. 웹뷰가 외부
  도메인으로 이동할 때 헤더가 따라가면 앱 정보가 제3자에게 유출된다

### 로그인 UX 흐름
같은 웹앱 코드가 환경에 따라 다르게 동작한다. 판별 근거는 User-Agent 토큰과
capability 목록이다.

| 환경 | GNB 로그인 버튼을 눌렀을 때 |
|---|---|
| PC·모바일 브라우저 | `/login` 페이지로 라우팅 |
| pocket 웹뷰 | 페이지 이동 없이 브릿지 호출. 네이티브 로그인 화면이 올라옴 |

- 웹: 홈 → 로그인 버튼 → `/login` 페이지 → ID/PW 또는 SSO 전체 리다이렉트 →
  콜백 → 세션 쿠키 → 홈 복귀
- 앱: 실행 → 시스템 스플래시 → 앱이 그리는 로딩 화면 뒤에서 refresh token
  확인. 토큰이 있으면 일회용 토큰을 교환해 **로그인된 홈으로 시작하며 GNB에
  로그인 버튼이 보이지 않는다**(자동 로그인의 체감 형태). 토큰이 없으면
  비로그인 상태로 홈을 띄우고 로그인 버튼을 노출한다
- 앱에서 로그인 버튼을 누르면 브릿지가 네이티브 로그인 화면을 띄우고, 성공
  시 refresh token을 보관한 뒤 일회용 토큰으로 웹뷰를 재부트스트랩한다
- 플랫폼별 SSO 체감 차이: iOS는 Safari가 관리하는 시트가 올라오며 시스템 동의
  팝업이 한 단계 더 있다. Android는 Custom Tabs가 열리고 시스템 브라우저와
  쿠키를 공유하므로 이미 브라우저에 로그인되어 있으면 계정 선택만으로 끝난다.
  Android 쪽 마찰이 더 적다

### 강제 업데이트
- 강제 업데이트 기준은 원격 설정으로 내려받는다. 기준값을 바이너리에 넣으면
  대상인 구버전 앱이 자신의 퇴출을 알 수 없어 목적을 달성하지 못한다
- 빌드 타임 config에는 원격 설정 엔드포인트 URL만 담는다. 최소 허용 앱 버전,
  최소 허용 런타임 버전, 강제와 권고의 구분, 점검 모드, 안내 문구는 서버가
  내려준다
- 초기 구현은 정적 JSON 파일을 특정 URL에 두는 방식으로 한다
- 앱 시작을 네트워크 호출로 막지 않고 캐시된 값을 먼저 쓰며 배경에서 갱신한다.
  오프라인에서 잘못된 안내가 뜨지 않도록 마지막 값을 보관하고, 확인 주기는
  콜드 스타트와 포그라운드 복귀로 제한한다
- Google Play는 사용자의 앱 접근을 불합리하게 차단하는 것을 금지하므로, 강제
  적용은 보안과 법규 준수 등 정당한 사유에 한정한다

### 앱별 config (2단계 산출물)
- 앱별 설정은 별도 비공개 저장소(`fabrics-pocket-config`)에 둔다
- 앱 버전과 빌드 번호도 이 저장소에 둔다. 어떤 버전이 언제 나갔는지가 git
  이력으로 남는다
- 서명·배포 자격(Android keystore와 비밀번호, iOS 배포 인증서와 provisioning
  profile)은 이 저장소에 넣지 않는다. config 저장소는 협업자와 CI가 읽어야
  하지만 서명 자격의 접근 범위는 더 좁아야 하기 때문이다. 로컬 키체인과
  비밀번호 관리 도구에 둔다
- JSON Schema로 필드를 검증하는 단계를 빌드 절차에 넣는다. 필드 누락은 빌드
  실패가 아니라 배포 후 런타임 오류로 드러나는 경우가 많다
- 항목 분류: 앱 정체성(번들 식별자, 표시 이름, URL scheme, 딥링크 도메인),
  웹뷰 연결(시작 URL, 내부 표시 허용 도메인 목록, UA 토큰, 원격 설정
  엔드포인트), 브랜딩 자산, capability와 권한 문구, 푸시 설정 파일과 알림 채널,
  스토어 리스팅(선택), 동작 설정(화면 방향, 다크 모드 정책, 최소 지원 OS)
- 내부 표시 허용 도메인 목록은 보안 요건이다. 목록 밖의 링크를 웹뷰 안에서
  열면 피싱 경로가 된다

### 브랜딩 자산 규격
- 앱 아이콘(iOS): iOS 18부터 Light, Dark, Tinted 세 변형이 필요하다. Dark는
  배경이 투명해야 하고 Tinted는 불투명 그레이스케일이어야 한다
- 앱 아이콘(Android): adaptive icon의 foreground와 background에 더해 Android
  13+ 테마 아이콘용 monochrome 레이어가 필요하다. iOS의 Tinted 에셋과 사실상
  동일하므로 하나로 공유한다
- 알림 아이콘(Android 전용): 투명 배경의 흰색 실루엣이라 앱 아이콘을
  재사용할 수 없다
- 시작 화면은 2층 구조다. 시스템 스플래시는 아이콘과 배경색만 지정할 수 있고
  로고·텍스트·로딩바를 넣을 수 없다(Android 12+ Splash Screen API의 제약이며,
  Apple은 launch screen에 브랜딩 요소를 넣지 말 것을 권고한다). 로고와 로딩
  인디케이터는 앱이 직접 그리는 첫 화면에 둔다

### 심사 대응
- 이 프로젝트의 목적은 단순 재포장이 아니라 OS API를 통한 기기 기능 접근을
  웹앱에 중개하는 것이다. Apple 4.2(Minimum Functionality)의 요건은 이 기능
  범위로 충족한다
- Google Play는 SMS와 통화 기록 권한을 제한 권한으로 분류하고 별도 승인 절차를
  요구한다. 통화 관련 기능의 범위를 확정할 때 이 절차의 필요 여부를 판단한다

## 진행 중: v0.1 네이티브 웹뷰 셸과 브릿지 기반

- 컨텍스트: 1단계의 첫 버전. 단일 웹 주소를 하드코딩한 상태로 AOS와 iOS 양쪽에
  웹뷰 셸을 세우고, 웹앱이 기기 기능을 호출할 수 있는 브릿지의 기반을 만든다.
  2단계(다중 앱 빌드)를 위해, 나중에 외부 주입으로 바뀔 값들은 플랫폼마다 한
  곳(Android는 product flavor, iOS는 xcconfig)에 모아 둔다
- 핵심 기능 (모두 완료되면 릴리스):
  - [ ] AOS·iOS 웹뷰 셸 (시작 URL 로딩, 오프라인·로딩 실패 화면)
  - [ ] 시작 화면 2층 구조 (시스템 스플래시 + 앱이 그리는 로딩 화면)
  - [ ] 브릿지 기반 레이어 (UA 토큰 주입, capability 목록 주입, 커스텀 이벤트
        수신, 미지원 기능 호출 시 명시적 오류 반환)
  - [ ] 강제 업데이트 (원격 설정 조회, 캐시 우선 동작, 강제·권고 분기)
  - [ ] 셸 기본 동작 (사용자가 탭한 외부 링크의 시스템 브라우저 전환,
        안드로이드 하드웨어 백 버튼과 웹 히스토리 연동, 화면 방향 고정,
        상태 표시줄 색 제어)
  - [ ] 기기 기능 브릿지: 카메라 촬영, 앨범 선택, 파일 다운로드와 공유 시트,
        클립보드, 햅틱
  - [ ] 링크 오픈 브릿지 (1) 기본 브라우저로 열기. localhost로 검증 가능
  - [ ] 링크 오픈 브릿지 (2) App Link/Universal Link로 관련 앱 열기.
        **blocker: 외부 HTTPS 도메인이 아직 확보되지 않았다.** OS가
        `/.well-known/assetlinks.json`(패키지명 + 서명 인증서 SHA-256 지문)과
        `/.well-known/apple-app-site-association`을 외부에서 직접 가져가
        검증하므로 localhost로는 성립하지 않는다. **호스팅 수단은 확정되었다.**
        Next 웹서버가 두 파일을 서빙하므로 별도 정적 호스팅이 필요하지 않고,
        도메인 확보가 유일한 잔여 조건이다
  - OS별 실현 가능성은 구현 시점에 재점검한다
  - [ ] 브릿지 계약의 잠정 정의 문서화 (이벤트명, 페이로드, capability 이름
        체계, 오류 형식, UA 토큰 형식). 안정화 후 `app-bridge`로 이관
- 세부 step:
  - [x] S0 개발 환경 준비. Android Studio와 SDK, 에뮬레이터 이미지를 설치하고
        `adb`를 PATH에 등록한다. Xcode는 이미 설치되어 있다
  - [x] S1 브릿지 계약 잠정 정의 문서 작성(`docs/architecture/app-pocket-bridge.md`).
        핵심 기능 목록에서는 마지막이지만 구현보다 앞선다. 두 플랫폼이 같은
        계약을 구현하고 서브에이전트가 양쪽을 나눠 작업하므로, 이벤트명과
        페이로드, capability 이름 체계, 오류 형식, UA 토큰 형식이 먼저 고정되지
        않으면 두 구현이 어긋난다
    - 메서드별 파라미터·반환 형식은 각 메서드를 구현하는 step(S8~S10)에서
      확정해 문서에 채운다
    - 런타임 버전 상수의 출처, v0.1 앱 토큰 값, 내부 표시 허용 도메인 목록의
      집약 지점 배치는 S3·S6에서 정한다
    - 결과 코드는 문서의 레지스트리 표가 원본이고, 각 플랫폼 enum은 손으로
      옮긴다. 레지스트리 파일과 코드 생성은 `app-bridge` 착수 시 도입한다
  - [x] S2 양 플랫폼 프로젝트 골격 생성 (aos `61e1f2d`·`f7e200c`, ios `11c9535`).
        Android는 Empty Activity(Compose), iOS는 App(SwiftUI) 템플릿이며 `minSdk 31`과
        Deployment Target `18.0`을 지정했다. 빌드 설정 집약 지점은 다음과 같다
    - Android: `pocket` flavor(`app` 차원)가 `applicationId`를, buildType별
      `BuildConfig.START_URL`이 시작 URL을 갖는다
    - iOS: `Config/Pocket.xcconfig`(앱 차원, `POCKET_BUNDLE_ID`)를
      `Debug`·`Release.xcconfig`(환경 차원, `POCKET_START_URL`)가 include하고,
      `Config/Info.plist`가 `PocketStartURL`로 노출한다
    - release 시작 URL은 외부 HTTPS 도메인 확보 전까지 빈 값이다
    - S2까지의 기본 설정은 main에 직접 반영했다. S3부터 기능 추가는 feat 브랜치에서
      작업하고 PR을 squash merge한다
  - [ ] S3 로컬 검증 환경 구축. 로그 영역을 갖춘 테스트 페이지, 원격 설정 JSON,
        debug 한정 평문 HTTP 설정, `adb reverse`를 포함한 개발 스크립트
  - [ ] S4 웹뷰 셸 (시작 URL 로딩, 오프라인·로딩 실패 화면)
  - [ ] S5 시작 화면 2층 구조
  - [ ] S6 브릿지 기반 레이어
  - [ ] S7 셸 기본 동작
  - [ ] S8 기기 기능 브릿지. 카메라와 앨범을 먼저 구현한다. 권한 요청, 사용자
        취소, 바이너리 반환 세 경로가 계약의 형태를 확정하므로 나머지 기능보다
        선행해야 한다
  - [ ] S9 강제 업데이트
  - [ ] S10 링크 오픈 브릿지 (1) 기본 브라우저로 열기
  - [ ] S11 링크 오픈 브릿지 (2). 도메인 확보 이후에 진행한다
- 다음 행동: S3 로컬 검증 환경 구축을 feat 브랜치에서 시작한다

## 다음 버전 (계획)

- **v0.2 인증**: 로그인, 로그아웃, 자동 로그인, 세션 갱신이 한 묶음이다.
  서버 측 엔드포인트(토큰 교환, 세션 교환)를 담당할 **신규 서버 프로젝트가
  필요하며 아직 생성되지 않았다.** 그 프로젝트가 만들어진 뒤에 착수한다.
  설계는 "인증과 세션" 절에 확정되어 있다
- v0.3 이후(1단계 잔여): 푸시 알림(Firebase 프로젝트와 서버 필요), 생체 인증
  (v0.2 인증 선행 필요), 위치, 연락처, 통화 관련 기능(Play Console 제한 권한
  승인 절차 가능성). 별도 인프라나 선행 결정이 필요해 v0.1에서 제외했다
- 2단계: 앱별 config 저장소(`fabrics-pocket-config`) 신설, 빌드 시점 메타데이터
  주입, capability 기반 권한 선언 생성, 빌드 매니페스트(앱 식별자·앱 버전·런타임
  버전) 기록

## 완료

_(없음)_

## 미확정 사항

- **통화 관련 기능의 범위**. 전화 걸기 수준인지 통화 기록 접근까지인지에 따라
  Play Console 제한 권한 승인 절차의 필요 여부가 갈린다
- **외부 HTTPS 도메인**. 아직 설정 전이다. 확보되면 실기기 검증 경로와 링크
  오픈 브릿지 (2)가 함께 열린다. `/.well-known/` 두 파일은 Next 웹서버가
  서빙하므로 호스팅 수단은 추가로 결정할 것이 없다
- **원격 설정 JSON의 스키마와 호스팅 위치**
- **도입할 SSO 제공자**. Apple은 앱이 서드파티 또는 소셜 로그인을 제공할 때
  Sign in with Apple을 함께 제공하도록 요구하는 조항(App Store Review
  Guideline 4.8)을 둔다. 제공자 목록이 정해지면 최신 문구를 확인한다
