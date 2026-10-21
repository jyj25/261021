"""Shared workspace storage backed by files in the project's GitHub repository."""

from __future__ import annotations

import base64
import json
from typing import Any

import requests


class SharedWorkspaceRepository:
    """Reads and commits shared workspace files through GitHub's Contents API."""

    DATA_PATH = "data/shared_experiment.csv"
    METADATA_PATH = "data/shared_workspace.json"
    MAX_CSV_BYTES = 10 * 1024 * 1024

    def __init__(self, token: str, repository: str, branch: str = "main") -> None:
        self.token = token
        self.repository = repository
        self.branch = branch
        self.api_url = f"https://api.github.com/repos/{repository}/contents"
        self.headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        }

    def _read_file(self, path: str) -> tuple[bytes | None, str | None]:
        response = requests.get(
            f"{self.api_url}/{path}",
            headers=self.headers,
            params={"ref": self.branch},
            timeout=20,
        )
        if response.status_code == 404:
            return None, None
        response.raise_for_status()
        result = response.json()
        if result.get("encoding") == "base64":
            content = base64.b64decode(result["content"])
        else:
            raw_headers = {**self.headers, "Accept": "application/vnd.github.raw+json"}
            raw_response = requests.get(
                f"{self.api_url}/{path}",
                headers=raw_headers,
                params={"ref": self.branch},
                timeout=30,
            )
            raw_response.raise_for_status()
            content = raw_response.content
        return content, result["sha"]

    def _write_file(self, path: str, content: bytes, message: str) -> None:
        _, sha = self._read_file(path)
        payload: dict[str, Any] = {
            "message": message,
            "content": base64.b64encode(content).decode("ascii"),
            "branch": self.branch,
        }
        if sha:
            payload["sha"] = sha
        response = requests.put(
            f"{self.api_url}/{path}",
            headers=self.headers,
            json=payload,
            timeout=30,
        )
        if response.status_code == 409:
            raise RuntimeError("다른 방문자가 동시에 저장했습니다. 새로고침한 뒤 다시 저장해 주세요.")
        response.raise_for_status()

    def read_csv(self) -> bytes | None:
        content, _ = self._read_file(self.DATA_PATH)
        return content

    def write_csv(self, content: bytes) -> None:
        if len(content) > self.MAX_CSV_BYTES:
            raise ValueError("공유 CSV는 10 MB 이하만 게시할 수 있습니다.")
        self._write_file(self.DATA_PATH, content, "Update shared experiment CSV")

    def read_metadata(self) -> dict[str, Any]:
        content, _ = self._read_file(self.METADATA_PATH)
        if content is None:
            return {}
        return json.loads(content.decode("utf-8"))

    def write_metadata(self, payload: dict[str, Any]) -> None:
        content = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
        self._write_file(self.METADATA_PATH, content, "Update shared analysis and report")
