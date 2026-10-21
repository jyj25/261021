# AI 기반 실험 데이터 분석 및 보고서 작성

연구자가 CSV 실험 데이터를 공유 작업공간에 올리면 데이터 정리, 조건별 비교, 이상치 탐색, 그래프 생성과 분석 코드·보고서 초안 편집을 제공합니다. AI는 집계 결과를 바탕으로 해석 초안을 생성합니다.

## 배포 방식

이 프로젝트는 호스팅 환경에서만 실행합니다. 로컬 웹 서버를 만들거나 `localhost`로 실행하지 않습니다.

1. GitHub에 `starter` 폴더를 저장소로 올립니다.
2. Supabase 프로젝트에서 `infra/supabase.sql`을 실행합니다.
3. Streamlit Community Cloud에서 GitHub 저장소와 `starter/app.py`를 지정해 앱을 배포합니다.
4. Streamlit 앱의 Secrets에 `SUPABASE_URL`, `SUPABASE_ANON_KEY`를 등록합니다.
5. AI 해석을 사용하려면 `OPENAI_API_KEY`를 Secrets에 추가합니다. `OPENAI_MODEL`은 선택 설정이며 기본값은 `gpt-5-mini`입니다.
6. 배포된 HTTPS 주소를 공유합니다. 이 링크의 방문자는 작업공간 내용을 수정할 수 있습니다.

GitHub의 수정 권한은 저장소 설정으로 별도 관리합니다. 공개 기여자는 저장소를 포크해 수정본을 제안할 수 있습니다. 공유 앱은 공용 데이터, 분석 설정, 보고서 초안의 수정 권한을 모든 방문자에게 제공합니다.

## 공유 편집과 데이터 취급

이 앱은 로그인 없이 공용 Supabase 저장소를 사용합니다. 모든 방문자가 현재 CSV를 교체하고, 보고서와 분석 코드를 편집하고, 변경사항을 저장할 수 있습니다. 누구나 내용을 덮어쓰거나 지울 수 있으므로 기밀·개인정보·보존 의무가 있는 데이터를 넣지 마세요. 이 공개 권한은 `infra/supabase.sql`의 정책에 구현되어 있습니다.

AI 해석을 요청할 때 앱은 원본 행을 보내지 않고 집계 통계, 조건별 요약, 이상치 개수만 OpenAI API에 전송합니다. 전송 전 화면 동의를 받습니다. 외부 AI 호출에는 API 사용료가 발생할 수 있고, 공유 앱의 방문자 누구나 요청할 수 있으므로 비용 한도를 설정한 API 키만 연결하세요. AI 결과는 초안이며 연구자가 확인해야 합니다.

## 기능

- CSV 업로드 및 인코딩 판별, 결측값 처리와 중복 행 정리
- 조건별 수치 비교와 그룹 분포 그래프
- IQR 또는 Z 점수 기반 이상치 후보 표시
- 산점도, 선, 막대, 히스토그램, 상자 그림
- 선택 조건을 반영한 재현용 Python 코드 생성 및 편집
- 요약 기반 AI 해석 초안, Markdown 보고서 생성·편집·공유
- 공유 CSV, 코드, 보고서의 다운로드

## 프로젝트 구조

```text
starter/
├─ README.md
├─ AGENTS.md
├─ app.py
├─ lab_data.py
├─ reporting.py
├─ shared_workspace.py
├─ requirements.txt
├─ infra/supabase.sql
├─ .agents/skills/lab-data-reporting/SKILL.md
└─ docs/
   ├─ requirements.md
   ├─ design.md
   ├─ tasks.md
   └─ progress.md
```

## 문서와 작업 지침

요구사항, 설계, 할 일과 진행 현황은 `docs/`에서 확인합니다. 재사용 분석·보고서 규칙은 `.agents/skills/lab-data-reporting/SKILL.md`에 있습니다. 코드, 화면, 문서와 스킬에 이모지를 사용하지 않습니다.
