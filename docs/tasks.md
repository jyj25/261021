# 작업 계획

## 작업 목록

| ID | 작업 | 산출물 | 상태 |
| --- | --- | --- | --- |
| T-01 | 실험 데이터 분석 범위 정의 | requirements.md | 완료 |
| T-02 | 객체 구조와 공개 저장 설계 | design.md | 완료 |
| T-03 | 정리, 비교, 이상치, 코드 생성 구현 | lab_data.py | 완료 |
| T-04 | 공유 저장과 공개 편집 권한 구현 | shared_workspace.py, infra/supabase.sql | 완료 |
| T-05 | AI 해석 및 보고서 초안 구현 | reporting.py, app.py | 완료 |
| T-06 | Streamlit/Supabase 호스팅 배포 | 공개 HTTPS URL | 대기 |
| T-07 | 호스팅 환경에서 공동 수정 및 AI 흐름 확인 | progress.md 증거 | 대기 |

## 다음 순서

1. Supabase 프로젝트에서 `infra/supabase.sql`을 실행한다.
2. GitHub 저장소를 Streamlit Community Cloud에 연결한다.
3. 앱 Secrets에 Supabase URL과 publishable key를 등록한다.
4. 필요할 때만 비용 한도가 설정된 OpenAI API 키를 추가한다.
5. 공개 가능한 CSV로 게시·수정·보고서 공유와 AI 동의 흐름을 호스팅에서 점검한다.

실제 배포 자격 증명과 계정 접근이 준비되어야 외부 공개 URL을 만들 수 있다. 로컬 서버를 대안으로 사용하지 않는다.
