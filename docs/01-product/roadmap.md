# Roadmap do SotuHire

## Estado atual — v1.11.0

O produto conecta Perfil Universal, documentos, fontes públicas, taxonomias, oportunidades,
candidaturas, entrevistas e ações de carreira. O histórico detalhado fica no
[CHANGELOG](https://github.com/Soturine/SotuHire/blob/main/CHANGELOG.md), na
[implementação](../07-development/v1.11.0-implementation.md) e nas
[release notes](../releases/v1.11.0.md).

As prioridades continuam local-first, multiárea, evidence-first e sob aprovação humana. Nenhuma próxima etapa inclui auto-apply, login automático, captura de sessão ou decisão crítica autônoma.

## Próximas versões

### v1.11.1 — Portfolio, Academic & Professional Evidence Expansion

- evidências acadêmicas/profissionais mais profundas;
- portfólio multimodal revisável;
- interoperabilidade de ativos sem promover candidatos a fatos.

### v2.0 — Human-Approved Career Copilot

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
