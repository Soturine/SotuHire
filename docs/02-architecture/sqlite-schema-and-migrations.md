# Schema SQLite e migrações

## Visão geral

O banco local padrão é `data/sotuhire.db`, ou `<SOTUHIRE_DATA_DIR>/sotuhire.db` quando o diretório é configurado por ambiente. O schema atual é a versão `3` e é criado pelo runner próprio em `modules/storage/migrations`.

O modelo é híbrido: campos usados em identidade, integridade e relacionamentos ficam em colunas; o objeto de domínio completo pode permanecer em `payload` JSON. Isso reduz normalização prematura e permite migrar stores existentes sem perder campos ainda não promovidos ao schema relacional.

## Inventário de tabelas

### Controle do schema

| Tabela | Finalidade |
|---|---|
| `migration_history` | versão, descrição, data, sucesso, validação e estratégia de rollback |
| `schema_metadata` | metadados simples, incluindo `schema_version` |
| `legacy_migration_history` | idempotência por arquivo, checksum, tipo e ID importado |

### Entidades e proveniência

| Tabela | Identidade/relacionamento principal | Dados promovidos |
|---|---|---|
| `profiles` | `id` | `source_ref`, `content_hash`, timestamps, `payload` |
| `profile_items` | `id` → `profiles.id` | origem, hash, confirmação humana, `payload` |
| `memories` | `id` | origem, hash e `payload` |
| `sources` | `id` | origem, hash e `payload` |
| `captures` | `id` | origem, hash e `payload` |
| `opportunities` | `id` | origem, hash e `payload` |
| `public_exam_notices` | `id` | origem, hash e `payload` |
| `public_exam_roles` | `id` → `public_exam_notices.id` | origem, hash e `payload` |
| `public_exam_requirements` | `id` → `public_exam_roles.id` | origem, hash e `payload` |
| `radar_wishlists` | `id` | origem, hash e `payload` |
| `radar_sources` | `id` | origem, hash e `payload` |
| `radar_runs` | `id` | origem, hash e `payload` |
| `radar_results` | `id`, `run_id` opcional → `radar_runs.id` | origem, hash e `payload` |
| `notifications` | `id` | origem, hash e `payload` |
| `schedules` | `id` | origem, hash e `payload` |
| `github_projects` | `id` | origem, hash e `payload` |

### Snapshots e candidaturas

| Tabela | Relacionamentos principais | Garantia |
|---|---|---|
| `job_snapshots` | oportunidade opcional | hash e histórico do anúncio |
| `resume_snapshots` | perfil opcional | currículo/variante realmente usado |
| `analysis_snapshots` | vaga e currículo opcionais | resultado, provider, modelo, prompt e evidências |
| `public_exam_snapshots` | edital e cargo opcionais | texto, estrutura, requisitos e cronograma |
| `applications` | snapshots, análise e captura opcionais | estado atual completo da candidatura |
| `application_events` | candidatura obrigatória | eventos de mudança de etapa |

### Auditoria de IA

`ai_runs` registra `feature`, provider/modelo solicitado e usado, prompt, modo, fallback, validade do schema, latência, uso de tokens, custo estimado, hashes, referências, evidências, warnings e necessidade de revisão. O schema não possui coluna para chave, cabeçalho de autorização ou conteúdo integral do prompt.

## Relações e comportamento de remoção

```text
profiles ──< profile_items

public_exam_notices ──< public_exam_roles ──< public_exam_requirements
radar_runs ──< radar_results

opportunities ──< job_snapshots
profiles ──< resume_snapshots
job_snapshots ──< analysis_snapshots >── resume_snapshots
public_exam_notices ──< public_exam_snapshots >── public_exam_roles

applications >── job/resume/analysis snapshots
applications ──< application_events
captures ──< applications
```

Regras de `ON DELETE`:

- `profile_items`, cargos/requisitos de edital e eventos de candidatura usam `CASCADE` a partir do pai mutável;
- `radar_results.run_id` e `applications.source_capture_id` usam `SET NULL`;
- entidades de origem referenciadas por snapshot usam a restrição padrão: não podem ser removidas enquanto o snapshot existir;
- vínculos de candidatura para snapshots e vínculos de análises para snapshots usam a restrição padrão; um snapshot referenciado não pode ser removido;
- além das FKs, os snapshots possuem triggers que impedem a remoção de qualquer forma.

## Imutabilidade dos snapshots

A migração 2 cria oito triggers:

```text
immutable_job_snapshots_update/delete
immutable_resume_snapshots_update/delete
immutable_analysis_snapshots_update/delete
immutable_public_exam_snapshots_update/delete
```

