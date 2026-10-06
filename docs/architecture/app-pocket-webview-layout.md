# app-pocket 웹뷰 레이아웃 계약 (safe area)

pocket 웹뷰와 탑재 웹앱이 화면 가장자리(상태바, 내비게이션 바, 노치, 홈 인디케이터)를
나눠 맡는 방식의 현행 명세다. 두 플랫폼 구현체와 웹앱은 이 문서를 그대로 따른다.

- 상태: v0.1. 첫 탑재 웹앱 stylist-web 기준으로 정했다
- 결정의 근거는 `../stylist-web-todo.md`의 "화면과 디자인 시스템" 절에 있다

## 1. 역할 분담

- 웹뷰는 **edge-to-edge 전체 화면**이다. 네이티브는 시스템 바·노치 영역에 padding이나
  별도 배경 뷰를 두지 않는다
- safe area는 **웹이 CSS로 처리한다.** 웹은 `viewport-fit=cover`를 선언하고
  `env(safe-area-inset-top|right|bottom|left)`를 패딩으로 쓴다
- 가로 모드를 지원한다(iPhone, iPad, Android 모두). 웹은 좌우 inset도 처리한다
- 네이티브는 inset 값을 웹에 별도로 주입하지 않는다(`--safe-area-inset-*` 변수, 브릿지
  이벤트 모두 없음). `env()` 값만이 계약이다

## 2. Android

- `enableEdgeToEdge()`를 호출하고, WebView에 시스템 바 inset만큼 padding을 주지 않는다.
  Compose `Scaffold`의 `innerPadding`을 WebView에 적용하지 않는다
- WindowInsets 리스너에서 inset을 `WindowInsets.CONSUMED`로 소비하지 않는다. 네이티브가
  처리한 inset 종류가 있으면 0으로 바꾼 WindowInsets를 넘긴다. CONSUMED로 반환하면
  WebView가 이전 inset을 계속 유지한다
- 지원 WebView 버전은 **M144 이상**이다. WebView는 M136부터 전체 화면 WebView에, M144부터
  모든 WebView에 inset을 전달한다. 그 미만 버전에서는 inset이 0이거나 부정확하며,
  이 경우의 대응은 하지 않는다. 검증 기기는 M144 이상으로 업데이트해 둔다

## 3. iOS

- SwiftUI의 WebView 래퍼에 `.ignoresSafeArea()`를 적용해 화면 전체를 덮는다
- `webView.scrollView.contentInsetAdjustmentBehavior = .never`로 설정한다. 기본값이면
  스크롤 뷰가 inset을 한 번 더 적용해 웹의 패딩과 중복될 수 있다

## 4. 검증

- 노치가 있는 iPhone, iPad, Android 실기기 또는 시뮬레이터·에뮬레이터에서 세로와
  가로 모드 모두 확인한다. 브라우저 개발자도구는 inset이 항상 0이라 검증 수단이 아니다
- 확인 항목: 상단 바가 상태바·노치와 겹치지 않는다. 하단 탭이 홈 인디케이터·내비게이션
  바와 겹치지 않는다. 가로 모드에서 내비와 본문이 노치 영역을 피한다. 여백이 이중으로
  생기지 않는다
