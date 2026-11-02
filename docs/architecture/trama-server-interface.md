# trama 서버 인터페이스 (초안)

trama 서버(Kotlin, Spring Boot)가 편집기와 AI에 제공하는 인터페이스의 현행 명세다. 문서 구조,
`apply_ops` 연산, 오류 코드는 `trama-document-model.md`가 정본이고, 주석 HTML 형식은
`trama-html-conversion.md`가 정본이다. 요구사항은 `../references/fabrics-tala-requirements.md`의
"AI 원격 API (MCP)", "동시 편집과 이력" 절이다.

- 상태: 초안. 인증은 다루지 않는다. 참여자는 `actor`를 스스로 밝힌다
- 서버는 문서의 원본을 소유하고, 모든 쓰기를 검증한 뒤 문서 단위 `seq` 순서로 적용한다

## 1. 인터페이스 구성

| 인터페이스 | 소비자 | 맡는 일 |
|---|---|---|
| REST `/api/*` (JSON) | 편집기 | 문서 목록·메타, 내보내기, 변경 기록·스냅샷 조회, 자산 |
| WebSocket `/api/documents/{docId}/sync` | 편집기 | 쓰기, Undo·Redo, 되돌리기, 스냅샷 복원, presence |
| MCP `/mcp` (Streamable HTTP) | AI | 읽기 도구, `inspect`, `apply_ops` |

- 편집기의 문서 쓰기는 WebSocket으로만 받는다. REST로 트랜잭션을 받는 엔드포인트는 두지 않는다
- AI의 `apply_ops`는 편집기 쓰기와 같은 적용 경로를 지나고, 결과는 WebSocket 참여자에게 같은 형식으로 브로드캐스트된다
- DTCG 토큰 가져오기·내보내기와 HTML 내보내기는 web이 처리한다. 가져오기 결과는 `apply_ops` 트랜잭션으로 들어온다

## 2. REST

| 메서드 | 경로 | 기능 | 응답 |
|---|---|---|---|
| `GET` | `/api/documents` | 문서 목록 | `[{ id, name, seq, updatedAt }]` |
| `POST` | `/api/documents` | 문서 생성. 본문 `{ name, content? }`. `content`는 문서 JSON(가져오기) | `{ id }` |
| `GET` | `/api/documents/{docId}` | 문서 메타 | `{ id, name, seq, updatedAt }` |
| `PATCH` | `/api/documents/{docId}` | 이름 변경. 본문 `{ name }` | 문서 메타 |
| `DELETE` | `/api/documents/{docId}` | 문서 삭제 | `204` |
| `GET` | `/api/documents/{docId}/content` | 현재 문서(내보내기) | `{ seq, doc }` |
| `GET` | `/api/documents/{docId}/transactions` | 변경 기록. 쿼리 `before`(seq), `actor`, `limit` | `[{ seq, txId, actor, at, changes }]`, `seq` 역순 |
| `GET` | `/api/documents/{docId}/snapshots` | 스냅샷 목록 | `[{ id, seq, reason, actor, at }]` |
| `POST` | `/api/documents/{docId}/snapshots` | 수동 스냅샷 | `{ id, seq }` |
| `PUT` | `/api/documents/{docId}/assets/{hash}` | 자산 업로드. 본문의 SHA-256이 `hash`와 다르면 거부 | `204` 또는 `409 HASH_MISMATCH` |
| `GET` | `/api/documents/{docId}/assets/{hash}` | 자산 조회 | 바이너리 |
| `GET` | `/actuator/health` | 상태 확인 | |

- 문서 이름은 서버 메타데이터이며 문서 모델(`objects`)에 포함하지 않는다
- `POST /api/documents`의 `content`는 적용 전에 `apply_ops`와 같은 검증을 거친다. 실패하면 `422`와 문서 모델 9절의 `error`를 반환한다
- `reason`은 `manual`, `ai-session`, `restore` 중 하나다
- 자산 엔드포인트는 문서 모델 11절의 자산이 구현된 뒤에 연다
- 없는 `docId`는 `404 DOCUMENT_NOT_FOUND`다. 오류 본문은 `{ code, message }`이며 판단은 `code`로 한다

## 3. WebSocket `/api/documents/{docId}/sync`

메시지는 JSON `{ "type": …, … }`이다. 연결 직후 클라이언트는 `join`을 보내고, `init`을 받기 전에는 다른 메시지를 보내지 않는다.

### 클라이언트 → 서버

