# Catálogo de prompts

Este catálogo é gerado do `PromptRegistry` real. Ele diferencia contratos consumidos pelo produto de contratos apenas registrados e valida schema, consumidores, providers, fallback, testes e documentação.

A IA interpreta e sugere; schemas e regras determinísticas validam a resposta. Nenhum prompt autoriza inventar formação, experiência, publicação, registro ou resultado.

## Fonte de verdade

- `modules/ai/prompt_loader.py` define os `PromptSpec` oficiais;
- o schema Pydantic de cada spec é o contrato de saída executável;
- consumidores são encontrados em chamadas Python reais, não em comentários;
- testes e documentos são localizados por referência exata ao `prompt_id`;
- este arquivo não contém chaves, payloads pessoais nem respostas de providers.

Um arquivo em `docs/04-ai/prompts/` que não aparece na tabela pode documentar uma ideia ou capacidade futura, mas não representa um contrato registrado no runtime.

## Decisão de arquitetura

O produto usa prompts separados por tarefa, versionados e com schemas próprios. Não existe um prompt genérico autorizado a decidir todo o fluxo de carreira.

```text
entrada estruturada + evidências rastreáveis
→ PromptSpec versionado
→ Gemini ou OpenAI (opcional)
→ validação Pydantic/JsonGuard
→ fallback determinístico explícito
→ revisão humana
```

## Regras globais

Todos os prompts consumidos pelo produto devem:

- retornar dados compatíveis com o schema registrado;
- não inventar experiência, formação, certificação, publicação ou registro profissional;
- diferenciar fato confirmado, inferência e sugestão;
- preservar `source_ref` e evidências quando o fluxo as fornece;
- indicar ausência de informação em vez de preencher lacunas;
- reduzir confiança quando houver ambiguidade ou conflito;
- manter warnings e necessidade de revisão humana;
- respeitar a diferença entre requisito obrigatório, desejável e opcional;
- não transformar projeto pessoal em experiência corporativa;
- não transformar curso livre em graduação;
- não afirmar que uma pessoa possui skill só porque a vaga a exige;
- não tomar decisão crítica final nem executar candidatura;
- omitir contexto sensível de providers externos sem consentimento explícito;
- registrar provider/modelo solicitado e usado quando a execução é rastreada;
- tornar fallback visível em metadata e warnings.

## Registro verificável

