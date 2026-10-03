# 검증 기록

## 비교 기준

- 원본: `ssu-newbie/pancake-server`의 `9e074ae5e22e89c4aa1a51bdb5a0f64e654d64d0`에 있는 `pancake_server.py`
- 환경: Python 3.12.14, FastAPI 0.142.2, Pydantic 2.13.5, Starlette 1.7.0, HTTPX 0.28.1, pytest 9.1.1
- 전체 패키지 버전: `requirements-test.lock`
- 운영 서버의 패키지 버전과 일치하는지는 확인하지 않았다. 원본과 리팩토링 코드는 같은 로컬 환경에서 비교했다.

## 결과

| 검증 | 결과 |
| --- | --- |
| 원본에 API 계약 테스트 실행 | 26 passed |
| 리팩토링에 같은 테스트 및 데이터 격리 테스트 실행 | 27 passed |
| 변경 전·후 `app.openapi()` 비교 | 동일 |
| `pancake_server:app` import | 성공 |

테스트는 HTTP 상태 코드와 JSON 응답, 저장된 JSON, 재시작 후 조회, 잘못된 입력, 손상된 JSON의 기존 처리, CORS를 확인한다. 네 개의 스레드에서 각각의 요청을 보내 총 12개 설문·12개 점수가 유실되지 않는지도 확인한다. 이 작은 동시 쓰기 검증은 처리량 측정이나 운영 부하 시험이 아니다.

Starlette가 HTTPX 테스트 클라이언트의 향후 지원 변경을 알리는 deprecation warning 한 건을 출력했다. 테스트는 모두 통과했으며, 테스트 클라이언트 전환은 후속 의존성 갱신 시 다룬다.

## 다시 실행하기

가상환경을 활성화하고 저장소 루트에서 실행한다.

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

원본과 비교하려면 macOS/Linux에서 다음과 같이 별도 임시 파일을 사용한다. 원본 파일은 덮어쓰지 않는다.

```bash
legacy_source=$(mktemp /tmp/pancake-legacy-XXXXXX.py)
git show 9e074ae5e22e89c4aa1a51bdb5a0f64e654d64d0:pancake_server.py > "$legacy_source"
PANCAKE_LEGACY_SOURCE="$legacy_source" python -m pytest -q tests/test_api_contract.py
rm "$legacy_source"
```

## 남은 검증

Unity 클라이언트 실행, 실제 설문 자료, Render 데이터 보존 설정, 운영 서버 의존성, 배포 후 연결은 아직 확인하지 않았다. 인수인계에 언급된 과거 동시 접속·시뮬레이션 수치를 이 테스트 결과로 대체하거나 검증했다고 주장하지 않는다.
