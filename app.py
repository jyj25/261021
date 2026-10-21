"""Public, cloud-hosted collaborative laboratory data analysis workspace."""

from __future__ import annotations

import json
from typing import Any

import plotly.express as px
import pandas as pd
import streamlit as st

from lab_data import AIReportService, ExperimentDataService, LabDataError
from reporting import ReportDraftService
from shared_workspace import SharedWorkspaceRepository


class VisualizationApp:
    """Coordinates cloud persistence, analysis controls, and report views."""

    def __init__(self) -> None:
        self.data_service = ExperimentDataService()
        self.report_service = ReportDraftService()
        self.ai_service = AIReportService(
            api_key=self._secret("OPENAI_API_KEY"),
            model=self._secret("OPENAI_MODEL") or None,
        )
        self.repository = self._create_repository()

    @staticmethod
    def _secret(name: str, default: str = "") -> str:
        try:
            return str(st.secrets.get(name, default))
        except Exception:
            return default

    def _create_repository(self) -> SharedWorkspaceRepository | None:
        url = self._secret("SUPABASE_URL")
        key = self._secret("SUPABASE_PUBLISHABLE_KEY")
        if not url or not key:
            return None
        return SharedWorkspaceRepository(url, key)

    @staticmethod
    def _option_index(options, selected) -> int:
        try:
            return options.index(selected)
        except (ValueError, AttributeError):
            return 0

    def run(self) -> None:
        st.set_page_config(page_title="AI 실험 데이터 분석", layout="wide")
        st.title("AI 기반 실험 데이터 분석 및 보고서 작성")
        st.caption("공유 편집이 가능한 실험 데이터 분석 작업공간")
        st.warning(
            "이 작업공간은 공개 편집 공간입니다. 링크에 접근한 누구나 데이터를 교체하고 보고서와 분석 설정을 수정할 수 있습니다. "
            "비공개·개인정보·기밀 실험 데이터는 올리지 마세요."
        )
        if self.repository is None:
            self._show_deployment_setup()
            return

        try:
            metadata = self.repository.read_metadata()
            shared_bytes = self.repository.read_csv()
        except Exception as exc:
            st.error(f"공유 데이터 저장소에 연결하지 못했습니다: {exc}")
            return

        if st.button("공유 변경사항 새로고침"):
            self._clear_editor_state()
            st.rerun()

        self._show_upload_form(metadata)
        if shared_bytes is None:
            st.info("공유 작업공간에 데이터가 없습니다. 공개 가능한 CSV를 올려 시작해 주세요.")
            return

        try:
            dataset = self.data_service.load_csv("shared_experiment.csv", shared_bytes)
        except LabDataError as exc:
            st.error(f"공유 CSV를 읽을 수 없습니다: {exc}")
            return

        self._show_workspace(dataset, metadata)

    @staticmethod
    def _show_deployment_setup() -> None:
        st.error("클라우드 공유 저장소가 연결되지 않았습니다.")
        st.markdown(
            "Streamlit 호스팅 비밀 설정에 `SUPABASE_URL`과 `SUPABASE_PUBLISHABLE_KEY`를 등록하고 "
            "`infra/supabase.sql`을 Supabase 프로젝트에서 실행하세요. 앱은 로컬 서버 모드로 실행하지 않습니다."
        )

    def _show_upload_form(self, metadata: dict[str, Any]) -> None:
        st.subheader("공유 데이터 교체")
        st.caption("업로드 후 게시하면 기존 공유 CSV와 보고서 초안이 새 자료로 교체됩니다.")
        uploaded = st.file_uploader("CSV 실험 데이터", type=["csv", "tsv", "txt"])
        if uploaded and st.button("공유 작업공간에 게시", type="primary"):
            try:
                candidate = self.data_service.load_csv(uploaded.name, uploaded.getvalue())
                self.repository.write_csv(uploaded.getvalue())
                self.repository.write_metadata(
                    {"source_name": uploaded.name, "report_markdown": "", "analysis_code": "", "ai_interpretation": ""}
                )
                self._clear_editor_state()
                st.success(f"{candidate.row_count:,}개 행을 공유 작업공간에 게시했습니다.")
                st.rerun()
            except Exception as exc:
                st.error(f"게시하지 못했습니다: {exc}")

    @staticmethod
    def _clear_editor_state() -> None:
        for key in (
            "report_editor", "code_editor", "condition_col", "condition_measure",
            "outlier_col", "outlier_method", "모든 값이 비어 있는 행 제거",
            "중복 행 제거", "결측값 처리",
        ):
            st.session_state.pop(key, None)

    def _show_workspace(self, dataset, metadata: dict[str, Any]) -> None:
        source_name = metadata.get("source_name", dataset.name)
        st.session_state["persisted_analysis"] = metadata.get("analysis", {})
        st.subheader(f"공유 분석 자료: {source_name}")
        st.caption("변경한 정리 설정과 보고서는 공유 저장소에 저장하면 다른 방문자에게도 표시됩니다.")

        with st.expander("데이터 정리", expanded=True):
            saved_cleaning = metadata.get("analysis", {}).get("cleaning", {})
            drop_empty = st.checkbox(
                "모든 값이 비어 있는 행 제거", value=saved_cleaning.get("drop_empty", True)
            )
            remove_duplicates = st.checkbox(
                "중복 행 제거", value=saved_cleaning.get("remove_duplicates", False)
            )
            missing_labels = {
                "유지": "keep",
                "결측값 포함 행 제거": "drop_rows",
                "숫자형 열 중앙값 대체": "median",
            }
            missing_options = list(missing_labels)
            selected_missing = next(
                (label for label, value in missing_labels.items() if value == saved_cleaning.get("missing_strategy")),
                missing_options[0],
            )
            missing_label = st.selectbox(
                "결측값 처리", missing_options, index=self._option_index(missing_options, selected_missing)
            )
            cleaning = {
                "drop_empty": drop_empty,
                "remove_duplicates": remove_duplicates,
                "missing_strategy": missing_labels[missing_label],
            }

        cleaned, cleaning_log = self.data_service.clean(
            dataset.frame,
            drop_empty=drop_empty,
            remove_duplicates=remove_duplicates,
            missing_strategy=missing_labels[missing_label],
        )
        if cleaned.empty:
            st.error("선택한 정리 조건을 적용한 뒤 분석할 행이 남지 않았습니다.")
            return
        summary = self.data_service.summary(cleaned)
        if not summary["numeric_columns"]:
            st.error("숫자형 측정 열을 찾지 못했습니다. CSV의 소수점·구분 기호 형식을 확인해 주세요.")
            return

        stats_tab, comparison_tab, outlier_tab, chart_tab, report_tab = st.tabs(
            ["요약", "조건별 비교", "이상치 탐색", "그래프", "코드와 보고서"]
        )
        with stats_tab:
            a, b, c = st.columns(3)
            a.metric("분석 행", f"{len(cleaned):,}")
            b.metric("변수 열", f"{len(cleaned.columns):,}")
            c.metric("숫자형 변수", f"{len(summary['numeric_columns']):,}")
            st.dataframe(summary["statistics"].round(5), use_container_width=True)
            st.markdown("#### 결측값 현황")
            st.dataframe(summary["missing"], use_container_width=True)
            st.markdown("#### 정리 이력")
            for entry in cleaning_log:
                st.write(f"- {entry}")
            st.dataframe(cleaned.head(500), use_container_width=True, hide_index=True)

        comparison, condition, measure = self._comparison_view(cleaned, comparison_tab)
        outliers, outlier_column, outlier_method = self._outlier_view(cleaned, outlier_tab)
        chart_html = self._chart_view(cleaned, chart_tab)

        with report_tab:
            self._report_view(
                dataset,
                cleaned,
                cleaning,
                cleaning_log,
                summary,
                comparison,
                condition,
                measure,
                outliers,
                outlier_column,
                outlier_method,
                metadata,
            )

    def _comparison_view(self, frame, tab):
        with tab:
            st.markdown("조건 열과 측정값을 선택하면 조건별 기술 통계를 비교합니다.")
            saved_analysis = st.session_state.get("persisted_analysis", {})
            condition = st.selectbox(
                "조건 열", frame.columns,
                index=self._option_index(list(frame.columns), saved_analysis.get("condition")),
                key="condition_col",
            )
            measures = frame.select_dtypes(include="number").columns.tolist()
            measure = st.selectbox(
                "측정값", measures,
                index=self._option_index(measures, saved_analysis.get("measure")),
                key="condition_measure",
            )
            try:
                result = self.data_service.compare_conditions(frame, condition, measure)
                st.dataframe(result, use_container_width=True)
                chart = px.box(frame, x=condition, y=measure, points="all", title=f"{condition} 조건별 {measure}")
                st.plotly_chart(chart, use_container_width=True)
            except LabDataError as exc:
                st.info(str(exc))
                result = pd.DataFrame()
        return result, condition, measure

    def _outlier_view(self, frame, tab):
        with tab:
            numeric = frame.select_dtypes(include="number").columns.tolist()
            saved_analysis = st.session_state.get("persisted_analysis", {})
            column = st.selectbox(
                "탐색할 열", numeric,
                index=self._option_index(numeric, saved_analysis.get("outlier_column")),
                key="outlier_col",
            )
            methods = ["IQR", "Z 점수"]
            method = st.selectbox(
                "탐색 방식", methods,
                index=self._option_index(methods, saved_analysis.get("outlier_method")),
                key="outlier_method",
            )
            outliers = self.data_service.find_outliers(frame, column, method)
            st.metric("표시된 이상치 후보", f"{len(outliers):,}행")
            st.caption("표시는 검토 후보이며, 자동으로 제거하지 않습니다.")
            st.dataframe(outliers, use_container_width=True, hide_index=True)
        return outliers, column, method

    @staticmethod
    def _chart_view(frame, tab) -> str:
        with tab:
            chart_type = st.selectbox("그래프 종류", ["산점도", "선 그래프", "막대 그래프", "히스토그램", "상자 그림"])
            numeric = frame.select_dtypes(include="number").columns.tolist()
            if chart_type in ("히스토그램", "상자 그림"):
                measure = st.selectbox("측정 열", numeric, key="chart_measure")
                group_options = ["구분 없음", *[column for column in frame.columns if column != measure]]
                group_choice = st.selectbox("조건별 색상", group_options)
                color = None if group_choice == "구분 없음" else group_choice
                figure = (
                    px.histogram(frame, x=measure, color=color, title=f"{measure} 분포")
                    if chart_type == "히스토그램"
                    else px.box(frame, y=measure, color=color, title=f"{measure} 분포")
                )
            else:
                x = st.selectbox("x축", frame.columns, key="chart_x")
                ys = [column for column in numeric if column != x] or numeric
                y = st.selectbox("y축", ys, key="chart_y")
                color_options = ["구분 없음", *[column for column in frame.columns if column not in (x, y)]]
                color_choice = st.selectbox("색상 구분", color_options)
                color = None if color_choice == "구분 없음" else color_choice
                maker = {"산점도": px.scatter, "선 그래프": px.line, "막대 그래프": px.bar}[chart_type]
                figure = maker(frame, x=x, y=y, color=color, title=f"{y}와 {x}")
            st.plotly_chart(figure, use_container_width=True)
            html = figure.to_html(include_plotlyjs="cdn", full_html=True)
            st.download_button("그래프 HTML 내려받기", html, "experiment_chart.html", "text/html")
        return html

    def _report_view(
        self,
        dataset,
        cleaned,
        cleaning,
        cleaning_log,
        summary,
        comparison,
        condition,
        measure,
        outliers,
        outlier_column,
        outlier_method,
        metadata,
    ) -> None:
        st.markdown("#### 재현 가능한 분석 코드")
        code = self.data_service.reproducible_code(
            condition, measure, outlier_column, cleaning, outlier_method
        )
        st.code(code, language="python")
        st.download_button("분석 코드 내려받기", code, "analysis.py", "text/x-python")

        st.markdown("#### AI 결과 해석 초안")
        st.caption("AI에는 원본 행이 아니라 집계 통계와 비교표만 전달합니다. 아래 동의 후 요청을 누르면 OpenAI API로 전송됩니다.")
        consent = st.checkbox("집계 분석 결과를 OpenAI API에 보내 해석 초안을 생성하는 데 동의합니다.")
        current_analysis = {
            "cleaning": cleaning,
            "condition": condition,
            "measure": measure,
            "outlier_column": outlier_column,
            "outlier_method": outlier_method,
        }
        is_current = metadata.get("analysis") == current_analysis
        ai_text = (
            metadata.get("ai_interpretation", "")
            if metadata.get("ai_analysis") == current_analysis
            else ""
        )
        if st.button("AI 해석 초안 생성", disabled=not consent):
            if not self.ai_service.is_configured:
                st.error("배포 환경 비밀 설정에 OPENAI_API_KEY가 필요합니다.")
            else:
                try:
                    metrics = {
                        "row_count": len(cleaned),
                        "descriptive_statistics": summary["statistics"].round(5).to_dict(),
                        "condition_comparison": comparison.round(5).to_dict(),
                        "outlier_method": outlier_method,
                        "outlier_column": outlier_column,
                        "outlier_count": len(outliers),
                    }
                    ai_text = self.ai_service.generate_interpretation(metrics)
                    metadata["ai_interpretation"] = ai_text
                    metadata["ai_analysis"] = current_analysis
                    self.repository.write_metadata(metadata)
                    st.rerun()
                except Exception as exc:
                    st.error(f"AI 초안을 생성하지 못했습니다: {exc}")
        if ai_text:
            st.markdown(ai_text)

        comparison_for_report = comparison.copy()
        report = self.report_service.create(
            dataset_name=metadata.get("source_name", dataset.name),
            source_rows=len(dataset.frame),
            analyzed_rows=len(cleaned),
            cleaning_log=cleaning_log,
            summary=summary,
            comparison=comparison_for_report,
            condition=condition,
            measure=measure,
            outlier_column=f"{outlier_column} ({outlier_method})",
            outlier_count=len(outliers),
            ai_interpretation=ai_text,
        )
        report = st.text_area(
            "공유 보고서 초안 편집",
            value=(metadata.get("report_markdown") if is_current else "") or report,
            height=420,
            key="report_editor",
        )
        code = st.text_area(
            "공유 분석 코드 편집",
            value=(metadata.get("analysis_code") if is_current else "") or code,
            height=220,
            key="code_editor",
        )
        if st.button("보고서와 코드 변경 공유", type="primary"):
            metadata["report_markdown"] = report
            metadata["analysis_code"] = code
            metadata["analysis"] = current_analysis
            self.repository.write_metadata(metadata)
            st.success("보고서와 분석 코드를 공유 작업공간에 저장했습니다.")
        st.download_button("보고서 Markdown 내려받기", report, "experiment_report.md", "text/markdown")


if __name__ == "__main__":
    VisualizationApp().run()
