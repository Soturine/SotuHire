# Arquitetura de repositórios e persistência local

## Objetivo

A camada `modules/storage` fornece persistência local transacional sem transformar o SotuHire em um serviço de banco de dados. A arquitetura é incremental: os stores JSON/JSONL existentes continuam legíveis e não são apagados, enquanto os fluxos que precisam de integridade referencial, histórico imutável ou auditoria usam SQLite.

O diretório de dados é definido por `SOTUHIRE_DATA_DIR`. Sem essa variável, o padrão é `data/`; o banco padrão é `data/sotuhire.db`.

`/data/` é ignorado pelo Git. Banco, JSON/JSONL locais e backups são artefatos de runtime e não devem entrar em commit ou pacote público.

```text
Módulos de produto
  ├─ stores legados JSON/JSONL
  ├─ EntityRepository (contrato comum)
  │    ├─ JsonRepository
  │    ├─ JsonlRepository
  │    └─ SqliteRepository
  └─ stores SQLite especializados
       ├─ SnapshotStore
       ├─ ApplicationRepository
       └─ AiRunStore
```

Não há Redis, servidor SQL, fila distribuída ou banco vetorial nessa camada.

## Contrato comum

`modules/storage/repositories/base.py` define `EntityRepository`, um `Protocol` estrutural com cinco operações:

```python
class EntityRepository(Protocol):
    def get(self, entity_id: str) -> dict[str, object] | None: ...
    def list(self, *, filters: Mapping[str, object] | None = None) -> list[dict[str, object]]: ...
    def save(self, entity: Mapping[str, object]) -> dict[str, object]: ...
    def delete(self, entity_id: str) -> bool: ...
    def exists(self, entity_id: str) -> bool: ...
```

O contrato é propositalmente pequeno. Ele permite substituir o adapter sem levar detalhes de arquivo ou SQL para serviços novos, mas não tenta esconder consultas relacionais complexas.

## Adapters

### `JsonRepository`

- espera um documento JSON cuja raiz seja uma lista de objetos;
- exige um campo de identidade, `id` por padrão;
- atualiza ou acrescenta por identidade;
- grava em um arquivo `.tmp` e usa substituição do arquivo de destino;
- aplica filtros por igualdade em memória;
- propaga JSON inválido e raiz incompatível como erro, em vez de retornar silenciosamente uma lista vazia.

### `JsonlRepository`

- exige um objeto JSON por linha não vazia;
- informa corrupção com o número da linha;
- reescreve o arquivo completo por meio de `.tmp` ao salvar ou apagar;
- mantém o mesmo contrato e a mesma semântica de filtros do adapter JSON.

Ele é um adapter de compatibilidade, não um log append-only para alto volume.

### `SqliteRepository`

- atende tabelas simples com `id`, `payload`, `created_at` e `updated_at`;
- valida nomes de tabela e campo por expressão regular antes de interpolá-los no SQL;
- usa parâmetros para valores;
- faz upsert do JSON serializado em `payload`;
- ordena listagens por `updated_at DESC`;
- aplica filtros de conteúdo depois de desserializar os registros.

O adapter genérico pressupõe que a tabela já exista. `MigrationRunner` ou `ensure_database()` deve preparar o schema antes do primeiro uso.

## Stores especializados

Algumas entidades não cabem no contrato CRUD genérico:

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

- `LocalStore` e stores de domínio existentes continuam atendendo fluxos legados;
- o Tracker mantém o cartão mutável no JSON e também persiste vínculos confiáveis em SQLite;
- Editais continuam com estado revisável em JSON e criam histórico imutável no SQLite;
- a Local Companion mantém sua fila/capturas e cria snapshots no banco local;
- scripts de migração importam cópias dos stores conhecidos, sem apagá-los.

Essa duplicidade é deliberada enquanto a transição está em andamento. O SQLite é a fonte dos vínculos e snapshots novos; os JSON/JSONL continuam sendo fontes legadas compatíveis até que cada módulo seja migrado de forma explícita.

## Transações e atomicidade

- cada migração de schema é validada e confirmada separadamente;
- a importação dos registros legados ocorre dentro de `BEGIN IMMEDIATE`;
- inserts repetidos são controlados por `legacy_migration_history`;
- adapters JSON/JSONL usam troca de arquivo, mas não oferecem transação entre vários stores;
- backup e restore possuem suas próprias garantias, descritas em [Backup, restauração e saúde dos dados](backup-restore-and-data-health.md).

## Segurança

- a camada não precisa de credenciais de banco;
- chaves de provedores não fazem parte do schema;
- `AiRunStore` rejeita campos/textos com marcadores de autorização ou formatos conhecidos de chaves;
- backups filtram nomes e conteúdo textual com aparência de segredo;
- o frontend recebe metadados de arquivos, nunca o caminho absoluto do diretório de dados.

O banco SQLite é incluído integralmente no backup. Portanto, a regra principal continua sendo não persistir segredos no banco. O filtro de conteúdo do backup não abre nem reescreve tabelas SQLite.

## Limitações atuais

- nem todos os módulos dependem de `EntityRepository` ainda;
- filtros do adapter SQLite genérico não são convertidos em `WHERE` sobre o JSON;
- JSON/JSONL continuam sem transação cruzada;
- o runner não implementa migração `down`; rollback é restauração do backup;
- arquivos legados corrompidos são reportados e preservados, não reparados automaticamente;
- dados antigos sem o texto original não recebem conteúdo inventado para preencher snapshot.

## Testes relacionados

```bash
pytest tests/test_storage_repository_contract.py
pytest tests/test_storage_migrations.py
pytest tests/test_storage_snapshots.py
pytest tests/test_legacy_data_migration.py
```

Os testes usam diretórios temporários; eles não autorizam nem representam uma migração aplicada sobre os dados reais da pessoa usuária.