| prompt_id | version | status | schema | consumers | providers | fallback | tests | docs |
|---|---|---|---|---|---|---|---|---|
| `ats_analysis_v1` | `1.0.0` | implementado | `modules.ai.schemas.analysis_insights.AtsAiReviewOutput` | `modules/tracker/job_tracker.py`<br>`apps/api/services/analysis.py` | gemini, openai | Revisão local de palavras-chave | `tests/test_api_ai_routing_v15.py`<br>`tests/test_api_ats.py`<br>`tests/test_prompt_registry.py` | `docs/04-ai/ai-orchestration-and-confidence.md`<br>`docs/04-ai/prompt-registry.md`<br>`docs/04-ai/prompting.md`<br>`docs/04-ai/prompts/ats-analysis-v1.md` |
| `career_advice_v1` | `1.0.0` | registrado sem consumidor | `modules.ai.schemas.analysis_insights.SafeAiInsightOutput` | — | gemini, openai | Sem consumidor ativo; fallback não executado | `tests/test_prompt_registry.py` | `docs/04-ai/prompt-registry.md`<br>`docs/04-ai/prompts/career-advice-v1.md` |
| `domain_classification_v1` | `1.0.0` | implementado sem fluxo integrado | `modules.ai.schemas.domain_classification.DomainClassificationOutput` | `modules/ai/domain_classification_service.py` | gemini, openai | Classificador determinístico de domínio | `tests/test_prompt_registry.py` | `docs/04-ai/prompt-registry.md`<br>`docs/04-ai/prompts/domain-classification-v1.md` |
| `github_repo_analysis_v2` | `2.0.0` | implementado | `modules.github_analyzer.schemas.GitHubRepoAnalysisOutput` | `modules/github_analyzer/analyzer_service.py`<br>`apps/api/services/analysis.py` | gemini, openai | Analisador heurístico do repositório | `tests/test_github_analyzer_service.py`<br>`tests/test_prompt_registry.py` | `docs/04-ai/ai-orchestration-and-confidence.md`<br>`docs/04-ai/prompt-registry.md`<br>`docs/04-ai/prompting.md`<br>`docs/04-ai/prompts/github-repo-analysis-v2.md` |
| `job_extraction_multi_domain_v1` | `1.0.0` | implementado | `modules.ai.schemas.job_extraction.JobExtractionOutput` | `modules/ai/structured_job_extractor.py`<br>`apps/api/services/analysis.py` | gemini, openai | Parser local de vaga | `tests/test_prompt_registry.py`<br>`tests/test_structured_job_extractor.py` | `docs/04-ai/ai-orchestration-and-confidence.md`<br>`docs/04-ai/prompt-registry.md`<br>`docs/04-ai/prompting.md`<br>`docs/04-ai/prompts/job-extraction-multi-domain-v1.md` |
| `job_radar_match_explanation_v1` | `1.0.0` | implementado | `modules.ai.schemas.analysis_insights.RadarMatchExplanationOutput` | `apps/api/services/radar.py` | gemini, openai | Explicação determinística de aderência | `tests/test_api_radar.py`<br>`tests/test_prompt_registry.py` | `docs/04-ai/prompt-registry.md` |
| `job_wishlist_builder_v1` | `1.0.0` | implementado | `modules.ai.schemas.analysis_insights.WishlistDraftOutput` | `apps/api/services/radar.py` | gemini, openai | Parser local de wishlist | `tests/test_api_radar_wishlist_draft.py`<br>`tests/test_prompt_registry.py` | `docs/04-ai/prompt-registry.md` |
| `match_analysis_evidence_based_v1` | `1.0.0` | implementado | `modules.schemas.job_analysis.JobAnalysisSchema` | `modules/ai/structured_analysis.py`<br>`modules/local_api/app.py`<br>`modules/tracker/job_tracker.py`<br>`apps/api/services/analysis.py` | gemini, openai | Match Engine determinístico | `tests/test_ai_run_store.py`<br>`tests/test_api_ai_routing_v15.py`<br>`tests/test_prompt_registry.py` | `docs/04-ai/ai-orchestration-and-confidence.md`<br>`docs/04-ai/prompt-registry.md`<br>`docs/04-ai/prompting.md`<br>`docs/04-ai/prompts/match-analysis-evidence-based-v1.md` |
| `profile_items_extractor_v1` | `1.0.0` | implementado | `modules.profile.models.ProfileImportDraft` | `apps/api/services/profile.py` | gemini, openai | Extrator local de itens de perfil | `tests/test_api_profile.py`<br>`tests/test_prompt_registry.py` | `docs/04-ai/prompt-registry.md` |
| `profile_lattes_extractor_v1` | `1.0.0` | implementado | `modules.academic.lattes_models.LattesImportResult` | `modules/academic/lattes_service.py` | gemini, openai | Parser local de Lattes | `tests/test_academic_lattes.py`<br>`tests/test_prompt_registry.py` | `docs/04-ai/prompt-registry.md`<br>`docs/04-ai/prompts/profile-lattes-extractor-v1.md` |
| `public_exam_notice_extractor_v1` | `1.0.0` | implementado | `modules.public_exams.models.PublicExamImportResult` | `modules/public_exams/service.py` | gemini, openai | Parser local de edital | `tests/test_prompt_registry.py`<br>`tests/test_public_exams.py` | `docs/04-ai/prompt-registry.md`<br>`docs/04-ai/prompts/public-exam-notice-extractor-v1.md` |
| `resume_extraction_v1` | `1.0.0` | implementado | `modules.ai.schemas.resume_extraction.ResumeExtractionOutput` | `modules/ai/structured_resume_extractor.py`<br>`apps/api/services/analysis.py` | gemini, openai | Parser local de currículo | `tests/test_prompt_registry.py`<br>`tests/test_structured_resume_extractor.py` | `docs/04-ai/ai-orchestration-and-confidence.md`<br>`docs/04-ai/prompt-architecture.md`<br>`docs/04-ai/prompt-registry.md`<br>`docs/04-ai/prompting.md`<br>`docs/04-ai/prompts/resume-extraction-v1.md` |
| `resume_tailor_v1` | `1.0.0` | implementado | `modules.ai.schemas.analysis_insights.ResumeTailorAiOutput` | `apps/api/services/analysis.py` | gemini, openai | Regras locais de adaptação segura | `tests/test_api_ai_routing_v15.py`<br>`tests/test_api_tailor.py`<br>`tests/test_prompt_registry.py` | `docs/04-ai/ai-orchestration-and-confidence.md`<br>`docs/04-ai/prompt-registry.md`<br>`docs/04-ai/prompting.md`<br>`docs/04-ai/prompts/resume-tailor-v1.md` |
| `source_import_enrichment_v1` | `1.0.0` | implementado | `modules.ai.schemas.analysis_insights.SourceImportEnrichmentOutput` | `apps/api/services/sources.py` | gemini, openai | Normalização determinística da importação | `tests/test_api_source_imports.py`<br>`tests/test_prompt_registry.py` | `docs/04-ai/prompt-registry.md` |

