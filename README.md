# AI 기반 실험 데이터 분석 및 보고서 작성

연구자가 CSV 실험 데이터를 공유 작업공간에 올리면 데이터 정리, 조건별 비교, 이상치 탐색, 그래프 생성과 분석 코드·보고서 초안 편집을 제공합니다. AI는 집계 결과를 바탕으로 해석 초안을 생성합니다.

## 배포 방식

이 프로젝트는 호스팅 환경에서만 실행합니다. 로컬 웹 서버를 만들거나 `localhost`로 실행하지 않습니다.

1. GitHub 저장소 `jyj25/261021`에 프로젝트 파일이 있습니다.
2. GitHub에서 Fine-grained personal access token을 만듭니다. Repository access는 `Only select repositories`로 두고 `jyj25/261021`만 선택합니다. Repository permissions에서 `Contents`를 `Read and write`로 설정합니다. 토큰은 배포 비밀 설정에만 입력합니다.
3. Streamlit Community Cloud에 GitHub 계정으로 로그인하고 저장소 `jyj25/261021`, 브랜치 `main`, 진입 파일 `app.py`를 지정해 앱을 배포합니다.
4. 배포 전 Advanced settings의 Secrets에 다음 설정을 넣습니다.

```toml
GITHUB_TOKEN = "저장소 하나에만 권한을 준 Fine-grained token"
OPENAI_API_KEY = "선택: OpenAI API key"
OPENAI_MODEL = "gpt-5-mini"
```

`OPENAI_API_KEY`는 AI 해석을 사용할 때만 필요합니다. 실제 키는 GitHub 파일이나 채팅에 넣지 말고 Streamlit 배포 설정에만 입력합니다.
5. 배포된 HTTPS 주소를 공유합니다. 이 링크의 방문자는 작업공간 내용을 수정할 수 있습니다.

GitHub의 수정 권한은 저장소 설정으로 별도 관리합니다. 공개 기여자는 저장소를 포크해 수정본을 제안할 수 있습니다. 공유 앱은 공용 데이터, 분석 설정, 보고서 초안의 수정 권한을 모든 방문자에게 제공합니다.

## 공유 편집과 데이터 취급

이 앱은 로그인 없이 GitHub 저장소에 있는 공용 CSV와 작업공간 파일을 사용합니다. 모든 방문자가 현재 CSV를 교체하고, 보고서와 분석 코드를 편집하고, 변경사항을 저장할 수 있습니다. 업로드 CSV와 수정 내용은 공개 저장소에 커밋되며 교체 전 자료도 Git 기록에 남습니다. 누구나 앱을 통해 공유 내용을 덮어쓸 수 있으므로 기밀·개인정보·보존 의무가 있는 데이터는 올리지 마세요. 토큰은 앱 서버의 Secrets에만 저장되며 방문자에게 전달되지 않습니다.

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
├─ .agents/skills/lab-data-reporting/SKILL.md
└─ docs/
   ├─ requirements.md
   ├─ design.md
   ├─ tasks.md
   └─ progress.md
```

## 문서와 작업 지침

요구사항, 설계, 할 일과 진행 현황은 `docs/`에서 확인합니다. 재사용 분석·보고서 규칙은 `.agents/skills/lab-data-reporting/SKILL.md`에 있습니다. 코드, 화면, 문서와 스킬에 이모지를 사용하지 않습니다.
