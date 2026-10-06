# 아키텍처 설계 문서

프로젝트 범위의 **현행 설계 규약**을 담는다. 여러 저장소가 같은 규약을 지켜야
하거나, 구현 코드보다 오래 유지되어야 하는 설계가 대상이다.

폴더의 역할과 다른 문서와의 구분은 `../ssot/repo-architecture.md`의
"아키텍처 설계 문서" 절이 정본이다.

## 색인

| 문서 | 내용 | 상태 |
|---|---|---|
| `app-pocket-bridge.md` | pocket 브릿지 계약의 잠정 정의 (이벤트명, 페이로드, capability 이름 체계, 오류 형식, UA 토큰 형식) | 잠정안 (v0.1). 안정화 후 `app-bridge`로 이관 |
| `app-pocket-webview-layout.md` | 웹뷰 edge-to-edge와 safe area 역할 분담 (네이티브 웹뷰 설정, 지원 WebView 버전, 검증 항목) | v0.1 |
