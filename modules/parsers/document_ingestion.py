"""Provenance-preserving foundation for local document ingestion."""

from __future__ import annotations

import hashlib
import importlib
import io
import json
from collections.abc import Iterable
from html.parser import HTMLParser
from pathlib import Path
from typing import Literal, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field

DocumentType = Literal["pdf", "docx", "html", "txt", "json"]


class DocumentPage(BaseModel):
    """Text extracted from one logical or physical page."""

    model_config = ConfigDict(extra="forbid")

    number: int = Field(ge=1)
    text: str = ""


class DocumentSection(BaseModel):
    """Conservative section inferred without inventing document facts."""

    model_config = ConfigDict(extra="forbid")

    title: str
    content: str


class DocumentProvenance(BaseModel):
    """Origin metadata carried through downstream review flows."""

    model_config = ConfigDict(extra="forbid")

    source: str
    source_ref: str
    extraction_method: str


class IngestedDocument(BaseModel):
    """Standard, local-first output shared by future document adapters."""

    model_config = ConfigDict(extra="forbid")

    document_id: str
    document_type: DocumentType
    text_blocks: list[str] = Field(default_factory=list)
    pages: list[DocumentPage] = Field(default_factory=list)
    sections: list[DocumentSection] = Field(default_factory=list)
    source_hash: str
    warnings: list[str] = Field(default_factory=list)
    provenance: list[DocumentProvenance] = Field(default_factory=list)


class DocumentIngestionPipeline(Protocol):
    """Contract for deterministic document-to-text ingestion."""

    def ingest(
        self,
        filename: str,
        content: bytes,
        *,
        document_type: DocumentType | None = None,
    ) -> IngestedDocument: ...


class LocalDocumentIngestionPipeline:
    """Ingest supported files locally, retaining hash and extraction origin."""

    def ingest(
        self,
        filename: str,
        content: bytes,
        *,
        document_type: DocumentType | None = None,
    ) -> IngestedDocument:
        resolved_type = document_type or _type_from_filename(filename)
        digest = hashlib.sha256(content).hexdigest()
        pages, method, warnings = _extract(content, resolved_type)
        blocks = _blocks(page.text for page in pages)
        return IngestedDocument(
            document_id=f"document:{digest[:24]}",
            document_type=resolved_type,
            text_blocks=blocks,
            pages=pages,
            sections=_sections(blocks),
            source_hash=digest,
            warnings=warnings,
            provenance=[
                DocumentProvenance(
                    source="local_upload",
                    source_ref=filename,
                    extraction_method=method,
                )
            ],
        )


def _type_from_filename(filename: str) -> DocumentType:
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix not in {"pdf", "docx", "html", "htm", "txt", "json"}:
        raise ValueError("Formato não suportado. Use PDF, DOCX, HTML, TXT ou JSON.")
    return cast(DocumentType, "html" if suffix == "htm" else suffix)


def _extract(
    content: bytes, document_type: DocumentType
) -> tuple[list[DocumentPage], str, list[str]]:
    if document_type == "pdf":
        fitz = importlib.import_module("fitz")
        with fitz.open(stream=content, filetype="pdf") as document:
            pages = [
                DocumentPage(number=index + 1, text=page.get_text())
                for index, page in enumerate(document)
            ]
        return pages, "pymupdf", _empty_warning(pages)
    if document_type == "docx":
        document_module = importlib.import_module("docx")
        document = document_module.Document(io.BytesIO(content))
        text = "\n".join(paragraph.text for paragraph in document.paragraphs)
        pages = [DocumentPage(number=1, text=text)]
        return pages, "python-docx", _empty_warning(pages)

    decoded = content.decode("utf-8", errors="replace")
    warnings = ["Caracteres inválidos foram substituídos."] if "�" in decoded else []
    if document_type == "html":
        parser = _VisibleTextParser()
        parser.feed(decoded)
        decoded = "\n".join(parser.parts)
        method = "html.parser"
    elif document_type == "json":
        try:
            decoded = json.dumps(json.loads(decoded), ensure_ascii=False, indent=2)
        except json.JSONDecodeError as exc:
            raise ValueError("Documento JSON inválido.") from exc
        method = "json"
    else:
        method = "utf-8"
    pages = [DocumentPage(number=1, text=decoded)]
    return pages, method, [*warnings, *_empty_warning(pages)]


def _empty_warning(pages: list[DocumentPage]) -> list[str]:
    if any(page.text.strip() for page in pages):
        return []
    return ["Nenhum texto legível foi extraído; revise o arquivo original."]


def _blocks(texts: Iterable[str]) -> list[str]:
    blocks: list[str] = []
    for text in texts:
        for block in str(text).split("\n\n"):
            cleaned = "\n".join(line.strip() for line in block.splitlines() if line.strip())
            if cleaned:
                blocks.append(cleaned)
    return blocks


def _sections(blocks: list[str]) -> list[DocumentSection]:
    sections: list[DocumentSection] = []
    current_title = "Conteúdo"
    current: list[str] = []
    for block in blocks:
        if len(block) <= 80 and "\n" not in block and not block.endswith((".", ";")):
            if current:
                sections.append(DocumentSection(title=current_title, content="\n\n".join(current)))
            current_title = block
            current = []
        else:
            current.append(block)
    if current:
        sections.append(DocumentSection(title=current_title, content="\n\n".join(current)))
    return sections


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in {"script", "style", "noscript"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript"} and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        cleaned = data.strip()
        if cleaned and not self._ignored_depth:
            self.parts.append(cleaned)
