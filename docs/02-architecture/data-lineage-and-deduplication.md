# Linhagem de dados e deduplicação

## Princípios

1. Origem e evidência acompanham a entidade.
2. Conteúdo extraído vira candidato revisável; não se transforma em fato confirmado por inferência.
3. Identidade forte tem prioridade sobre similaridade textual.
4. Merge preserva IDs e referências; fato confirmado não é apagado silenciosamente.
5. Snapshot registra o conteúdo usado naquele momento, sem substituir a entidade mutável.
6. A mesma evidência não deve entrar repetidamente no Perfil e na memória.

## Fluxo de ponta a ponta

```text
Origem pública/manual/extensão
  → captura ou importação sanitizada
  → entidade mutável + source/source_ref
  → candidato revisável para o Perfil, quando aplicável
  → Career Context com evidências necessárias
  → análise e AiRun
  → snapshots de vaga/currículo/análise/edital
  → Tracker/ApplicationRecord
  → eventos, resultado e feedback
```

O Perfil Universal é a fonte consolidada de fatos de carreira. Memória, capturas e stores acadêmicos continuam guardando evidências e histórico; eles não substituem automaticamente um item confirmado do Perfil.

## Campos de proveniência

Nem todas as entidades usam exatamente o mesmo modelo, mas os fluxos confiáveis preservam o equivalente a:

| Campo | Semântica |
|---|---|
| `source` / `source_kind` | tipo ou método de origem |
| `source_ref` | referência principal durável |
| `source_refs` | todas as referências preservadas |
| `source_url` / `source_urls` | URLs brutas úteis para auditoria |
| `content_hash` | identidade determinística do conteúdo |
| `confirmed_by_user` | confirmação humana do fato |
| `confidence` | qualidade da extração/evidência |
| `evidence_used` | evidências efetivamente usadas na análise |
| `source_capture_id` | captura que originou a candidatura |
| `legacy_source_paths` | stores envolvidos em merge de migração |

`merge_source_refs()` remove repetição sem mudar a primeira ordem observada.

## Linhagem por origem

| Origem | Dados produzidos | Persistência | Consumidor/revisão |
|---|---|---|---|
| texto manual | vaga, currículo, edital ou candidato | store do domínio; snapshot quando entra em fluxo confiável | Match, Perfil, Editais, Tracker |
| Lattes | itens acadêmicos candidatos | store acadêmico/Perfil após confirmação | Perfil → Career Context |
| GitHub/portfólio | relatório, projeto e candidatos | JSONL, `github_projects`, memória | revisão → Perfil/portfólio |
| extensão | captura sanitizada | Companion JSONL, `captures`, snapshots | Vaga/Edital/GitHub/Tracker |
| Radar | resultado e alerta | JSON + tabelas Radar/notifications | Caixa, Tracker, notificação |
| Tracker | cartão, candidatura e eventos | JSON mutável + SQLite | Dashboard, Inteligência, memória |
| Perfil | evidências de contexto | JSON/SQLite conforme origem | Match, ATS, Tailor, Radar, Editais |
| IA | resultado e trace seguro | `analysis_snapshots`, `ai_runs` | tela, Tracker e auditoria |

## Identidades canônicas

`modules/core/entity_identity.py` centraliza primitivas compartilhadas.

### URL

`normalize_entity_url()`:

- remove fragmento;
- normaliza scheme/host;
- remove barra final redundante;
- ordena query params;
- descarta `utm_*`, `fbclid`, `gclid`, `ref`, `source`, `tracking`, `trk` e similares;
- preserva parâmetros não classificados como tracking, pois podem carregar o ID real da entidade.

### DOI, ORCID e GitHub

- DOI vira identificador lowercase sem prefixo de URL;
- ORCID vira o formato canônico em maiúsculas;
- repositório GitHub vira `owner/repo`, sem `.git`.

### `ProfileItem`

DOI e ORCID são referências fortes. Para referências que representam contêiner — repositório GitHub, perfil Lattes, arquivo importado ou página — a identidade também inclui o tipo e o título do item. Isso evita colapsar várias publicações/skills vindas da mesma fonte.

Sem referência forte, o fallback usa tipo + título normalizados. A origem e o texto da evidência continuam como proveniência, não como motivo para duplicar uma mesma credencial revisada.

### Memória

Com referência, a identidade combina tipo + referência. Sem ela, usa tipo, título, origem e conteúdo normalizado. Durante a migração, memórias que não são evento/feedback só são mescladas por conteúdo exato.

### Editais

A ordem é:

1. número + órgão + banca, quando número e órgão existem;
2. URL canônica;
3. fingerprint de título + órgão + trecho do texto.

Um edital pode conter vários cargos; cada `role_id` e requisito continua entidade própria.

### Projetos

A ordem é owner/repo GitHub, URL canônica e fingerprint de owner/repo/título.

## Vagas entre portais

`same_opportunity()` considera:

1. a mesma URL depois da remoção de tracking; ou
2. a mesma empresa normalizada e o mesmo título; ou
3. mesma empresa e sobreposição forte de tokens do título.

O fallback textual exige empresa presente e igual. Conteúdo semelhante de empresas diferentes não é mesclado. URLs brutas permanecem em `source_urls`, enquanto domínios são acumulados em `source_domains`.

## Primitivas de deduplicação

`modules/core/deduplication.py` oferece duas operações deliberadamente pequenas:

- `duplicate_groups`: agrupa duplicatas e deixa a decisão para o chamador;
- `unique_preserving_order`: mantém a primeira ocorrência sem mutar ou apagar a entrada.

Para itens do Perfil com identidade incerta, o produto cria sugestão de dedupe; não remove itens automaticamente.

## Deduplicação na migração legada

O importador calcula a identidade antes de inserir. Um merge forte/exato registra:

```json
{
  "merged_legacy_ids": ["id-original", "id-duplicado"],
  "legacy_source_paths": ["store-a.json", "store-b.jsonl"],
  "source_refs": ["referencia-a", "referencia-b"],
  "deduplication_reason": "strong_or_exact_identity_during_legacy_migration"
}
```

O primeiro ID é preservado. Campos vazios podem ser preenchidos pelo registro seguinte e listas são unidas por representação JSON. Dados divergentes não vazios não são sobrescritos indiscriminadamente.

`legacy_migration_history` registra arquivo, checksum, tabela, ID e hash do payload. Reexecutar o mesmo arquivo é idempotente; alterar o arquivo exige nova avaliação.

## Snapshots e linhagem temporal

Entidade e snapshot têm papéis diferentes:

```text
Opportunity (estado atual) ──< JobSnapshot (estado capturado)
Profile (estado atual) ──────< ResumeSnapshot (versão usada)
Job + Resume snapshots ─────< AnalysisSnapshot (resultado/evidência)
ExamNotice (revisável) ─────< PublicExamSnapshot (estado histórico)
```

O hash exclui IDs e timestamps, permitindo reutilizar conteúdo idêntico. Triggers impedem update/delete. Uma candidatura liga os IDs exatos de vaga, currículo, variante Tailor, Match e ATS.

Dados antigos sem texto original não recebem conteúdo inventado. Eles permanecem sem snapshot completo e aparecem como warning no data health.

## Career Context e revisão humana

O contexto deve transportar:

```json
{
  "context_summary": "",
  "evidence_used": [],
  "warnings": [],
  "source_refs": []
}
```

ATS, Tailor e outros fluxos de declaração usam evidência confirmada quando produzem termos que poderiam ser interpretados como fato profissional. Itens candidatos vindos de Lattes, GitHub ou extensão precisam de confirmação antes de entrar como afirmação segura.

## Auditoria de IA

`AiRunStore` separa trace de execução do resultado imutável:

- solicitado versus usado;
- modelo e prompt versionados;
- fallback e motivo;
- validade do schema;
- hash da entrada, fontes, referências e evidências;
- warnings e necessidade de revisão.

O store não recebe chave de API nem conteúdo bruto de autorização. `AnalysisSnapshot` mantém o resultado ligado às evidências e às versões de vaga/currículo.

## Detecção de órfãos

O data health sinaliza:

- candidatura sem snapshot de vaga;
- oportunidade ou edital sem snapshot;
- oportunidade sem referência de origem;
- snapshot com hash repetido em registros distintos;
- trace de IA incompleto;
- FK ou integridade inválida;
- memória legada sem referência.

Warnings não fazem merge nem correção automática. O relatório orienta revisão e migração.

## Estado de transição

O SotuHire ainda opera com JSON/JSONL e SQLite em paralelo. Essa condição é explícita:

- arquivos antigos são preservados;
- novos snapshots e vínculos vivem no banco;
- alguns cartões são espelhados nas duas camadas;
- não existe transação única entre arquivo e SQLite;
- a migração completa de cada store deve ocorrer por etapas verificáveis.

Veja [Arquitetura de repositórios](storage-repository-architecture.md), [Schema SQLite](sqlite-schema-and-migrations.md) e [Snapshots](application-snapshots.md).
