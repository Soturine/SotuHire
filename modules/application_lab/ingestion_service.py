"""Resume ingestion adapter from secure document extraction to canonical review drafts."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal, cast

from modules.application_lab.models import MasterResume, ResumeEntry, ResumeSection, utc_now
from modules.parsers.document_ingestion import IngestedDocument, LocalDocumentIngestionPipeline
from modules.storage.database import connect_database, default_database_path
from modules.storage.migrations import ensure_database


class ResumeIngestionService:
    def __init__(self, database_path: str | Path | None = None) -> None:
        self.database_path = (
            Path(database_path) if database_path is not None else default_database_path()
        )
        self.pipeline = LocalDocumentIngestionPipeline()

    def ingest(self, filename: str, content: bytes) -> tuple[IngestedDocument, MasterResume]:
        """Extract locally, persist provenance and return an unconfirmed editor draft."""
        document = self.pipeline.ingest(filename, content)
        source_refs = [item.source_ref for item in document.provenance]
        sections = [
            ResumeSection(
                section_type="imported",
                title=section.title,
                entries=[
                    ResumeEntry(
                        entry_type="imported_block",
                        title=section.title,
                        content=section.content,
                        source_refs=source_refs,
                        confirmed_by_user=False,
                    )
                ],
            )
            for section in document.sections
        ]
        if not sections and document.text_blocks:
            sections = [
                ResumeSection(
                    section_type="imported",
                    title="Conteúdo importado",
                    entries=[
                        ResumeEntry(
                            entry_type="imported_block",
                            content=block,
                            source_refs=source_refs,
                            confirmed_by_user=False,
                        )
                        for block in document.text_blocks
                    ],
                )
            ]
        source_type = cast(
            Literal["manual", "profile", "pdf", "docx", "txt", "json_resume"],
            {"json": "json_resume", "html": "txt"}.get(
                document.document_type, document.document_type
            ),
        )
        draft = MasterResume(
            master_resume_id=f"master-{document.source_hash[:24]}",
            title=Path(filename).stem or "Currículo importado",
            raw_text="\n\n".join(document.text_blocks),
            source_type=source_type,
            source_refs=source_refs,
            sections=sections,
            validation_warnings=[
                *document.warnings,
                "Conteúdo importado permanece sourced até confirmação explícita no editor.",
            ],
        )
        self._save_ingestion(document)
        return document, draft

    def _save_ingestion(self, document: IngestedDocument) -> None:
        ensure_database(self.database_path)
        now = utc_now().isoformat()
        with connect_database(self.database_path) as connection:
            connection.execute(
                """INSERT INTO document_ingestions
                (ingestion_id, document_id, file_name, media_type, byte_size, content_hash,
                 status, provenance, extraction_result, warnings, created_at)
                VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(ingestion_id) DO NOTHING""",
                (
                    document.document_id,
                    str(document.provenance[0].location.get("file_name", ""))
                    if document.provenance
                    else "",
                    document.media_type,
                    document.byte_size,
                    document.source_hash,
                    document.status,
                    json.dumps(
                        [item.model_dump(mode="json") for item in document.provenance],
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    json.dumps(
                        document.model_dump(mode="json"),
                        ensure_ascii=False,
                        sort_keys=True,
                    ),
                    json.dumps(document.warnings, ensure_ascii=False),
                    now,
                ),
            )


__all__ = ["ResumeIngestionService"]
