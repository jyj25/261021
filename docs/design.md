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
      -> shared_workspace.py: Supabase 공용 저장
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

Supabase Storage의 `lab-shared/workspace/experiment.csv`에 공용 CSV를 두고, `lab_workspace`의 `main` 행 JSONB에 보고서, 분석 코드, 설정을 저장한다. RLS 및 Storage 정책은 anon 역할의 읽기·쓰기·갱신·삭제를 허용한다. 누구든 동일한 작업공간을 편집하며 동시 수정은 마지막 저장이 덮어쓴다.

## 4. 분석 및 AI 경계

- 정리는 원본을 복제한 DataFrame에서 수행한다.
- 이상치 후보는 IQR 또는 Z 점수로 표시하고 자동으로 제거하지 않는다.
- 조건별 비교는 그룹별 count, mean, std, median, min, max를 제공한다. 자동 유의성 검정은 하지 않는다.
- 재현 코드는 화면 선택에 대응하는 일반 pandas 스크립트로 생성한다.
- AI 입력은 집계 기술 통계, 그룹별 요약, 이상치 개수와 파일명이다. 원본 행은 포함하지 않는다.
- OpenAI 결과는 초안이며 실험 맥락이나 인과성을 만들어내지 않도록 지침을 포함한다.

## 5. 배포

- 웹 앱: Streamlit Community Cloud
- 공유 데이터베이스 및 파일: Supabase
- 언어 모델: 선택 설정된 OpenAI API
- 비밀값: 호스팅 플랫폼 Secrets에 보관
- 로컬 서버 제공 및 실행: 금지
