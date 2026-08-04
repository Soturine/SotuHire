# Roadmap do SotuHire

## Estado atual — v1.9.9

O produto conecta Perfil Universal, ingestão documental, Currículo Mestre, vaga e motores
reais em um Application Lab guiado. Resume Studio entrega review de PDF/DOCX/HTML/TXT/JSON,
variantes, diff, editor, preview e exports PDF/DOCX/JSON Resume. Professional Assets e o
Application Kit preservam lifecycle, aprovação por item e stale. O histórico detalhado fica no
[CHANGELOG](https://github.com/Soturine/SotuHire/blob/main/CHANGELOG.md), na
[implementação](../07-development/v1.9.9-implementation.md) e nas
[release notes](../releases/v1.9.9.md).

As prioridades continuam local-first, multiárea, evidence-first e sob aprovação humana. Nenhuma próxima etapa inclui auto-apply, login automático, captura de sessão ou decisão crítica autônoma.

## Próximas versões

### v1.10.0 — Official Connectors, CBO/QBQ/ESCO/O*NET

- Greenhouse, Lever, `schema.org/JobPosting` e RSS/Atom;
- CBO, QBQ, ESCO e O*NET com versão, licença e proveniência;
- normalização de competências e fontes oficiais;
- top-K local antes da IA e monitoramento responsável.

### v1.10.1 — Interview, STAR, Follow-up & Career Actions

- preparação para entrevista e banco de histórias STAR;
- follow-up revisável e lembretes;
- plano de carreira, certificações e projetos para gaps;
- calendário/ICS opcional, nunca criado sem confirmação.

### v2.0 — Agentic assistive workflows with approval

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
