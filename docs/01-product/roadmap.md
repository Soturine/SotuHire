# Roadmap do SotuHire

## Estado atual — v1.9.7

Avaliação de IA, tracing seguro, golden datasets, comparação de providers, feedback humano e Outcome Learning foram integrados. A próxima etapa é acumular amostras reais suficientes por domínio e tarefa, aprofundar calibração e avaliar endpoint local OpenAI-compatible sem comprometer structured output ou fallback.

Este documento apresenta somente o estado atual, prioridades, próximos ciclos, riscos, itens fora de escopo e critérios de entrada na v2.0. O histórico detalhado foi preservado no [arquivo do roadmap](roadmap-archive-through-v1.9.5.md), no [CHANGELOG](https://github.com/Soturine/SotuHire/blob/main/CHANGELOG.md), nos [documentos de desenvolvimento](../07-development/v1.9.6-data-reliability-migrations-backups.md) e nas [release notes](../releases/v1.9.6.md).

## Estado atual

### v1.9.6 — Data Reliability, Migrations, Backups & Snapshots

A base técnica atual consolida:

- repositories compatíveis com JSON, JSONL e SQLite;
- SQLite local com transações, foreign keys, WAL, busy timeout e migrações versionadas;
- dry-run e migração idempotente dos stores legados, sempre preservando os arquivos originais;
- backup, export portátil, restore com checksum e data health;
- snapshots imutáveis de vaga, currículo, variante, análise e edital;
- candidatura ligada à vaga, currículo e análises realmente usados quando esses conteúdos existem;
- identidade canônica, deduplicação conservadora e proveniência reforçada;
- Perfil Profissional Universal e Career Context com confirmação, confiança e origem preservadas;
- rastros seguros de provider, modelo, prompt e fallback, sem segredos;
- extensão integrada e independente com handshake, fila confiável e `JobPosting` estruturado;
- manifesto de capacidades, matriz de integração e catálogo de prompts verificáveis;
- frontend local com data health, backup, export e restauração assistida.

O projeto continua local-first, modular e executável sem provider externo. O modo Demo, a API Real, o fallback local, a extensão e os fluxos legados permanecem suportados.

## Prioridades atuais

1. Medir a qualidade real dos fluxos de IA e deduplicação com datasets controlados.
2. Ampliar a ingestão e edição de documentos sem perder proveniência ou revisão humana.
3. Integrar fontes públicas por APIs, feeds e padrões oficiais antes de criar seletores frágeis.
4. Reduzir dados órfãos entre Perfil, memória, Radar, Fontes, Tracker, GitHub e Editais.
5. Manter compatibilidade entre frontend, API, Local Companion, extensão, schema e documentação.
6. Elevar cobertura progressivamente com base medida, sem threshold arbitrário.

## Próximas versões

### v1.9.7 — AI Evaluation, Tracing & Outcome Learning

- benchmark local, Gemini, OpenAI e Ollama;
- golden datasets multiárea;
- validade de schema e acurácia de extração;
- evidence precision/recall;
- unsupported claim e hallucination rate;
- calibração de confiança e acordo entre providers;
- custo, tokens, latência e taxa de fallback;
- aceitação/rejeição humana e aprendizado com outcomes;
- avaliação de precisão/recall da deduplicação.

### v1.9.8 — Document Ingestion & Resume Studio

- pipeline ampliado para PDF, DOCX, HTML e certificados;
- Lattes HTML/XML e edital PDF/HTML;
- JSON Resume completo sem limitar o Perfil Universal ao padrão;
- currículo mestre e variantes por oportunidade;
- preview ATS;
- export PDF, DOCX e JSON;
- snapshot da variante realmente usada no Tracker.

### v1.9.9 — Official Connectors & Taxonomy Intelligence

- Greenhouse Job Board API;
- Lever postings públicos;
- RSS/Atom avançado;
- `schema.org/JobPosting`;
- páginas públicas simples e diretórios manuais;
- adapters CBO, ESCO e O*NET;
- normalização de skills e ocupações;
- recuperação top-K local antes de IA.

### v2.0 — Human-Approved Career Assistant

- workflows de preparação de candidatura com aprovação explícita;
- preparação para entrevista e follow-up;
- plano de carreira e próximos passos explicáveis;
- integração MCP somente leitura ou rascunho;
- decisões críticas sempre submetidas à pessoa usuária;
- nenhuma forma de auto-apply.

## Riscos

| Risco | Mitigação esperada |
| --- | --- |
| Divergência entre JSON legado e SQLite | Migração idempotente, backup prévio, health check e arquivos antigos preservados |
| Campo produzido sem consumidor | Manifesto, matriz de integração e auditoria periódica de linhagem |
| Evidência incerta apresentada como fato | Confirmação humana, confidence, warnings e `source_ref` até a saída |
| Provider/modelo ignorado ou fallback silencioso | AiRun, trace padronizado e UI com provider/modelo efetivos |
| Extensão incompatível com Companion/API | Handshake, versões mínimas/máximas testadas e diagnóstico visível |
| Fonte pública muda de HTML | Priorizar API, feed e JSON-LD; evitar parser específico sem necessidade |
| Backup incluir segredo | Allowlist de arquivos, exclusão por caminho/conteúdo e testes do ZIP |
| Crescimento de escopo | Entregas incrementais, sem microserviços ou infraestrutura distribuída prematura |

## Fora de escopo

- auto-apply, candidatura ou inscrição automática;
- pagamento, emissão de boleto ou envio automático de documentos;
- login automático, captura de cookies, tokens, sessão ou headers autenticados;
- bypass de CAPTCHA, proxies, rotação de IP ou scraping agressivo;
- crawler autenticado novo;
- decisão crítica final somente por IA;
- criação de formação, experiência, publicação, registro ou requisito sem evidência;
- Redis, Kubernetes, fila distribuída, microserviços ou vector database pesado;
- substituir o Perfil Universal por JSON Resume;
- publicar dados locais ou chaves no frontend, GitHub Pages ou artefatos.

## Critérios para v2.0

A v2.0 só deve começar quando:

- migração, backup, restore e data health estiverem estáveis em Windows e Linux/macOS;
- snapshots cobrirem todos os fluxos que influenciam candidatura ou edital;
- matriz de capacidades, OpenAPI, rotas e documentação forem verificadas automaticamente;
- avaliação de IA possuir baseline multiárea reproduzível;
- unsupported claims e hallucinations forem medidos e tratados como falha de qualidade;
- provider, modelo, prompt, fallback e evidências forem rastreáveis nos fluxos críticos;
- currículo mestre, variantes e ingestão documental estiverem integrados ao Tracker;
- conectores oficiais e taxonomias tiverem contratos estáveis;
- extensão, Companion e API possuírem compatibilidade testada;
- workflows continuarem assistivos, reversíveis e aprovados por humanos;
- não houver auto-apply, inscrição automática ou automação financeira/documental.
