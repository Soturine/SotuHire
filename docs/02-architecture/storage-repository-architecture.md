# Arquitetura de repositórios e persistência local

## Objetivo

A camada `modules/storage` fornece persistência local transacional sem transformar o SotuHire em um serviço de banco de dados. A arquitetura é incremental: os stores JSON/JSONL existentes continuam legíveis e não são apagados, enquanto os fluxos que precisam de integridade referencial, histórico imutável ou auditoria usam SQLite.

O diretório de dados é definido por `SOTUHIRE_DATA_DIR`. Sem essa variável, o padrão é `data/`; o banco padrão é `data/sotuhire.db`.

`/data/` é ignorado pelo Git. Banco, JSON/JSONL locais e backups são artefatos de runtime e não devem entrar em commit ou pacote público.

```text
Módulos de produto
  ├─ stores legados JSON/JSONL (LocalStore, perfil universal, fontes, editais)
  └─ stores SQLite especializados
       ├─ SnapshotStore
       ├─ ApplicationRepository
       └─ AiRunStore
```

Não há Redis, servidor SQL, fila distribuída ou banco vetorial nessa camada.

## Por que não há um repositório genérico

Até 2026-11 existia `modules/storage/repositories` (`EntityRepository`, `JsonRepository`,
`JsonlRepository`, `SqliteRepository`), um CRUD genérico criado em 2026-07 para uma migração
futura. Nenhum módulo de produto chegou a usá-lo: os únicos consumidores eram o próprio teste de
contrato e este documento. Ele foi removido na auditoria de 2026-11 (ver
[triagem de duplicação e código morto](../00-audit/2026-11-dead-dedupe-triage.md)); o código
continua no histórico do Git.

As entidades que precisam de persistência têm stores próprios, porque cada uma tem invariantes que
um CRUD genérico não expressa (dedupe por hash, FKs, transações entre tabelas, bloqueio de
segredos).

## Stores especializados

Stores SQLite em uso:

| Store | Responsabilidade | Por que é especializado |
|---|---|---|
| `SnapshotStore` | criar e recuperar snapshots por conteúdo | dedupe por hash, FKs e imutabilidade |
| `ApplicationRepository` | vincular candidatura a snapshots e registrar eventos | gravação coordenada de `applications` e `application_events` |
| `AiRunStore` | persistir metadados seguros de execução | schema próprio e bloqueio de material com aparência de segredo |

Esses stores chamam `ensure_database()` e trabalham sobre o schema versionado.

## Conexões SQLite

`modules/storage/database.py` abre conexões de escrita com:

```text
PRAGMA foreign_keys = ON
PRAGMA busy_timeout = 5000
PRAGMA journal_mode = WAL
PRAGMA synchronous = NORMAL
```

A conexão usa `sqlite3.Row`, timeout de cinco segundos e é fechada ao sair do bloco `with`, inclusive após rollback. SQLite continua sendo um arquivo local; WAL melhora convivência entre leituras e gravações, mas não substitui coordenação entre vários processos escrevendo intensamente.

Health check e verificação de migrações usam `connect_readonly_database()`, que abre um banco existente por URI com `mode=ro` e não altera schema nem modo de journal.

## Compatibilidade durante a transição

A migração não troca todos os stores de uma vez:

- `LocalStore` é somente compatibilidade de import/export e fallback de leitura antes da
  primeira gravação canônica;
- o Tracker lê e grava novos cartões em `applications` no SQLite; não faz dual-write JSON;
- Editais continuam com estado revisável em JSON e criam histórico imutável no SQLite;
- a Local Companion mantém sua fila/capturas e cria snapshots no banco local;
- scripts de migração importam cópias dos stores conhecidos, sem apagá-los.

SQLite é a fonte de verdade de candidaturas, eventos, links e snapshots. Os
JSON/JSONL continuam como fontes legadas preservadas até migração explícita, mas
não recebem novas gravações do Tracker.

## Transações e atomicidade

- cada migração de schema é validada e confirmada separadamente;
- a importação dos registros legados ocorre dentro de `BEGIN IMMEDIATE`;
- inserts repetidos são controlados por `legacy_migration_history`;
- stores JSON/JSONL usam troca de arquivo, mas não oferecem transação entre vários stores;
- a conclusão do Application Lab usa `BEGIN IMMEDIATE` para cartão, links,
  `application_created`, status da sessão e chave idempotente;
- a chave estável combina perfil, identidade da oportunidade, snapshots, sessão e ação;
- referências de captura inexistentes ficam em `pending_link` com referência externa,
  sem criar entidade fictícia para satisfazer FK;
- backup e restore possuem suas próprias garantias, descritas em [Backup, restauração e saúde dos dados](backup-restore-and-data-health.md).

## Segurança

- a camada não precisa de credenciais de banco;
- chaves de provedores não fazem parte do schema;
- `AiRunStore` rejeita campos/textos com marcadores de autorização ou formatos conhecidos de chaves;
- backups filtram nomes e conteúdo textual com aparência de segredo;
- o frontend recebe metadados de arquivos, nunca o caminho absoluto do diretório de dados.

O banco SQLite é incluído integralmente no backup. Portanto, a regra principal continua sendo não persistir segredos no banco. O filtro de conteúdo do backup não abre nem reescreve tabelas SQLite.

## Limitações atuais

- JSON/JSONL continuam sem transação cruzada;
- o runner não implementa migração `down`; rollback é restauração do backup;
- arquivos legados corrompidos são reportados e preservados, não reparados automaticamente;
- dados antigos sem o texto original não recebem conteúdo inventado para preencher snapshot.

## Testes relacionados

```bash
pytest tests/test_storage_migrations.py
pytest tests/test_storage_snapshots.py
pytest tests/test_legacy_data_migration.py
```

Os testes usam diretórios temporários; eles não autorizam nem representam uma migração aplicada sobre os dados reais da pessoa usuária.
