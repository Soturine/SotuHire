import io

import fitz
from docx import Document
from modules.parsers.document_ingestion import LocalDocumentIngestionPipeline


def test_ingestion_is_deterministic_and_preserves_provenance():
    pipeline = LocalDocumentIngestionPipeline()
    first = pipeline.ingest("curriculo.txt", b"Perfil\n\nPython e SQL")
    second = pipeline.ingest("curriculo.txt", b"Perfil\n\nPython e SQL")

    assert first.document_id == second.document_id
    assert first.source_hash == second.source_hash
    assert first.provenance[0].source_ref == "curriculo.txt"
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
    pdf = fitz.open()
    pdf.new_page().insert_text((72, 72), "Curriculo PDF")
    pdf_result = LocalDocumentIngestionPipeline().ingest("resume.pdf", pdf.tobytes())
    pdf.close()

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