| type | 필드 | 기능 |
|---|---|---|
| `join` | `actor`, `lastSeq?` | 참여 시작. `actor`는 `user:<id>` |
| `submit` | `txId`, `ops` | 트랜잭션 제출. `actor`는 `join`의 값을 쓴다 |
| `undo` | | 자기 트랜잭션 중 가장 최근 것을 되돌린다 |
| `redo` | | 가장 최근 Undo를 다시 적용한다 |
| `revert` | `seq` | 변경 기록의 트랜잭션 하나를 되돌린다. 작성자와 무관하다 |
| `restore` | `snapshotId` | 스냅샷 시점의 문서로 되돌린다 |
| `presence` | `selection`, `cursor?` | 선택한 노드 ID 목록과 보드 좌표 |

### 서버 → 클라이언트

| type | 필드 | 기능 |
|---|---|---|
| `init` | `seq`, `doc` 또는 `txs` | `join` 응답. `lastSeq` 이후 로그가 남아 있으면 `txs`, 아니면 `doc` 전체 |
| `ack` | `txId`, `seq`, `changes`, `warnings` | 자기 요청이 적용됨 |
| `reject` | `txId?`, `error` | 자기 요청이 거부됨. `error`는 문서 모델 9절 형식 |
| `tx` | `seq`, `txId`, `actor`, `changes` | 다른 참여자의 적용 결과 |
| `presence` | `actor`, `selection`, `cursor?`, `working?` | 참여자 상태. `working`은 AI가 작업 중인 Section·Frame ID 목록 |
| `leave` | `actor` | 참여 종료 |

- `changes`는 `[{ id, key, value }]`이며, 서버가 적용한 결과 값이다. `value`가 `null`이면 속성 삭제다. 객체 삭제는 그 객체의 모든 키를 `null`로 보낸다
- 클라이언트는 `ops`를 다시 적용하지 않고 `changes`를 그대로 덮어쓴다. `order`의 fractional index 키는 서버가 계산하므로 다시 적용하면 서버와 달라질 수 있다
- 낙관적 반영: 클라이언트는 `submit` 직후 로컬에 먼저 적용할 수 있다. `ack`의 `changes`로 덮어쓰고, `reject`면 로컬 적용분을 되돌린다
- `undo`, `redo`, `revert`, `restore`는 서버가 새 트랜잭션을 만들어 적용하며, 결과는 `ack`와 `tx`로 전달된다. 되돌릴 대상이 없으면 아무 메시지도 보내지 않는다
- 되돌리기 규칙(`undo`, `revert`)은 문서 모델 9절 "Undo"를 따른다. 이후 다른 트랜잭션이 바꾼 `(ID, 키)`는 건너뛴다
- `restore`는 스냅샷 시점과 현재 문서의 차이를 트랜잭션 1개로 적용한다. 적용 직전 현재 문서로 `reason: restore` 스냅샷을 남긴다

## 4. MCP `/mcp`

| 도구 | 입력 | 출력 |
|---|---|---|
| `list_documents` | | `[{ id, name, seq }]` |
| `get_tree` | `document`, `node?`, `depth?`, `format?` | `node`를 생략하면 Frame 목록과 Section·주요 컨테이너 개요. 지정하면 그 하위를 `format`(`html` 기본, `json`)으로 반환 |
| `get_tokens` | `document` | 토큰 목록, 설명, modifier 조합별 해석값 |
| `get_components` | `document` | 컴포넌트, componentProp, 변형 목록 |
| `inspect` | `document`, `node`, `bp`, `screenshot?` | 해당 BP에서 계산된 박스 크기, 오버플로·잘림 경고. `screenshot: true`면 PNG 포함 |
| `apply_ops` | `document`, `ops` | 문서 모델 9절 응답 |

- `html` 형식은 `trama-html-conversion.md`의 `annotated` 출력이다. 속성과 토큰 바인딩은 `json` 형식으로 읽는다
- `json` 형식은 대상 노드와 하위 노드의 객체를 문서 모델 1절의 `objects` 형식으로 반환한다
- `actor`는 `ai:<MCP 세션 ID>`이고 `txId`는 서버가 만든다. 도구 호출 1회가 트랜잭션 1개이자 Undo 1단계다
- 한 세션이 한 문서에 처음 `apply_ops`를 호출하면, 적용 직전에 `reason: ai-session` 스냅샷을 남긴다
- AI의 Undo 도구는 두지 않는다. AI 변경은 편집기의 변경 기록에서 `revert`로 되돌린다
- `inspect`와 `get_tree`의 `html` 출력은 서버의 헤드리스 Chromium이 web의 `render.js`를 불러 만든다
