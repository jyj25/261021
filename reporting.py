"""Reusable Markdown report draft composition."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import pandas as pd


class ReportDraftService:
    """Assembles transparent analysis inputs into an editable report draft."""

    @staticmethod
    def create(
        dataset_name: str,
        source_rows: int,
        analyzed_rows: int,
        cleaning_log: list[str],
        summary: dict[str, Any],
        comparison: pd.DataFrame | None,
        condition: str | None,
        measure: str | None,
        outlier_column: str | None,
        outlier_count: int,
        ai_interpretation: str = "",
    ) -> str:
        statistics = summary["statistics"]
        stats_markdown = statistics.round(4).to_string() if not statistics.empty else "숫자형 열이 없습니다."
        comparison_markdown = comparison.to_string() if comparison is not None else "조건 비교를 실행하지 않았습니다."
        ai_section = ai_interpretation.strip() or "AI 해석 초안을 생성하지 않았습니다."
        return f"""# 실험 데이터 분석 보고서 초안

작성 시각: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}

## 데이터 개요

- 파일: {dataset_name}
- 원본 행 수: {source_rows}
- 분석 행 수: {analyzed_rows}
- 열 수: {len(summary['numeric_columns'])}개 숫자형 변수 포함

## 데이터 정리

""" + "\n".join(f"- {entry}" for entry in cleaning_log) + f"""

## 기술 통계

{stats_markdown}

## 조건별 비교

비교 변수: {condition or '미선택'} / 측정 변수: {measure or '미선택'}

{comparison_markdown}

## 이상치 탐색

- 탐색 열: {outlier_column or '미선택'}
- 표시된 행 수: {outlier_count}
- 탐색된 값은 삭제하지 않았으며 실험 기록과 함께 검토해야 합니다.

## 결과 해석 초안

{ai_section}

## 해석 한계와 검토 항목

- 본 문서는 탐색적 분석 초안이며 연구자의 검토와 수정이 필요합니다.
- 비교 결과만으로 인과관계나 통계적 유의성을 단정하지 않습니다.
- 단위, 실험 설계, 반복 구조, 측정 장비와 제외 기준을 확인해야 합니다.
- 결측값 처리와 이상치 판정 기준이 결과에 미치는 영향을 검토해야 합니다.
"""
