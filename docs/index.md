# SotuHire

SotuHire é um assistente de carreira local-first, multiárea e baseado em evidências. Ele conecta Perfil Profissional Universal, currículo, vagas, Match, ATS, Tailor, Lattes, Editais, Radar, Tracker, GitHub/portfólio e uma extensão assistiva sem automatizar candidaturas ou decisões críticas.

## Comece aqui

| Interesse | Documento recomendado |
| --- | --- |
| Entender o produto | [Visão](01-product/vision.md) e [estratégia multiárea](01-product/multi-domain-product-strategy.md) |
| Instalar e executar | [README do repositório](https://github.com/Soturine/SotuHire#readme) |
| Ver como os módulos se conectam | [Mapa de módulos](02-architecture/module-integration-map.md) |
| Conferir capacidades reais | [Matriz verificável](02-architecture/integration-capability-matrix.md) |
| Entender dados locais | [Repository architecture](02-architecture/storage-repository-architecture.md) |
| Ver a demonstração | [Roteiro](09-portfolio/demo-script.md) e [case study](09-portfolio/portfolio-case-study.md) |

## Produto

O Perfil Universal reúne fatos confirmados e candidatos revisáveis com origem, confiança e sensibilidade. O Career Context seleciona apenas o necessário para cada finalidade. Análises preservam warnings, provider/modelo efetivos e evidências; quando seguem ao Tracker, podem ser ligadas a snapshots imutáveis.

O frontend possui modo Demo e modo API Real. A extensão pode capturar vagas, editais e projetos, operar com Local Companion sem o React aberto e usar análise local, IA do SotuHire ou chave própria opcional isolada no service worker.

## Dados e persistência

SQLite local adiciona transações, foreign keys, migrações e vínculos entre entidades. JSON/JSONL antigos continuam preservados durante a transição. Backup e export excluem secrets conhecidos; restore valida checksum, formato, schema, integridade SQLite e exige confirmação quando acionado pelo frontend.

- [SQLite e migrações](02-architecture/sqlite-schema-and-migrations.md)
- [Snapshots](02-architecture/application-snapshots.md)
- [Backup, restore e health](02-architecture/backup-restore-and-data-health.md)
- [Linhagem e dedupe](02-architecture/data-lineage-and-deduplication.md)
- [Auditoria atual da IA](00-audit/v1.9.7-ai-system-audit.md)

## IA responsável

Gemini e OpenAI são opcionais. O caminho local continua disponível e o fallback é explícito. Itens não confirmados não devem virar fatos seguros em ATS, Tailor, Radar ou edital.

- [Orquestração e confiança](04-ai/ai-orchestration-and-confidence.md)
- [Catálogo de providers/modelos](02-architecture/ai-provider-model-catalog.md)
- [Prompt Catalog](04-ai/prompt-catalog.md)
- [Plano de avaliação](04-ai/ai-evaluation-plan.md)
- [Golden datasets](09-testing/golden-datasets.md)
- [Arquitetura de avaliação](04-ai/ai-evaluation-architecture.md)
- [Feedback humano e outcomes](04-ai/human-feedback.md)

## Extensão e fontes

- [Local Companion API](02-architecture/local-companion-api.md)
- [Bridge com o Perfil](02-architecture/extension-profile-bridge.md)
- [Regras de captura](03-business-rules/browser-assisted-capture-rules.md)
- [Fontes públicas](05-data-sources/job-sources.md)
- [GitHub/portfólio](05-data-sources/github-portfolio-analyzer.md)
- [Testes da extensão](09-testing/browser-extension-testing.md)

## Engenharia

- [QA e testes](06-engineering/qa-testing.md)
- [CI/CD](06-engineering/ci-cd.md)
- [Segurança e privacidade](06-engineering/security-privacy.md)
- [Índice documental completo](documentation-index.md)

## Limites

O SotuHire não implementa auto-apply, inscrição automática, pagamento, boleto, envio automático de documento, bypass de CAPTCHA, captura de cookies/tokens/sessão ou decisão crítica final somente por IA.

Consulte o [roadmap](01-product/roadmap.md) para prioridades, riscos e critérios de entrada na v2.0.
