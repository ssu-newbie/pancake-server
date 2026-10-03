# PancakE 인수인계와 다음 작업

## 자료의 기준

현재 GitHub 서버 소스와 새 회귀 테스트는 직접 검토·실행했다. Claude가 작성한 `HANDOFF.md`의 Unity 관련 내용은 이전 작업에 관한 전달 기록이다. 문서의 `[확인]` 표시는 당시의 확인 상태이며, 이번 작업에서 소스와 실행 결과를 대조했다는 뜻이 아니다.

## 역할

인수인계에 따르면 사용자는 팀 리더·개발 담당으로 요구사항과 자료를 제공하고 Unity 편집, 빌드·실행, 배포와 플레이 검증을 수행했다. Claude가 C#·Python 코드를 작성했다. 이번 서버 책임 분리와 자동화 테스트·문서 정리는 GPT/Codex와 협업한 변경이다.

## 현재 상태

| 영역 | 확보한 근거 | 다음 단계 |
| --- | --- | --- |
| FastAPI 서버 | GitHub 소스와 로컬 회귀 테스트 | 초안 PR 검토, 운영 환경과 대조 |
| Unity → 서버 요청 | 인수인계상 `claims`에 `q1`~`q112` ID 사용 | `SurveyClient.cs`와 실제 요청 대조 |
| 서버 연결 실패 시 대체 데이터 | 인수인계상 서버→내장→합성 순서 | 타임아웃 및 실패 분기 재현 |
| 내장 설문 데이터 | 인수인계상 80명×112문항 | `RealSurveyData.cs`에서 직접 확인 |
| 과거 성능·시뮬레이션 | 실행 원본 자료 없음 | 수치의 포트폴리오 기재 보류 |

## 다음에 받을 파일

우선 `PancakE_v5_scripts.zip` 최신본, 또는 다음 소스가 필요하다.

- `SurveyClient.cs`, `RealSurveyData.cs`, `GameDataV5.cs`
- `GameFlowController.cs`, `GameManager.cs`, `ContentDatabase.cs`
- `HUDManager.cs`, `CookingController.cs`, `PancakeVisual.cs`
- 씬 생성·모델 교체를 담당하는 Editor 스크립트

Unity 프로젝트로 실행까지 검증하려면 `Assets`의 필요한 소스·씬·메타 파일, `Packages/manifest.json`, `Packages/packages-lock.json`, `ProjectSettings/ProjectVersion.txt`도 필요하다. 원본 설문 개인정보나 `Library`, `Temp`, 빌드 캐시는 필요하지 않다.

## 우선순위

1. 최신 클라이언트 요청과 기존 API 계약 대조
2. 게임 진행 상태와 UI·씬 이름 의존 관계 기록
3. 핵심 플레이 흐름의 실행 기준 확보 후 작은 단위로 책임 분리
4. 이전·이후 동작 근거를 연결한 포트폴리오 사례 작성
