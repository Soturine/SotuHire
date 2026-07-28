# Roadmap do SotuHire

## Estado atual — v1.9.8

O produto conecta Perfil Universal, Currículo Mestre, vaga e engines existentes em um Application Lab guiado. Resume Studio já entrega variantes, diff, editor, preview e JSON Resume. A camada de IA possui taxonomia de erros, structured output, retry/reparo limitados, fallback explícito e benchmarks externos opt-in. O histórico detalhado permanece no [CHANGELOG](https://github.com/Soturine/SotuHire/blob/main/CHANGELOG.md), nos [documentos de desenvolvimento](../07-development/v1.9.8-guided-application-lab-resume-studio.md) e nas [release notes](../releases/v1.9.8.md).

As prioridades continuam local-first, multiárea, evidence-first e sob aprovação humana. Nenhuma próxima etapa inclui auto-apply, login automático, captura de sessão ou decisão crítica autônoma.

## Próximas versões

### v1.9.9 — Document Ingestion, Professional Assets & Resume Studio Completion

- ingestão avançada PDF/DOCX/HTML, Lattes HTML/XML e edital PDF/HTML;
- certificados e proveniência por página/bloco;
- export PDF/DOCX maduro e validação visual dos arquivos;
- templates ATS-safe adicionais e currículo acadêmico;
- carta e demais assets profissionais revisáveis.

### v1.10.0 — Official Connectors, Taxonomies & Opportunity Intelligence

- Greenhouse, Lever, `schema.org/JobPosting` e RSS/Atom;
- CBO, ESCO e O*NET;
- normalização de competências e fontes oficiais;
- top-K local antes da IA e monitoramento responsável.

### v1.10.1 — Interview, Follow-up & Career Action Plans

- preparação para entrevista e banco de histórias STAR;
- follow-up revisável e lembretes;
- plano de carreira, certificações e projetos para gaps;
- calendário/ICS opcional, nunca criado sem confirmação.

### v2.0 — Human-Approved Career Assistant

- workflows compostos e agente assistivo;
- MCP somente leitura ou rascunho;
- aprovação etapa por etapa;
- sem auto-apply, login automático ou decisão crítica autônoma.

## Riscos

| Risco | Mitigação |
|---|---|
| Provider indisponível/quota | erro tipado, retry pequeno, fallback explícito e medição sanitizada |
| Variante divergir do mestre | IDs de origem, change set, snapshots separados e diff |
| Evidência incerta virar fato | confirmação, `source_refs`, warnings e bloqueio de sugestão sem suporte |
| Dados legados divergirem do SQLite | migração idempotente, backup, health e JSON/JSONL preservados |
| Escopo crescer prematuramente | releases incrementais sem microserviços ou infraestrutura distribuída |

## Critérios para v2.0

- ingestão e exports finais validados em múltiplas plataformas;
- snapshots cobrindo artefatos usados em decisões;
- baselines externos por task com amostras comparáveis e sem segredo;
- conectores/taxonomias oficiais com contratos estáveis;
- extensão, Companion, API, frontend, schema e documentação compatíveis;
- workflows reversíveis, explicáveis e aprovados por humanos.
