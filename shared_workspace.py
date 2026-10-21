"""Shared cloud storage for a single openly editable project workspace."""

from __future__ import annotations

from typing import Any

from supabase import Client, create_client


class SharedWorkspaceRepository:
    """Persists a shared CSV and report metadata in Supabase."""

    WORKSPACE_ID = "main"
    BUCKET = "lab-shared"
    OBJECT_PATH = "workspace/experiment.csv"

    def __init__(self, url: str, anon_key: str) -> None:
        self.client: Client = create_client(url, anon_key)

    def read_csv(self) -> bytes | None:
        try:
            result = self.client.storage.from_(self.BUCKET).download(self.OBJECT_PATH)
            return bytes(result)
        except Exception as exc:
            message = str(exc).lower()
            if "not found" in message or "404" in message or "object" in message and "exist" in message:
                return None
            raise

    def write_csv(self, content: bytes) -> None:
        self.client.storage.from_(self.BUCKET).upload(
            self.OBJECT_PATH,
            content,
            file_options={"upsert": "true", "content-type": "text/csv"},
        )

    def read_metadata(self) -> dict[str, Any]:
        response = (
            self.client.table("lab_workspace")
            .select("payload")
            .eq("id", self.WORKSPACE_ID)
            .maybe_single()
            .execute()
        )
        return (response.data or {}).get("payload", {})

    def write_metadata(self, payload: dict[str, Any]) -> None:
        self.client.table("lab_workspace").upsert(
            {"id": self.WORKSPACE_ID, "payload": payload}, on_conflict="id"
        ).execute()
