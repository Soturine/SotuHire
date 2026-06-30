# profile_lattes_extractor_v1

Prompt estruturado para transformar texto colado do Currículo Lattes ou de trajetória acadêmica em candidatos revisáveis de `ProfileItem`.

## Objetivo

Extrair somente evidências explícitas para o Perfil Profissional Universal:

- formação acadêmica e técnica;
- iniciação científica, pesquisa, extensão, monitoria e docência;
- publicações, artigos, anais, livros e capítulos;
- produção técnica, artística, datasets, patentes e registros de software;
- eventos, apresentações, bancas, orientações, prêmios e bolsas;
- Lattes ID, ORCID, DOI, ISBN e ISSN quando aparecerem no texto.

## Regras

- Não inventar formação, publicação, DOI, ORCID, Lattes ID, instituição, orientador, vínculo, prêmio, autoria, cargo ou resultado.
- Não inferir titulação a partir de palavras soltas.
- Separar fato explícito, suposição e pergunta a confirmar.
- Cada item deve ter `source`, `source_ref`, `evidence`, `confidence` e `confirmed_by_user=false`.
- A saída deve ser JSON válido, sem markdown.
- Nada é salvo automaticamente no Perfil.

## Entrada

```json
{
  "text": "texto colado pelo usuário",
  "source_url": "opcional",
  "lattes_id": "opcional",
  "orcid": "opcional",
  "language": "pt-BR",
  "local_parser_draft": {}
}
```

## Saída

```json
{
  "items": [],
  "detected_sections": [],
  "assumptions": [],
  "questions_to_confirm": [],
  "warnings": [],
  "confidence": "medium",
  "needs_user_review": true,
  "provider_used": "gemini",
  "requested_provider": "gemini",
  "analysis_mode": "ai"
}
```

## Segurança

Gemini atua como extrator assistido, não como fonte de verdade. Se a resposta for inválida, incompleta ou indisponível, o SotuHire usa o parser local e retorna warning. Dados sensíveis não devem ser enviados a provider externo sem configuração explícita.
