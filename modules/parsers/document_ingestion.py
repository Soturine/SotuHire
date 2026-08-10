"""Secure, provenance-preserving local document ingestion."""

from __future__ import annotations

import hashlib
import importlib
import io
import json
import zipfile
from collections.abc import Iterable
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Literal, Protocol, cast

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from modules.schemas.json_resume import JSONResume

DocumentType = Literal["pdf", "docx", "html", "txt", "json"]
IngestionStatus = Literal["accepted", "needs_review"]

MAX_DOCUMENT_BYTES = 10 * 1024 * 1024
MAX_EXTRACTED_CHARACTERS = 2_000_000
MAX_PDF_PAGES = 200
MAX_ZIP_ENTRIES = 2_000
MAX_ZIP_UNCOMPRESSED_BYTES = 40 * 1024 * 1024
MAX_COMPRESSION_RATIO = 250


class DocumentPage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    number: int = Field(ge=1)
    text: str = ""


class DocumentSection(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    content: str


class DocumentProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    source: str
    source_ref: str
    extraction_method: str
    location: dict[str, str | int] = Field(default_factory=dict)


class IngestedDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    document_type: DocumentType
    media_type: str
    byte_size: int = Field(ge=0)
    status: IngestionStatus
    text_blocks: list[str] = Field(default_factory=list)
    pages: list[DocumentPage] = Field(default_factory=list)
    sections: list[DocumentSection] = Field(default_factory=list)
    structured_data: dict[str, Any] = Field(default_factory=dict)
    source_hash: str
    warnings: list[str] = Field(default_factory=list)
    provenance: list[DocumentProvenance] = Field(default_factory=list)


class DocumentIngestionPipeline(Protocol):
    def ingest(
        self,
        filename: str,
        content: bytes,
        *,
        document_type: DocumentType | None = None,
    ) -> IngestedDocument: ...


class LocalDocumentIngestionPipeline:
    """Parse supported documents without network access, macros, OCR or active content."""

    def ingest(
        self,
        filename: str,
        content: bytes,
        *,
        document_type: DocumentType | None = None,
    ) -> IngestedDocument:
        safe_name = Path(filename).name
        normalized_name = filename.replace("\\", "/")
        if not safe_name or "/" in normalized_name or safe_name != normalized_name:
            raise ValueError("Nome de arquivo inválido; caminhos não são aceitos.")
        if not content:
            raise ValueError("Documento vazio.")
        if len(content) > MAX_DOCUMENT_BYTES:
            raise ValueError("Documento excede o limite local de 10 MiB.")
        resolved_type = document_type or _type_from_filename(safe_name)
        detected_type = _sniff_type(content)
        if (resolved_type in {"pdf", "docx"} and detected_type != resolved_type) or (
            detected_type is not None and detected_type != resolved_type
        ):
            raise ValueError("Conteúdo do arquivo não corresponde à extensão declarada.")
        digest = hashlib.sha256(content).hexdigest()
        pages, method, warnings, structured_data = _extract(content, resolved_type)
        extracted_size = sum(len(page.text) for page in pages)
        if extracted_size > MAX_EXTRACTED_CHARACTERS:
            raise ValueError("Texto extraído excede o limite local de segurança.")
        blocks = _blocks(page.text for page in pages)
        status: IngestionStatus = "needs_review" if warnings else "accepted"
        media_type = _media_type(resolved_type)
        provenance = [
            DocumentProvenance(
                source="local_upload",
                source_ref=f"ingest://{digest}/page/{page.number}",
                extraction_method=method,
                location={"file_name": safe_name, "page": page.number},
            )
            for page in pages
        ]
        return IngestedDocument(
            document_id=f"document:{digest[:24]}",
            document_type=resolved_type,
            media_type=media_type,
            byte_size=len(content),
            status=status,
            text_blocks=blocks,
            pages=pages,
            sections=_sections(blocks),
            structured_data=structured_data,
            source_hash=digest,
            warnings=warnings,
            provenance=provenance,
        )


def _type_from_filename(filename: str) -> DocumentType:
    suffix = Path(filename).suffix.lower().lstrip(".")
    if suffix not in {"pdf", "docx", "html", "htm", "txt", "json"}:
        raise ValueError("Formato não suportado. Use PDF, DOCX, HTML, TXT ou JSON Resume.")
    return cast(DocumentType, "html" if suffix == "htm" else suffix)


def _sniff_type(content: bytes) -> DocumentType | None:
    prefix = content[:4096].lstrip()
    if prefix.startswith(b"%PDF-"):
        return "pdf"
    if prefix.startswith(b"PK"):
        try:
            with zipfile.ZipFile(io.BytesIO(content)) as archive:
                if "word/document.xml" in archive.namelist():
                    return "docx"
        except zipfile.BadZipFile as exc:
            raise ValueError("Contêiner ZIP/DOCX inválido.") from exc
    lowered = prefix.lower()
    if lowered.startswith((b"<!doctype html", b"<html", b"<body")):
        return "html"
    if prefix.startswith((b"{", b"[")):
        return "json"
    if b"\x00" in prefix:
        raise ValueError("Arquivo binário não suportado.")
    return None


def _extract(
    content: bytes,
    document_type: DocumentType,
) -> tuple[list[DocumentPage], str, list[str], dict[str, Any]]:
    if document_type == "pdf":
        pypdf = importlib.import_module("pypdf")
        document = pypdf.PdfReader(io.BytesIO(content))
        if document.is_encrypted:
            raise ValueError("PDF criptografado ou protegido por senha não é aceito.")
        if len(document.pages) > MAX_PDF_PAGES:
            raise ValueError("PDF excede o limite de 200 páginas.")
        pages = [
            DocumentPage(number=index + 1, text=page.extract_text() or "")
            for index, page in enumerate(document.pages)
        ]
        warnings = _empty_warning(pages)
        if warnings:
            warnings.append("PDF possivelmente baseado em imagem; OCR não é executado.")
        return pages, "pypdf_text", warnings, {}
    if document_type == "docx":
        zip_warnings = _validate_docx_container(content)
        document_module = importlib.import_module("docx")
        document = document_module.Document(io.BytesIO(content))
        paragraphs = [paragraph.text for paragraph in document.paragraphs]
        table_rows = [
            " | ".join(cell.text for cell in row.cells)
            for table in document.tables
            for row in table.rows
        ]
        pages = [DocumentPage(number=1, text="\n".join([*paragraphs, *table_rows]))]
        return pages, "python-docx", [*zip_warnings, *_empty_warning(pages)], {}

    decoded = content.decode("utf-8", errors="replace")
    warnings = ["Caracteres inválidos foram substituídos."] if "�" in decoded else []
    structured_data: dict[str, Any] = {}
    if document_type == "html":
        parser = _VisibleTextParser()
        parser.feed(decoded)
        decoded = "\n".join(parser.parts)
        method = "html.parser_visible_text"
        if parser.active_content_count:
            warnings.append("Conteúdo ativo HTML foi removido durante a ingestão.")
    elif document_type == "json":
        decoded, structured_data = _extract_json_resume(decoded)
        method = "json_resume"
    else:
        method = "utf-8"
    pages = [DocumentPage(number=1, text=decoded)]
    return pages, method, [*warnings, *_empty_warning(pages)], structured_data


def _validate_docx_container(content: bytes) -> list[str]:
    try:
        with zipfile.ZipFile(io.BytesIO(content)) as archive:
            entries = archive.infolist()
            if len(entries) > MAX_ZIP_ENTRIES:
                raise ValueError("DOCX contém entradas demais.")
            total_size = sum(item.file_size for item in entries)
            if total_size > MAX_ZIP_UNCOMPRESSED_BYTES:
                raise ValueError("DOCX excede o limite descompactado de segurança.")
            for item in entries:
                if item.file_size and item.compress_size == 0:
                    raise ValueError("DOCX contém entrada comprimida inválida.")
                if (
                    item.compress_size
                    and item.file_size / item.compress_size > MAX_COMPRESSION_RATIO
                ):
                    raise ValueError("DOCX apresenta razão de compressão insegura.")
            warnings: list[str] = []
            relation_names = [name for name in archive.namelist() if name.endswith(".rels")]
            if any(b'TargetMode="External"' in archive.read(name) for name in relation_names):
                warnings.append(
                    "Relações externas do DOCX foram ignoradas; nenhuma rede foi acessada."
                )
            return warnings
    except zipfile.BadZipFile as exc:
        raise ValueError("DOCX inválido.") from exc


def _extract_json_resume(decoded: str) -> tuple[str, dict[str, Any]]:
    try:
        payload = json.loads(decoded)
    except json.JSONDecodeError as exc:
        raise ValueError("Documento JSON inválido.") from exc
    if not isinstance(payload, dict):
        raise ValueError("JSON Resume deve ser um objeto JSON.")
    try:
        resume = JSONResume.model_validate(payload)
    except ValidationError as exc:
        raise ValueError("JSON não atende ao contrato JSON Resume aceito.") from exc
    values: list[str] = []
    values.extend(str(value) for value in resume.basics.values() if isinstance(value, str))
    for bucket in (
        resume.work,
        resume.volunteer,
        resume.education,
        resume.awards,
        resume.publications,
        resume.skills,
        resume.projects,
        resume.certificates,
        resume.languages,
    ):
        for item in bucket:
            values.extend(_string_values(item))
    return "\n".join(dict.fromkeys(filter(None, values))), resume.model_dump(mode="json")


def _string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, list):
        return [text for item in value for text in _string_values(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in _string_values(item)]
    return []


def _media_type(document_type: DocumentType) -> str:
    return {
        "pdf": "application/pdf",
        "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "html": "text/html",
        "txt": "text/plain",
        "json": "application/json",
    }[document_type]


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
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0
        self.active_content_count = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "noscript", "iframe", "object", "embed"}:
            self._ignored_depth += 1
            self.active_content_count += 1
        self.active_content_count += sum(
            1
            for name, value in attrs
            if name.casefold().startswith("on")
            or (value or "").casefold().startswith("javascript:")
        )

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "noscript", "iframe", "object", "embed"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)

    def handle_data(self, data: str) -> None:
        cleaned = data.strip()
        if cleaned and not self._ignored_depth:
            self.parts.append(cleaned)


__all__ = [
    "DocumentIngestionPipeline",
    "DocumentPage",
    "DocumentProvenance",
    "DocumentSection",
    "DocumentType",
    "IngestedDocument",
    "LocalDocumentIngestionPipeline",
]
