# Public Exam Notice Extractor v1

```txt
PROMPT_ID: public_exam_notice_extractor_v1
PROMPT_VERSION: 1.0.0
MODULES: modules/public_exams, modules/ai, apps/api/services/public_exams.py
```

Prompt estruturado para transformar texto colado de edital, concurso, bolsa, residência, estágio público ou chamada institucional em um rascunho revisável.

## Regras

- Extraia somente informações explícitas.
- Não invente órgão, banca, cargo, salário, taxa, datas, requisitos, documentos, etapas ou conteúdo programático.
- Não faça login, scraping, crawler, inscrição, pagamento ou envio de documento.
- Não decida elegibilidade da pessoa usuária sem evidências do Perfil Profissional Universal.
- Sempre retorne `needs_user_review=true`.
- Preserve `source_excerpts` curtos para auditoria.
- Use `warnings` e `questions_to_confirm` para campos ambíguos.
- Retorne JSON válido, sem markdown.

## Saída

A saída deve seguir o schema `PublicExamImportResult`, com `notice`, `roles`, `timeline`, `subjects`, `requirements`, `warnings`, `questions_to_confirm`, `source_excerpts`, `provider_used` e `analysis_mode`.

O edital oficial sempre prevalece.
