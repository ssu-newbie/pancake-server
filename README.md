# PancakE Survey Server

**플레이어의 설문 응답을 다음 플레이의 주민 데이터로 연결하는 게임 서버입니다.**

`Python` · `FastAPI` · `Pydantic` · `Uvicorn`

PancakE는 사람들의 찬반 응답을 게임 속 주민 데이터로 활용하는 게임입니다.
이 저장소는 설문 응답 저장, 최근 주민 조회, 점수 등록과 최고 점수 조회를 담당하는 API 서버를 담고 있습니다.

요구사항 정의·게임 연동·실행 검증을 중심으로 AI와 협업한 프로젝트입니다. 기존 코드 작성과 이번 리팩토링의 역할은 [인수인계 문서](docs/handoff.md)에 구분해 기록했습니다.

## 핵심 데이터 흐름

1. 게임을 마친 플레이어가 설문에 응답합니다.
2. 클라이언트가 `POST /responses`로 주장 ID와 찬반 응답을 제출합니다.
3. 서버가 한 번의 제출을 한 명의 응답자로 저장합니다.
4. 다음 플레이에서 `GET /residents`로 최근 응답자 데이터를 가져갑니다.

게임 클라이언트와 서버 사이의 응답 형식은 아래 API 예제에서 확인할 수 있습니다.

## 제공 기능

| 기능 | 구현 |
| --- | --- |
| 설문 응답 수집 | 주장 ID 목록과 찬반 목록을 한 응답자 단위로 저장 |
| 주민 데이터 조회 | 최근 응답자를 최신순으로 반환, 기본 100명 |
| 점수 기록 | 제출 시각과 점수를 저장하고 최고 점수 반환 |
| 상태 확인 | 서버 상태와 저장된 설문 응답 수 조회 |

## 로컬 실행

Python 환경에서 아래 명령을 실행합니다.

```powershell
git clone https://github.com/ssu-newbie/pancake-server.git
Set-Location -LiteralPath pancake-server
python -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m uvicorn pancake_server:app --host 127.0.0.1 --port 8000
```

macOS / Linux에서는 다음 명령을 사용합니다.

```bash
git clone https://github.com/ssu-newbie/pancake-server.git
cd pancake-server
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m uvicorn pancake_server:app --host 127.0.0.1 --port 8000
```

- API 문서: <http://127.0.0.1:8000/docs>
- 상태 확인: <http://127.0.0.1:8000/health>

실행 경로와 의존성은 현재 저장소의 소스를 기준으로 작성했습니다. 의존성 버전은 `requirements.txt`에서 고정하지 않습니다.

## API

| Method | Path | 역할 |
| --- | --- | --- |
| `GET` | `/health` | 상태와 누적 설문 응답 수 |
| `POST` | `/responses` | 설문 응답 한 건 저장 |
| `GET` | `/residents?n=100` | 최근 응답자 목록 조회 |
| `POST` | `/score` | 점수 한 건 저장 |
| `GET` | `/best` | 최고 점수와 점수 기록 수 |

업로드된 Unity 소스에서 확인한 클라이언트는 `claims`에 `q1`부터 `q112`까지의 주장 ID를 전달합니다. 서버 자체는 임의의 문자열을 허용하며, 문항의 의미와 순서는 클라이언트가 관리합니다. 소스 대조 결과와 검증 범위는 [클라이언트 연동 문서](docs/client-integration.md)에 기록했습니다.

### 설문 제출

```http
POST /responses
Content-Type: application/json
```

```json
{
  "claims": ["q1", "q2"],
  "agrees": [true, false]
}
```

응답 예시 — 저장된 설문이 없던 상태에서 한 건을 제출한 경우:

```json
{"ok": true, "total": 1}
```

`claims`와 `agrees`의 길이가 다르면 **짧은 목록의 길이에 맞춰 잘라 저장**합니다.
둘 중 하나가 비어 있으면 `{"ok": false, "error": "empty"}`를 반환합니다. 이 경우 현재 구현의 HTTP 상태 코드는 `200`입니다.

### 주민 조회

```http
GET /residents?n=100
```

```json
{
  "count": 1,
  "residents": [
    {
      "claims": ["q1", "q2"],
      "agrees": [true, false]
    }
  ]
}
```

`n`은 정수이며 내부적으로 `1`에서 `1000` 사이로 제한됩니다.
응답자는 최신순으로 반환되고, 요청 수보다 적게 저장되어 있으면 있는 데이터만 반환합니다.
저장 시각 `ts`는 주민 조회 응답에 포함하지 않습니다.

### 점수 기록과 최고 점수

```http
POST /score
Content-Type: application/json
```

```json
{"score": 1200}
```

점수 기록이 없던 상태에서 위 값을 제출한 경우:

