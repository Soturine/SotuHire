import io
import json

import pytest
from docx import Document
from modules.parsers.document_ingestion import LocalDocumentIngestionPipeline
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas


def _pdf_bytes(text: str = "", *, rectangle: bool = False) -> bytes:
    output = io.BytesIO()
    pdf = canvas.Canvas(output, invariant=1)
    if text:
        pdf.drawString(72, 770, text)
    if rectangle:
        pdf.rect(20, 20, 80, 80, fill=1)
    pdf.save()
    return output.getvalue()


def test_ingestion_is_deterministic_and_preserves_provenance():
    pipeline = LocalDocumentIngestionPipeline()
    first = pipeline.ingest("curriculo.txt", b"Perfil\n\nPython e SQL")
    second = pipeline.ingest("curriculo.txt", b"Perfil\n\nPython e SQL")

    assert first.document_id == second.document_id
    assert first.source_hash == second.source_hash
    assert first.provenance[0].source_ref.startswith("ingest://")
    assert first.provenance[0].location == {"file_name": "curriculo.txt", "page": 1}
    assert first.document_type == "txt"
    assert "Python e SQL" in first.text_blocks


def test_ingestion_removes_script_content_from_html():
    result = LocalDocumentIngestionPipeline().ingest(
        "perfil.html",
        b"<h1>Perfil</h1><script>secret()</script><p>Experiencia publica</p>",
    )

    assert "secret" not in " ".join(result.text_blocks)
    assert "Experiencia publica" in " ".join(result.text_blocks)


def test_ingestion_supports_pdf_and_docx():
    pdf_result = LocalDocumentIngestionPipeline().ingest("resume.pdf", _pdf_bytes("Curriculo PDF"))

    docx = Document()
    docx.add_paragraph("Curriculo DOCX")
    buffer = io.BytesIO()
    docx.save(buffer)
    docx_result = LocalDocumentIngestionPipeline().ingest("resume.docx", buffer.getvalue())

    assert pdf_result.pages[0].text.strip() == "Curriculo PDF"
    assert docx_result.pages[0].text == "Curriculo DOCX"


def test_ingestion_rejects_invalid_json_and_unknown_format():
    pipeline = LocalDocumentIngestionPipeline()

    try:
        pipeline.ingest("profile.json", b"{")
    except ValueError as exc:
        assert "JSON" in str(exc)
    else:
        raise AssertionError("JSON inválido deveria falhar")

    try:
        pipeline.ingest("profile.csv", b"name,value")
    except ValueError as exc:
        assert "não suportado" in str(exc)
    else:
        raise AssertionError("Formato desconhecido deveria falhar")


def test_ingestion_rejects_spoofed_paths_mime_and_encrypted_pdf():
    pipeline = LocalDocumentIngestionPipeline()

    with pytest.raises(ValueError, match="caminhos"):
        pipeline.ingest("../resume.txt", b"texto")
    with pytest.raises(ValueError, match="extensão"):
        pipeline.ingest("resume.pdf", b"texto comum")

    writer = PdfWriter()
    writer.append_pages_from_reader(PdfReader(io.BytesIO(_pdf_bytes("privado"))))
    writer.encrypt("user-fixture", "owner-fixture")
    encrypted = io.BytesIO()
    writer.write(encrypted)
    with pytest.raises(ValueError, match="criptografado"):
        pipeline.ingest("resume.pdf", encrypted.getvalue())


def test_image_only_pdf_is_reviewable_without_hidden_ocr():
    result = LocalDocumentIngestionPipeline().ingest("scan.pdf", _pdf_bytes(rectangle=True))

    assert result.status == "needs_review"
    assert any("OCR não é executado" in warning for warning in result.warnings)


def test_json_resume_standard_fields_are_structured_and_active_html_is_removed():
    payload = {
        "$schema": "https://raw.githubusercontent.com/jsonresume/resume-schema/master/schema.json",
        "basics": {"name": "Pessoa Fictícia", "label": "Analista"},
        "work": [{"name": "Empresa", "position": "Analista", "summary": "Qualidade"}],
        "volunteer": [{"organization": "Projeto", "position": "Mentoria"}],
        "publications": [{"name": "Artigo fictício"}],
    }
    result = LocalDocumentIngestionPipeline().ingest(
        "resume.json",
        json.dumps(payload, ensure_ascii=False).encode("utf-8"),
    )
    html = LocalDocumentIngestionPipeline().ingest(
        "resume.html",
        b'<h1>Perfil</h1><iframe src="https://example.invalid"></iframe><p>Seguro</p>',
    )

    assert result.structured_data["basics"]["name"] == "Pessoa Fictícia"
    assert "Qualidade" in " ".join(result.text_blocks)
    assert html.status == "needs_review"
    assert "example.invalid" not in " ".join(html.text_blocks)
