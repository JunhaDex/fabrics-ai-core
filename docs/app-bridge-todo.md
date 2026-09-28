# app-bridge todo

저장소: `fabrics-pocket-bridge` (원격 미등록, 추후 생성) · 로컬: `projects/app-bridge/`
목적: pocket 브릿지 계약의 TypeScript 타입 정의와 런타임 헬퍼. 웹앱이 의존하는 npm 패키지

## 착수 조건 (중요)

**이 프로젝트는 아직 착수하지 않는다.** `app-pocket`의 네이티브 구현이
시행착오를 거쳐 브릿지 계약을 안정시킨 뒤에 패키지를 작성하고 배포한다.
계약이 확정되지 않은 상태에서 패키지를 먼저 만들면, 네이티브 구현이 바뀔
때마다 MAJOR 승급이 반복되어 버전 번호가 의미를 잃는다.

의존 순서는 다음과 같다.

```
app-pocket 네이티브 구현 (계약 안정화)
  → app-bridge 패키지 작성·배포
    → 웹앱 개발 착수
```

웹앱 개발은 `common-design`과 `app-bridge`가 모두 완성된 뒤에 시작할 수 있다.

## 결정 사항

- 브릿지 계약의 정의 위치는 이 별도 저장소다. 계약을 참조하는 주체가 AOS
  구현, iOS 구현, 모든 소비 웹앱 셋이므로, 세 곳에 흩어지면 반드시 어긋난다.
  웹앱이 타입 검사로 계약 위반을 컴파일 시점에 잡을 수 있다는 점이 선택의
  근거다
- 발행 방식은 `common-design`에서 검증한 파이프라인을 재사용한다.
  GitHub Packages, 스코프 `@junhadex`, changesets, GitHub Actions +
  `changesets/action@v2`
- 라이브러리이므로 CHANGELOG 생성기는 changesets다 (`app-pocket`은 앱이라
  git-cliff를 쓴다)
- 이 패키지의 버전은 `app-pocket`의 런타임 버전과 같은 계약을 서술하므로,
  두 번호의 대응 관계를 명시적으로 유지한다. 구체적인 연동 규칙은 미확정

## 계약에 담길 내용 (app-pocket에서 확정되는 대로 이관)

- 커스텀 이벤트 이름과 페이로드 구조
- capability 이름 체계
- 미지원 기능 호출 시의 오류 형식
- User-Agent 토큰 형식 (`pocket/<런타임 버전>`)
- 최소 런타임 버전 선언과 강제 업데이트 연동 방식

## 진행 중

_(착수 전. 위 "착수 조건" 참고)_

## 다음 버전 (계획)

- v0.1: `app-pocket` 1단계에서 확정된 계약의 타입 정의와 런타임 헬퍼.
  UA 토큰 판별 유틸리티, capability 탐지 유틸리티, 미지원 기능 호출 시의
  fallback 처리

## 완료

_(없음)_

## 미확정 사항

- 패키지 버전과 `app-pocket` 런타임 버전의 연동 규칙. 같은 번호로 맞출지,
  호환 표를 별도로 둘지
- 저장소명 `fabrics-pocket-bridge` 확정 여부. 디렉터리명은 `app-bridge`로
  등록되어 있어 둘이 다르다
- 프레임워크 비종속 여부. React 전용 훅을 포함할지, 순수 TypeScript로 유지하고
  프레임워크 어댑터를 분리할지
- PC 브라우저 fallback(앱 다운로드 페이지 리다이렉트)을 이 패키지가 제공할지,
  웹앱이 각자 구현할지