Cada `UPDATE` ou `DELETE` aborta com erro `... snapshot is immutable`. Mudança de conteúdo gera outro snapshot; o registro anterior permanece consultável.

## Índices e unicidade

- `profile_items(profile_id)` e `profile_items(source_ref)`;
- `memories(source_ref)`;
- `ai_runs(feature, created_at DESC)` e `ai_runs(input_hash)`;
- `job_snapshots`: único por `(opportunity_id, content_hash)`;
- `resume_snapshots`: único por `(profile_id, resume_variant_id, content_hash)`;
- `public_exam_snapshots`: único por `(notice_id, role_id, content_hash)`.

`SnapshotStore` também procura uma análise existente por tipo + vaga + currículo + hash antes de inserir. Essa deduplicação de análise é feita na aplicação; atualmente não há `UNIQUE` equivalente na tabela `analysis_snapshots`, portanto concorrência extrema entre processos ainda pode produzir duas inserções iguais.

## Migrações versionadas

| Versão | Conteúdo | Validação mínima |
|---:|---|---|
| 1 | entidades locais, proveniência e stores transacionais | tabelas centrais de Perfil, memória, fontes, vagas, Editais, Radar, notificações e GitHub |
| 2 | snapshots imutáveis, candidaturas e eventos | quatro tabelas de snapshot, `applications`, `application_events` |
| 3 | `ai_runs` e histórico de importação legada | tabelas de auditoria de IA e idempotência |

Cada objeto `Migration` possui `version`, `description`, `up`, `validation`, `rollback_strategy` e `created_at`.

## Funcionamento do runner

`MigrationRunner.apply()`:

1. consulta a última versão marcada com sucesso;
2. ordena as migrações pendentes;
3. cria backup do banco quando ele já possui versão maior que zero e `create_backup=True`;
4. inicia `BEGIN IMMEDIATE` para cada migração;
5. executa o SQL e sua validação;
6. grava `migration_history` e confirma a transação;
7. faz rollback e levanta `MigrationError` em caso de falha.

Executar novamente é idempotente: sem versões pendentes, a lista retornada é vazia.

`current_version()` e `MigrationRunner.verify()` abrem o arquivo em modo SQLite read-only. A criação de `migration_history` ocorre apenas no caminho de `apply()`.

`MigrationRunner.verify()` verifica:

- registro de sucesso de todas as migrações;
- versão em `migration_history` igual à versão em `schema_metadata` e à versão mais recente suportada;
- tabelas exigidas por cada versão;
- `PRAGMA foreign_key_check`;
- `PRAGMA integrity_check`.

## Migração dos stores legados

O comando público é:

```bash
python scripts/migrate_local_data.py --dry-run
python scripts/migrate_local_data.py --apply
python scripts/migrate_local_data.py --verify
```

`--dry-run` é o padrão e não cria banco nem diretório de backup. O relatório JSON contém:

```text
mode, data_dir, database_path
found, imported, duplicates, rejected
warnings, backup_path, schema_version
original_files_preserved, success
```

Antes de importar, `--apply` cria um backup completo do diretório de dados. A importação ocorre em uma transação e registra cada item em `legacy_migration_history`. Os JSON/JSONL originais não são apagados.

Stores reconhecidos:

```text
profile/profiles.json
memory/career-profile.json
memory/career-memory.jsonl
sotuhire-history.json
sotuhire-opportunities.json
sources/imports.json
public_exams/notices.json
radar/radar.json
radar/schedules.json
companion/captures.jsonl
companion/active-context.json
portfolio/project-analyses.jsonl
```

Linhas ou arquivos inválidos são rejeitados com warning; a origem é preservada. Se uma candidatura antiga não tiver o texto do anúncio, a migração não inventa um snapshot. Capturas/oportunidades com texto original podem produzir `job_snapshots`.

## Rollback

Não existe migração `down` automática. As estratégias registradas apontam para:

1. validar o backup com `scripts/restore_data.py` sem `--apply`;
2. restaurar o backup pré-migração se necessário;
3. continuar usando os JSON/JSONL, que permanecem no disco.

Um banco já existente sem versão reconhecida não recebe backup isolado pelo runner porque sua versão calculada é zero. Para dados legados, use sempre `scripts/migrate_local_data.py --apply`, que cria o backup completo antes da alteração.

## Estado de execução

Os testes automatizados exercitam criação, idempotência, FKs e imutabilidade em diretórios temporários. Esta documentação não afirma que `--apply` tenha sido executado sobre os dados reais do ambiente; essa decisão exige revisão do dry-run e autorização explícita.
