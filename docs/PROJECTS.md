# 프로젝트 레지스트리 (SSOT)

`0_pjt_fabrics` 산하 모든 프로젝트의 단일 색인. 새 프로젝트가 생기면 이 표에
한 행을 추가한다. CLAUDE.md의 "프로젝트 색인" 표는 이 문서의 요약본이므로,
이 문서를 먼저 갱신한다.

| 프로젝트 | 상태 | 저장소 URL | 로컬 경로 | 한 줄 설명 | 관련 SSOT |
|---|---|---|---|---|---|
| _(예시) inventory-system | 기획 | (미정) | `projects/inventory-system/` | 원단 재고 실시간 추적 | — |
| common-design | 구축중 | https://github.com/JunhaDex/fabrics-design-system | `projects/common-design/` | 테마(빌드)·모드(런타임) 2층위 스타일을 지원하는 fabrics 공통 디자인 시스템 (React, Radix, Tailwind v4, npm) | — |
| app-pocket | 구축중 | https://github.com/JunhaDex/fabrics-pocket-aos · https://github.com/JunhaDex/fabrics-pocket-ios | `projects/app-pocket/aos/`, `projects/app-pocket/ios/` | 웹앱 주소만 바꿔 끼우면 새 앱이 되는 OS별 웹뷰 컨테이너. 웹앱에 기기 기능 브릿지를 제공 (Kotlin, Swift) | ADR 0005 |
| app-bridge | 기획 | (미정) `fabrics-pocket-bridge` | `projects/app-bridge/` | pocket 브릿지 계약의 TypeScript 타입과 런타임 헬퍼. 웹앱이 의존하는 npm 패키지 | — |

## 상태 값 정의
- **기획**: 루트 세션에서 구조/요구사항을 논의 중. 아직 별도 저장소 없음.
- **구축중**: 독립 저장소 생성됨, 프로젝트 스코프 세션에서 작업 중.
- **운영중**: 배포되어 운영 중.
- **보류/중단**: 일시 중지 또는 폐기.

## 표기 규칙
복수 저장소를 갖는 프로젝트(ADR 0005의 컨테이너 디렉터리)는 행 하나에
저장소와 로컬 경로를 모두 나열한다. 원격 저장소가 아직 없으면 "(미정)"과
함께 예정된 저장소명을 적는다.

## 갱신 규칙
이 문서는 사용자가 직접 갱신하거나, 루트 세션에서 사용자 승인 후에만 갱신한다.
(CLAUDE.md의 "가이드 우선" 원칙 참고)
