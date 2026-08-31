"""Concrete ``ResultSink`` writing flat files.

Swapping this for a database sink later means writing another ``ResultSink`` and
changing one line in the composition root — the pipeline is untouched (OCP/DIP).
"""

from pathlib import Path, PurePath

from app.domain.models import DocumentResult
from app.domain.ports import ResultSink


class JsonTextSink(ResultSink):
    """Write ``<name>.json`` (full result) and ``<name>.txt`` (plain text)."""

    def __init__(self, output_dir: Path) -> None:
        self._output_dir = output_dir
        self._output_dir.mkdir(parents=True, exist_ok=True)

    def save(self, result: DocumentResult) -> None:
        stem = PurePath(result.source_filename).stem
        base = self._output_dir / stem
        base.with_suffix(".json").write_text(
            result.model_dump_json(indent=2), encoding="utf-8"
        )
        base.with_suffix(".txt").write_text(result.full_text, encoding="utf-8")
