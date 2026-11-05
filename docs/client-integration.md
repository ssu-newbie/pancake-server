# Unity 소스와 서버 계약 대조

## 자료와 확인 범위

업로드된 `PancakE_v5_scripts (40).zip`을 직접 검사했다. ZIP SHA-256은 `1e21730a0322da0155ac93f209b30ece809e3d36c180eb1a2308d483bccc03e8`이다.

ZIP의 `Server/pancake_server.py`는 Git blob `23eca8d91445b3e952b4250ccdbc12c6197b3a57`로, 이 PR의 기준 커밋에 있는 서버와 바이트 단위로 일치한다. 따라서 이전에 검증한 서버가 이 클라이언트 묶음에 동봉된 서버임을 확인했다.

ZIP은 전체 Unity 프로젝트가 아니다. 스크립트·모델·오디오·이미지·폰트는 있지만 `.meta`, 씬 파일, `Packages`, `ProjectSettings`가 없다. 실제 에디터 버전과 패키지 조합, 씬 참조는 별도 프로젝트에서 확인해야 한다.

## 소스에서 확인한 계약

| 항목 | 확인 결과 | 원본 위치 |
| --- | --- | --- |
| 주장 ID | `q1`~`q112`, 문항 순서에서 생성 | `ContentDatabase.GetClaims` |
| 내장 설문 | 80개 행, 각 행은 112자리 이진 문자열 | `RealSurveyData.Rows` |
| 주민 조회 | `GET /residents?n=...`, timeout은 설정값을 올림해 최소 1초 | `SurveyClient.FetchResidents` |
| 주민 등록 | 엔딩 문항을 먼저 넣고 나머지 전체 문항을 이어 제출 | `GameFlowController.RunResidentRegistration` |
| 등록 중단 | 제출 코루틴 호출 전에 종료, 부분 저장 없음 | 같은 메서드 |
| 점수 제출 | `POST /score`, timeout 4초, 실패 콜백 -1 | `SurveyClient.PostScore` |
| 설문 제출 | `POST /responses`, timeout 5초 | `SurveyClient.PostSurvey` |

`GameConfig.surveyMaxAnswers = 5` 필드는 남아 있지만 현재 등록 루프는 그 필드를 사용하지 않는다. "최대 5문항 설문"이라는 설명은 현재 클라이언트와 맞지 않는다.

## 주민 데이터가 만들어지는 방식

`GameManager.ResetRun`은 주민 수만큼 서버 응답자를 먼저 배치하고, 남는 자리를 내장 설문 80명으로 채운 뒤 부족한 주민을 합성한다. 서버가 없고 기본 주민 수가 100이면 내장 80명과 합성 20명이다.

서버 응답자의 누락 문항은 같은 인덱스의 내장 행으로 채우지 않는다. 그 주민의 성향과 주장 기준 찬성률을 이용해 합성한다. 따라서 서버 주민 수와 실제 응답이 채워진 셀 수는 다르다. `serverResidentCount`도 서버 주민과 내장 주민을 합산한 값이다.

## 발견한 연동 문제

`SurveyClient.PostSurvey`는 `UnityWebRequest.Result.Success`만 확인한다. 서버는 빈 목록에 HTTP 200과 `{"ok": false, "error": "empty"}`를 반환하므로, 이 응답은 현재 클라이언트에서 성공으로 전달된다. 서버 동작은 기존 계약 테스트에 기록되어 있다. 현재 정상 등록 흐름은 전체 문항을 보내므로, 빈 제출 경로가 게임에서 실제 발생했다고 판단한 것은 아니다.

후속 수정에서는 응답 DTO의 `ok`를 읽고 HTTP 성공과 저장 성공을 함께 확인해야 한다. 실패 메시지도 통신 실패·서버 거절·파싱 실패를 구분할 수 있다. 이번 서버 구조 분리에서는 HTTP 상태 코드를 바꾸지 않았다.

또한 엔딩 문구는 주민이 모두 실제 사람이라고 표현하지만, 기본 오프라인 구성에는 합성 주민이 포함된다. 데이터 구성 설명과 플레이어 안내를 함께 검토할 항목이다.

## 검증

`tests/test_unity_contract.py`는 실제 개인정보나 원본 설문행을 사용하지 않는다. 전체 112문항을 엔딩 문항 우선 순서로 보내는 경우와 과거의 부분 응답을 서버가 그대로 돌려주는 경우를 확인한다. Unity의 JSON 직렬화·네트워크 코루틴·UI를 실행한 테스트는 아니다.

Unity 소스 정리본은 DTO 다섯 개를 `SurveyModels.cs`로 옮겼다. 네임스페이스, 클래스명, 필드, 코루틴 본문의 코드 토큰을 보존했다. 에디터 컴파일과 서버 장애 시나리오의 플레이 검증은 다음 단계다.
