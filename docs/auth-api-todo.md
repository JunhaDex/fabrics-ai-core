# auth-api todo

저장소: https://github.com/JunhaDex/fabrics-auth-api · 로컬: `projects/auth-api/`
Slack: `C0CDC8Y5UKH`
목적: 회원가입, 로그인, 계정 연결, 세션을 관리하는 fabrics 공통 회원 서버. 외부 제공자에게 로그인을 위임하고 자체 ID/PW도 지원하는 안전한 인증 서버 (Kotlin, Spring Boot, PostgreSQL)

## 결정 사항

### 역할과 범위
- fabrics 공통 회원 서버다. stylist, trama 등 모든 서비스가 한 계정을 공유한다
- OIDC 제공자(OP)가 되지 않는다. 외부 제공자에 대해서는 OAuth 2.0/OIDC client로
  동작하고, fabrics 서비스에는 자체 세션과 토큰 API를 제공한다
- 첫 소비자는 app-pocket v0.2 인증과 stylist-web이다. 서버가 제공할 엔드포인트
  요구는 `docs/app-pocket-todo.md` "인증과 세션" 절이 정본이다
- 서비스 고유 데이터는 각 서비스가 갖는다. 이 서버는 회원 공통 정보만 보관한다

### 로그인 수단
- 외부 제공자: Google, Apple, Kakao, Naver, GitHub
  - Google, GitHub는 Spring Security `CommonOAuth2Provider` 기본값을 쓴다.
    Apple, Kakao, Naver는 provider를 직접 등록한다
  - Naver와 GitHub는 OIDC가 아니라 OAuth 2.0 + 사용자 정보 API다. 사용자 정보
    매핑을 제공자별로 구현한다. GitHub 이메일은 `user:email` scope와
    `/user/emails`의 verified 주소로 얻는다
- 자체 ID/PW: 식별자는 이메일이다. 이메일 소유 인증과 비밀번호 재설정 메일이 필요하다
- 추가 인증 수단(TOTP, 패스키)은 v0.1에서 제외한다. 데이터 모델은 인증 수단을
  추가할 수 있는 구조로 둔다

### 계정 모델
- 소셜 계정은 `(제공자, 제공자 고유 ID)`로 식별한다. 이메일은 식별 근거로 쓰지 않는다
- 제공자가 이메일을 주지 않거나 중계 주소를 주어도 가입을 허용한다. 이메일은
  있으면 저장하고 없으면 비워 둔다
- 계정 연결은 수동이다. 제공자별 첫 로그인은 별도 계정을 만들고, 로그인한
  사용자가 다른 제공자를 직접 연결한다. 이메일이 같아도 자동으로 연결하지 않는다
- 회원 공통 정보는 이메일, 닉네임, 프로필 이미지만 보관한다
- 탈퇴는 유예 기간 후 삭제한다. 탈퇴 즉시 로그인을 차단하고 모든 토큰을 폐기한다.
  유예 기간이 지나면 개인정보를 파기한다
- 회원 상태 필드(활성, 정지, 탈퇴 대기)를 둔다. 관리자 기능은 v0.1에서 제외한다

### 세션과 토큰
- access token은 수명이 짧은 서명 JWT다. 각 서비스가 공개키(JWKS)로 직접 검증한다
- refresh token은 DB에 저장하고 회전과 폐기를 지원한다
- app-pocket이 요구하는 일회용 교환 토큰(수명 수 초, POST 본문 전달)과 세션
  쿠키 발급(`HttpOnly`, `Secure`, `SameSite`)을 제공한다
- 앱 소셜 로그인은 서버 경유 브라우저 리다이렉트다. 앱이 시스템 브라우저로 이
  서버를 열면, 서버가 제공자와 OAuth를 수행하고 App Link/Universal Link로 앱에
  복귀한다. 앱과 이 서버 사이의 코드 교환은 PKCE로 보호한다. 제공자 secret은
  서버에만 둔다

### 스택
- Kotlin + Spring Boot, Spring Security OAuth2 Client
- Java 21 (LTS). 기기에 설치된 Temurin 21을 그대로 쓴다. 빌드 도구는 Gradle Kotlin DSL과 Gradle Wrapper다
- PostgreSQL. 세션, refresh token, 일회용 토큰도 같은 DB에 둔다
- 로컬 PostgreSQL은 Docker Compose Support로 띄우고, 이미지는 메이저 버전
  태그 `postgres:18`로 고정한다. 마이너 업데이트만 따라간다
- CHANGELOG는 git-cliff로 만든다. `cliff.toml`은 trama-web, stylist-web과 같은 형식이다

## 진행 중

_(현재 없음. 다음 착수 대상은 v0.2)_

## 다음 버전 (계획)
- v0.2: 회원·소셜 계정 데이터 모델과 Flyway 마이그레이션, Google 로그인부터 시작하는 외부 제공자 연동
- 이후: 자체 이메일·비밀번호 가입과 메일 인증, 계정 연결, refresh token·일회용 교환 토큰·JWKS, 탈퇴

## 완료
- v0.1 (2026-11-01) 최초 골격: Spring Boot 4.1.2·Kotlin 2.3.21·Gradle 9.8.2 앱과 Docker Compose `postgres:18` 로컬 실행 환경(`./gradlew bootRun` 기동 확인), git-cliff `cliff.toml`, 프로젝트 `CLAUDE.md`(SSOT import)·`.claude/settings.json`, 루트 색인 등록, Slack 채널 `C0CDC8Y5UKH` slack-worker 연동

## 미확정 사항
- **배포 범위 이후의 인프라**. v0.1은 로컬 실행 검증까지다. 호스팅, TLS, 비밀값
  관리는 외부 도메인 확보 후 정한다
- **도메인과 쿠키 범위**. trama는 `trama.fabrics.*` 서브도메인을 쓴다. 이 서버의
  서브도메인과, 서비스별 세션 쿠키를 어느 도메인에 발급할지는 외부 도메인과 함께 정한다
- **메일 발송 수단**. 이메일 인증과 비밀번호 재설정에 필요하다. 로컬 검증용 수단도 함께 정한다
- **토큰 수명 값**. access token, refresh token, 일회용 교환 토큰의 구체적 수명
- **탈퇴 유예 기간 값과 법정 보관 항목**
- **약관·개인정보 동의 이력의 저장 방식**
- **app-pocket 설계와의 정합**. "서버 경유 브라우저 리다이렉트" 결정과 엔드포인트
  명세를 `docs/app-pocket-todo.md` "인증과 세션" 절과 맞춘다
