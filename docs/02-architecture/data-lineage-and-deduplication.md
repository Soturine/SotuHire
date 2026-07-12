# Linhagem de dados e deduplicação

## Princípios

1. Origem e evidência acompanham a entidade.
2. Item inferido vira candidato, nunca fato automático.
3. Identidade forte tem prioridade sobre similaridade textual.
4. Merge preserva URLs, IDs e motivo; item confirmado não é apagado silenciosamente.
5. A mesma evidência não deve entrar repetidamente no Perfil e na memória.

## Identidades canônicas

`modules/core/entity_identity.py` centraliza:

- URL sem fragmento e parâmetros de tracking, mantendo `jobId` e outros IDs úteis;
- DOI e ORCID canônicos;
- repositório GitHub como `owner/repo`;
- ProfileItem por tipo + referência forte, com fallback semântico;
- memória por origem/referência ou conteúdo;
- edital por URL, número + órgão + banca ou conteúdo;
- projeto por repositório, URL ou conteúdo.

`modules/core/deduplication.py` somente agrupa ou mantém o primeiro item em ordem. A decisão de merge continua na camada de produto.

## Linhagem

| Origem | Entidade criada | Referência preservada | Próximo consumidor |
|---|---|---|---|
| Texto manual | vaga, currículo, edital ou candidato | URL/request ID quando disponível | Match, Perfil, Editais |
| Lattes | ProfileItem candidato | DOI, ORCID, Lattes ID/URL | confirmação -> Perfil -> Context |
| GitHub/portfólio | relatório e candidato | owner/repo, URL, arquivos | confirmação -> Perfil/memória |
| Extensão | capture record | capture ID, URLs, domínios, kind | Site -> Vaga/Edital/GitHub/Tracker |
| Radar | result/alert | run/source/wishlist/result IDs | Caixa/Tracker/notificação |
| Tracker | StoredAnalysis/evento | source URL, collection method | Dashboard/Inteligência/memória |
| Perfil | CareerContextEvidence | source/source_ref/confidence/confirmed | Match/ATS/Tailor/Radar/Editais |

## Regras específicas

- Vagas iguais em portais diferentes podem ser relacionadas por empresa + título semelhante; empresas diferentes nunca são mescladas por esse fallback.
- DOI igual deduplica publicação mesmo quando o título varia.
- Edital exato pode ser consolidado; suas URLs brutas permanecem em `source_refs`.
- Memória repetida conserva o ID original e acumula referências de origem.
- Dúvida de Perfil produz `ProfileDeduplicationSuggestion`; não remove itens.
- Tracking params não participam da identidade, mas a URL original pode permanecer na proveniência.

## Complexidade

As identidades são hashes/strings determinísticos. Stores pequenos continuam JSON/JSONL local-first; a v1.9.5 não adiciona banco externo, Redis, fila ou vector DB.