## Como interpretar o status

- `implementado`: existe ao menos uma chamada executável que referencia o prompt;
- `implementado sem fluxo integrado`: há serviço executável, mas nenhuma rota/feature o invoca;
- `registrado sem consumidor`: o contrato está no registry, mas nenhum fluxo o chama;
- a presença no registry não prova que todas as telas usam o resultado;
- a coluna `tests` mostra referências existentes, não uma garantia automática de cobertura total.

## Contratos sem consumidor

- `career_advice_v1` está registrado, mas não é chamado por nenhum módulo ou serviço.

## Envelope de entrada recomendado

Nem todos os prompts usam todos os campos, mas integrações novas devem preferir contexto estruturado e mínimo em vez de concatenar dados indiscriminadamente.

```json
{
  "prompt_id": "string",
  "prompt_version": "string",
  "language": "pt-BR",
  "analysis_mode": "fast | standard | deep",
  "user_goal": "string | null",
  "candidate_profile": "object | null",
  "job_post": "object | null",
  "resume_text": "string | null",
  "job_text": "string | null",
  "career_context": "object | null",
  "source_refs": [],
  "constraints": "object | null"
}
```

O contexto enviado deve ser limitado ao propósito da análise. O Perfil Universal completo não deve ser anexado a toda chamada por padrão.

## Envelope de saída recomendado

O schema específico é soberano. Quando fizer sentido para o fluxo, ele deve expor também os sinais de auditoria abaixo:

```json
{
  "result": {},
  "confidence": 0.0,
  "needs_human_review": true,
  "warnings": [],
  "evidence_used": [],
  "source_refs": [],
  "missing_information": [],
  "unsupported_claims": []
}
```

Campos ausentes não devem ser confundidos com campos não analisados. Uma resposta válida no JSON, mas incompatível com as evidências, ainda deve ser rejeitada ou marcada para revisão.

## Metadados de execução

Fluxos rastreados devem manter, quando disponíveis:

- `run_id`, `feature`, `prompt_id` e `prompt_version`;
- `provider_requested`, `provider_used`, `model_requested` e `model_used`;
- `analysis_mode`, `fallback_used` e `fallback_reason`;
- `schema_valid`, `latency_ms`, `token_usage` e `estimated_cost`;
- `input_hash`, `context_sources`, `source_refs` e `evidence_used`;
- `warnings`, `needs_user_review` e `created_at`.

