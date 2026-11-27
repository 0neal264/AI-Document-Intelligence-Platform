"""Local cache for validated raw chunk responses, keyed without secrets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from documind.extraction.provider import ExtractionResult


class ExtractionCache:
    """Store successful model responses on disk to make reruns resumable."""

    def __init__(self, directory: Path | str | None = Path(".documind-cache")) -> None:
        self.directory = Path(directory) if directory is not None else None

    @staticmethod
    def document_hash(pages: list[tuple[int, str]]) -> str:
        digest = hashlib.sha256()
        for number, text in pages:
            digest.update(str(number).encode("ascii"))
            digest.update(b"\0")
            digest.update(text.encode("utf-8"))
            digest.update(b"\0")
        return digest.hexdigest()

    def load(
        self,
        *,
        document_hash: str,
        chunk_index: int,
        profile: str,
        model: str | None,
        prompt_version: str,
        chunk_text: str,
    ) -> ExtractionResult | None:
        path = self._path(
            document_hash, chunk_index, profile, model, prompt_version, chunk_text
        )
        if path is None or not path.is_file():
            return None
        return ExtractionResult.model_validate_json(path.read_text(encoding="utf-8"))

    def save(
        self,
        result: ExtractionResult,
        *,
        document_hash: str,
        chunk_index: int,
        profile: str,
        model: str | None,
        prompt_version: str,
        chunk_text: str,
    ) -> None:
        path = self._path(
            document_hash, chunk_index, profile, model, prompt_version, chunk_text
        )
        if path is None:
            return
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_path = path.with_suffix(".tmp")
        temporary_path.write_text(result.model_dump_json(), encoding="utf-8")
        temporary_path.replace(path)

    def _path(
        self,
        document_hash: str,
        chunk_index: int,
        profile: str,
        model: str | None,
        prompt_version: str,
        chunk_text: str,
    ) -> Path | None:
        if self.directory is None:
            return None
        key = json.dumps(
            [
                document_hash,
                chunk_index,
                profile,
                model,
                prompt_version,
                hashlib.sha256(chunk_text.encode("utf-8")).hexdigest(),
            ],
            separators=(",", ":"),
        )
        name = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.directory / f"{name}.json"
