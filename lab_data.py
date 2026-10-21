"""Data preparation, exploratory analysis, and AI draft generation."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from io import BytesIO
from typing import Any

import pandas as pd
from openai import OpenAI


class LabDataError(ValueError):
    """Raised when uploaded laboratory data cannot be analyzed."""


@dataclass
class ExperimentDataset:
    """Parsed experiment data and source details."""

    name: str
    frame: pd.DataFrame
    encoding: str

    @property
    def numeric_columns(self) -> list[str]:
        return self.frame.select_dtypes(include="number").columns.tolist()


class ExperimentDataService:
    """Validates and transforms tabular data without changing the source frame."""

    MAX_FILE_BYTES = 20 * 1024 * 1024
    MAX_ROWS = 250_000

    def load_csv(self, name: str, content: bytes) -> ExperimentDataset:
        if not content:
            raise LabDataError("파일이 비어 있습니다.")
        if len(content) > self.MAX_FILE_BYTES:
            raise LabDataError("파일 크기는 20 MB 이하로 제한됩니다.")

        frame = None
        encoding_used = ""
        for encoding in ("utf-8-sig", "cp949", "utf-8"):
            try:
                frame = pd.read_csv(BytesIO(content), encoding=encoding, sep=None, engine="python")
                encoding_used = encoding
                break
            except (UnicodeDecodeError, pd.errors.ParserError, ValueError):
                continue
        if frame is None or frame.empty:
            raise LabDataError("CSV를 읽지 못했습니다. 인코딩, 구분 기호, 열 머리글을 확인해 주세요.")
        if len(frame.index) > self.MAX_ROWS:
            raise LabDataError("행 수는 250,000개 이하로 제한됩니다.")

        frame.columns = [str(column).strip() for column in frame.columns]
        if any(not column for column in frame.columns):
            raise LabDataError("이름이 비어 있는 열이 있습니다. CSV 첫 행을 확인해 주세요.")
        if frame.columns.duplicated().any():
            raise LabDataError("중복된 열 이름이 있습니다. 열 이름을 고유하게 바꿔 주세요.")
        return ExperimentDataset(name, frame, encoding_used)

    @staticmethod
    def clean(
        frame: pd.DataFrame,
        drop_empty: bool = True,
        remove_duplicates: bool = False,
        missing_strategy: str = "keep",
    ) -> tuple[pd.DataFrame, list[str]]:
        cleaned = frame.copy()
        changes: list[str] = []
        if drop_empty:
            before = len(cleaned)
            cleaned = cleaned.dropna(how="all")
            changes.append(f"빈 행 {before - len(cleaned)}개 제거")
        if remove_duplicates:
            before = len(cleaned)
            cleaned = cleaned.drop_duplicates()
            changes.append(f"중복 행 {before - len(cleaned)}개 제거")
        if missing_strategy == "drop_rows":
            before = len(cleaned)
            cleaned = cleaned.dropna()
            changes.append(f"결측값 포함 행 {before - len(cleaned)}개 제거")
        elif missing_strategy == "median":
            numeric = cleaned.select_dtypes(include="number").columns
            counts = int(cleaned[numeric].isna().sum().sum()) if len(numeric) else 0
            if len(numeric):
                cleaned.loc[:, numeric] = cleaned[numeric].fillna(cleaned[numeric].median())
            changes.append(f"숫자형 열 결측값 {counts}개를 열별 중앙값으로 대체")
        elif missing_strategy != "keep":
            raise LabDataError("지원하지 않는 결측값 처리 방식입니다.")
        if not changes:
            changes.append("데이터를 변경하지 않음")
        return cleaned, changes

    @staticmethod
    def summary(frame: pd.DataFrame) -> dict[str, Any]:
        numeric = frame.select_dtypes(include="number").columns.tolist()
        statistics = frame[numeric].describe().T if numeric else pd.DataFrame()
        missing = pd.DataFrame({"결측값 수": frame.isna().sum()})
        missing["결측 비율 (%)"] = (frame.isna().mean() * 100).round(2)
        return {"statistics": statistics, "missing": missing, "numeric_columns": numeric}

    @staticmethod
    def compare_conditions(frame: pd.DataFrame, condition: str, measure: str) -> pd.DataFrame:
        if condition not in frame.columns or measure not in frame.columns:
            raise LabDataError("비교에 사용할 열을 찾을 수 없습니다.")
        data = frame[[condition, measure]].dropna()
        if data.empty:
            raise LabDataError("비교할 유효한 값이 없습니다.")
        return (
            data.groupby(condition, dropna=False)[measure]
            .agg(["count", "mean", "std", "median", "min", "max"])
            .round(5)
        )

    @staticmethod
    def find_outliers(frame: pd.DataFrame, column: str, method: str = "IQR") -> pd.DataFrame:
        values = pd.to_numeric(frame[column], errors="coerce")
        valid = values.dropna()
        if valid.empty:
            return frame.iloc[0:0].copy()
        if method == "IQR":
            q1, q3 = valid.quantile([0.25, 0.75])
            spread = q3 - q1
            mask = (values < q1 - 1.5 * spread) | (values > q3 + 1.5 * spread)
        else:
            standard_deviation = valid.std(ddof=0)
            if standard_deviation == 0 or pd.isna(standard_deviation):
                return frame.iloc[0:0].copy()
            mask = ((values - valid.mean()).abs() / standard_deviation) > 3
        return frame.loc[mask.fillna(False)].copy()

    @staticmethod
    def reproducible_code(
        condition: str | None,
        measure: str,
        outlier_column: str,
        cleaning: dict[str, Any],
        outlier_method: str = "IQR",
    ) -> str:
        lines = ["import pandas as pd", "", "data = pd.read_csv('experiment.csv')"]
        if cleaning.get("drop_empty", True):
            lines.append("data = data.dropna(how='all')")
        if cleaning.get("remove_duplicates", False):
            lines.append("data = data.drop_duplicates()")
        strategy = cleaning.get("missing_strategy", "keep")
        if strategy == "drop_rows":
            lines.append("data = data.dropna()")
        elif strategy == "median":
            lines.append("numeric = data.select_dtypes(include='number').columns")
            lines.append("data.loc[:, numeric] = data[numeric].fillna(data[numeric].median())")
        lines.extend(["", f"# 이상치 탐색: {outlier_method}"])
        if condition:
            lines.append(
                f"comparison = data.groupby({condition!r})[{measure!r}].agg(['count', 'mean', 'std', 'median'])"
            )
        else:
            lines.append("comparison = None  # 비교 조건 열을 선택하지 않았습니다.")
        lines.append(f"values = pd.to_numeric(data[{outlier_column!r}], errors='coerce')")
        if outlier_method == "Z 점수":
            lines.extend([
                "z_score = (values - values.mean()) / values.std(ddof=0)",
                "outliers = data[z_score.abs() > 3]",
            ])
        else:
            lines.extend([
                "q1, q3 = values.quantile([0.25, 0.75])",
                "iqr = q3 - q1",
                "outliers = data[(values < q1 - 1.5 * iqr) | (values > q3 + 1.5 * iqr)]",
            ])
        lines.extend(["print(comparison)", "print(outliers)"])
        return "\n".join(lines) + "\n"


class AIReportService:
    """Creates a cautious interpretation draft from aggregate metrics only."""

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-5-mini")

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_interpretation(self, metrics: dict[str, Any]) -> str:
        if not self.api_key:
            raise LabDataError("AI 보고서 기능을 사용하려면 호스팅 비밀 설정에 OPENAI_API_KEY를 등록해 주세요.")
        client = OpenAI(api_key=self.api_key)
        response = client.responses.create(
            model=self.model,
            instructions=(
                "당신은 과학적 보고서 초안 작성 보조자입니다. 한국어로 관찰 결과와 한계를 구분하세요. "
                "인과관계, 통계적 유의성, 실험 맥락을 근거 없이 주장하지 마세요. "
                "집계값만 근거로 사용하고 불확실한 내용은 확인 질문으로 표시하세요."
            ),
            input=json.dumps(metrics, ensure_ascii=False, default=str),
            max_output_tokens=1200,
        )
        return response.output_text