Segredos, cabeçalhos de autenticação e conteúdo sensível não pertencem ao trace.

## Política de fallback

O fallback é uma decisão de produto, não apenas tratamento de exceção:

1. preserve a entrada original e o resultado determinístico local;
2. tente o provider somente quando o recurso e a permissão estiverem ativos;
3. valide a saída estruturada antes de mesclar qualquer campo;
4. ao falhar, use o resultado local sem ocultar `fallback_used`;
5. informe um motivo seguro, sem incluir chave, payload integral ou traceback sensível;
6. mantenha a decisão final sob revisão da pessoa usuária.

Quando não existe fallback seguro, o fluxo deve retornar indisponibilidade clara em vez de fabricar uma resposta aparentemente completa.

## Providers e fallback

Os mesmos `PromptSpec` estruturados podem ser executados pelos adapters Gemini e OpenAI. O provider local não consome esses prompts: ele representa o caminho determinístico indicado na coluna `fallback`. Falhas externas devem aparecer nos metadados da análise e nunca ser silenciosas.

## Multiárea e linguagem

Os contratos devem funcionar para tecnologia, engenharias, saúde, direito, educação, pesquisa, artes, design, administração, turismo, cursos técnicos e transição de carreira. Exemplos e schemas não podem pressupor que todo portfólio é software ou que toda evidência profissional vem de emprego formal.

## Quando não usar IA

Não é necessário chamar um provider para:

- CRUD, mudança de estágio ou cálculo de métricas do Tracker;
- validação de checksum, backup, restore ou migração de schema;
- deduplicação por identificador forte, DOI, ORCID ou URL canônica;
- aplicação de regras de segurança e bloqueios anti-invenção;
- operações que já possuem resultado determinístico suficiente;
- qualquer ação automática de candidatura ou inscrição, que está fora de escopo.

A IA também não deve ser usada para confirmar sozinha um ProfileItem, declarar que um requisito regulatório foi atendido ou substituir leitura oficial de edital.

## Revisão humana

A interface deve solicitar revisão quando houver baixa confiança, evidência conflitante, claim sem source_ref, dado sensível, requisito regulado, mudança material no currículo ou fallback. Aceite e rejeição humana são sinais de avaliação; não são autorização para aprender ou publicar dados pessoais fora do ambiente local.

## Avaliação associada

Prompts consumidos devem ser avaliados com fixtures multiárea e, quando aplicável:

- validade de schema e acurácia de extração de campos;
- precisão/recall de evidências;
- taxa de claims sem suporte e alucinação;
- calibração de confiança e taxa de fallback;
- latência, tokens, custo estimado e concordância entre providers;
- aceitação/rejeição humana e precisão de deduplicação.

Testes externos são opt-in. O CI padrão usa fakes/mocks e não depende de chaves reais.

## Regras de manutenção

- altere o `PromptSpec` e seu schema de saída de forma versionada;
- mantenha ao menos um teste com provider fake para prompts consumidos;
- preserve evidências, warnings e necessidade de revisão humana;
- não registre chaves, payloads sensíveis ou conteúdo pessoal neste catálogo;
- regenere e confira este arquivo após incluir ou remover prompts.

Um prompt só deve ser tratado como pronto quando possui objetivo claro, versão, schema, consumidor, fallback explícito, teste e documentação coerente. Alterações incompatíveis exigem nova versão do contrato.

### Checklist de alteração

1. confirme se a mudança altera apenas texto ou também o contrato;
2. atualize versão e schema quando houver incompatibilidade;
3. ajuste consumidores e fixtures com provider fake;
4. valide o caminho de fallback e os warnings;
5. verifique que evidências/source_refs continuam preservados;
6. gere novamente este catálogo e execute `--check`;
7. registre mudanças de produto no CHANGELOG, não neste catálogo atemporal.

## Validação

```bash
python scripts/generate_prompt_catalog.py
python scripts/generate_prompt_catalog.py --check
```