```json
{"ok": true, "best": 1200, "count": 1}
```

`GET /best`는 `best`와 `count`를 반환합니다. 기록이 없으면 둘 다 `0`입니다.

## 저장 방식과 설계

| 파일 | 저장 내용 |
| --- | --- |
| `pancake_server.py` | 기존 Uvicorn 실행 진입점 |
| `pancake/application.py` | 앱 생성, 저장 경로, CORS 설정 |
| `pancake/api.py` | 설문·주민·점수 API 처리 |
| `pancake/schemas.py` | Pydantic 요청 모델 |
| `pancake/storage.py` | JSON 읽기, 잠금, 임시 파일 교체 |
| `requirements.txt` | FastAPI와 Uvicorn 의존성 |
| `tests/` | 기존 API 계약 및 앱 데이터 격리 회귀 테스트 |
| `responses.json` | 실행 중 생성되는 설문 응답 기록 |
| `scores.json` | 실행 중 생성되는 점수 기록 |

작은 서버의 데이터 흐름을 확인하기 쉽게 JSON 파일을 사용합니다.
쓰기 작업은 `threading.Lock`으로 같은 프로세스 내부에서 순서를 제어합니다.
완성된 JSON을 임시 파일에 쓴 뒤 `os.replace`로 대상 파일을 교체합니다.
기본 데이터 경로는 실행 위치와 관계없이 `pancake_server.py`가 있는 폴더입니다.
테스트에서는 `create_app(data_dir=...)`로 임시 저장 경로를 주입합니다.

## 리팩토링과 검증

한 파일에 있던 API·요청 모델·파일 입출력을 분리했습니다. Unity 연동을 유지하기 위해 URL, JSON 형식, 기존 예외 동작, 실행 명령을 보존했습니다.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

원본 서버와의 호환성까지 한 번에 확인하려면 Git 이력이 있는 저장소에서 실행합니다.

```bash
python scripts/verify_compatibility.py
```

이 명령은 원본 26개 테스트, 변경본 29개 테스트, OpenAPI 비교를 순서대로 수행합니다. GitHub Actions에도 같은 명령을 연결해 PR과 `main` 변경 시 Linux·Windows 환경에서 검증하도록 구성했습니다. 원격 실행 결과는 [Actions](https://github.com/ssu-newbie/pancake-server/actions/workflows/tests.yml)에서 확인할 수 있습니다.

위 명령은 가상환경을 활성화한 상태에서 실행합니다. 개발 의존성은 `requirements-test.lock`으로 이번 검증 환경에 맞춥니다. 운영 의존성 파일은 기존 상태를 유지했습니다.

- 변경 전 서버: API 회귀 테스트 **26개 통과**
- 변경 후 서버: 같은 API 테스트 26개 + 앱별 데이터 격리 1개 + Unity 요청 계약 2개, **29개 통과**
- 동일한 의존성 환경에서 변경 전·후 **OpenAPI 명세 일치** 확인

이 결과는 로컬 임시 데이터로 검증했습니다. Unity 실행, 운영 배포, 외부 동시 접속 성능을 검증한 결과는 아닙니다.

[구조와 설계 판단](docs/architecture.md) · [검증 기록과 재현 방법](docs/verification.md) · [인수인계와 다음 작업](docs/handoff.md)

## 현재 구현의 범위

- **단일 프로세스 기준:** 잠금은 프로세스 사이에 공유되지 않습니다. 여러 워커나 여러 서버에서 같은 파일을 함께 쓰는 구조는 지원하지 않습니다.
- **로컬 파일 저장:** 데이터가 누적되며, 읽기·쓰기 시 파일 전체를 처리합니다. 자동 정리나 데이터베이스는 구현되어 있지 않습니다.
- **오류 처리:** 파일이 없거나 읽기에 실패하면 빈 목록을 사용합니다. `/health`는 저장 데이터의 무결성을 검증하는 API가 아닙니다.
- **입력·접근 제어:** 기본 요청 타입 검사는 Pydantic에 맡깁니다. 응답 목록의 길이 일치 검사, 점수 범위 검사, 인증, 요청 제한은 별도로 구현되어 있지 않습니다.
- **CORS:** 현재 소스는 모든 출처를 허용합니다.

## 확장 방향

1. 기존 주장 ID 체계를 유지하면서 문항 사전과 검증 규칙 명문화
2. 설문 목록 길이와 점수 범위의 검증 규칙 추가
3. SQLite 또는 PostgreSQL로 저장소를 옮기고 동시 쓰기 처리 개선
4. 실제 배포 환경에 맞춘 데이터 보존, 접근 제어, 오류 관찰 체계 구성

위 항목은 후속 개선 방향이며 현재 구현된 기능과 구분합니다.
