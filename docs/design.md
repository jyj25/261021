# 설계 명세

## 문서 정보

| 항목 | 내용 |
| --- | --- |
| 문서 번호 | LAB-SDD-001 |
| 버전 | 2.0 |
| 상태 | 초안 |
| 참고 | ISO/IEC/IEEE 42010, 12207 구조 참고 |

## 1. 구성

```text
브라우저 방문자
  -> Streamlit Community Cloud / app.py
      -> lab_data.py: CSV 정리, 비교, 이상치, 재현 코드
      -> reporting.py: Markdown 초안 구성
      -> shared_workspace.py: GitHub 저장소 공용 저장
      -> OpenAI Responses API: 동의 후 집계 기반 해석
```

## 2. 객체와 모듈 책임

| 객체/모듈 | 책임 |
| --- | --- |
| VisualizationApp | 공개 편집 UI, 분석 설정, AI 동의, 저장·내려받기 |
| ExperimentDataset | 표 데이터와 숫자형 측정 변수 표현 |
| ExperimentDataService | CSV 읽기, 정리, 조건 비교, 이상치 및 Python 코드 생성 |
| ReportDraftService | 입력된 결과와 한계를 Markdown 초안으로 조립 |
| SharedWorkspaceRepository | 공용 CSV 오브젝트와 보고서·설정 메타데이터 읽기·쓰기 |
| AIReportService | 동의 후 집계 자료만 전송해 해석 문장 초안 생성 |

## 3. 공유 저장

GitHub Contents API로 `data/shared_experiment.csv`와 `data/shared_workspace.json`을 읽고 쓴다. Streamlit Secrets에 저장소 하나로 범위를 제한한 Fine-grained token을 보관한다. 앱 방문자는 로그인 없이 UI에서 데이터를 수정할 수 있으며 저장마다 Git commit이 생성된다. 공개 저장소이므로 업로드한 CSV와 이전 변경 내용이 공개 Git 기록에 남는다. 동시 저장이 충돌하면 새로고침 후 다시 저장하도록 안내한다. CSV 업로드는 10 MB까지 허용한다.

## 4. 분석 및 AI 경계

- 정리는 원본을 복제한 DataFrame에서 수행한다.
- 이상치 후보는 IQR 또는 Z 점수로 표시하고 자동으로 제거하지 않는다.
- 조건별 비교는 그룹별 count, mean, std, median, min, max를 제공한다. 자동 유의성 검정은 하지 않는다.
- 재현 코드는 화면 선택에 대응하는 일반 pandas 스크립트로 생성한다.
- AI 입력은 집계 기술 통계, 그룹별 요약, 이상치 개수와 파일명이다. 원본 행은 포함하지 않는다.
- OpenAI 결과는 초안이며 실험 맥락이나 인과성을 만들어내지 않도록 지침을 포함한다.

## 5. 배포

- 웹 앱: Streamlit Community Cloud
- 공유 파일: GitHub 저장소 Contents API
- 언어 모델: 선택 설정된 OpenAI API
- GitHub 쓰기 토큰과 선택적 AI 키: 호스팅 플랫폼 Secrets에 보관
- 로컬 서버 제공 및 실행: 금지
