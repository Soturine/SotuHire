# Backup, restauração, export e saúde dos dados

## Escopo

`modules/storage/backup.py` cria arquivos ZIP portáteis com manifesto e checksum. `modules/storage/health.py` executa verificações somente leitura. As mesmas capacidades são expostas por CLI e pela API local, com proteções adicionais no fluxo HTTP.

## Backup e export

Comandos:

```bash
python scripts/backup_data.py
python scripts/backup_data.py --export
python scripts/backup_data.py --data-dir data --output caminho/arquivo.zip
```

Sem `--output`, os nomes são:

```text
data/backups/sotuhire-data-backup-YYYYMMDD-HHMMSS.zip
data/backups/sotuhire-data-export-YYYYMMDD.zip
```

Backup e export usam o mesmo formato. O campo `kind` e o nome distinguem a finalidade.

### Manifesto

Cada ZIP inclui `manifest.json` com:

```text
format_version
kind
app_version
schema_version
max_supported_schema_version
created_at
files[]: path, size, sha256
excluded_categories
excluded_files
```

O banco SQLite é copiado pela API de backup do próprio SQLite antes de entrar no ZIP. Isso evita copiar um arquivo em estado intermediário enquanto WAL/transações estão ativos.

`schema_version` vem do histórico do banco copiado; vale `0` quando não existe banco. `max_supported_schema_version` registra a versão máxima entendida pelo aplicativo que gerou o arquivo.

### Arquivos elegíveis

Extensões aceitas:

```text
.json .jsonl .db .sqlite .sqlite3 .toml .yaml .yml
```

Diretórios/categorias excluídos incluem:

```text
secrets, secret, credentials, tokens, cookies
scraping-cache, backups, __pycache__
```

Também são excluídos:

- nomes contendo `api-key`, `apikey`, `credential`, `secret`, `token` ou `cookie`;
- arquivos ocultos e nomes com `.local.`;
- arquivos textuais que correspondam a formatos de chave Gemini/OpenAI ou atribuições de credencial/autorização/token;
- arquivos fora da lista de extensões permitidas.

`chrome.storage`, IndexedDB e storage de terceiros não ficam no diretório de dados e não são coletados.

### Limite importante

O filtro de conteúdo não inspeciona internamente bancos SQLite. O banco entra inteiro no arquivo; por isso o schema e os serviços não devem persistir chaves. `AiRunStore` rejeita metadados com aparência de segredo, mas essa defesa não substitui a regra de nunca gravar credenciais em entidades genéricas.

## Restauração por CLI

Validação sem alterar dados:

```bash
python scripts/restore_data.py data/backups/sotuhire-data-backup-YYYYMMDD-HHMMSS.zip
```

Aplicação explícita:

```bash
python scripts/restore_data.py data/backups/sotuhire-data-backup-YYYYMMDD-HHMMSS.zip --apply
```

Antes de aplicar, o restore verifica:

1. existência e validade do `manifest.json`;
2. compatibilidade: o schema do arquivo não pode ser mais novo que o suportado;
3. caminhos relativos sem `..` ou raiz absoluta;
4. categoria/extensão permitida;
5. presença de cada arquivo declarado;
6. SHA-256 de cada conteúdo.

No modo padrão, retorna apenas `files_validated`; `files_restored` permanece zero. Com `--apply`, cria backup preventivo quando o destino já contém dados, extrai em staging temporário e substitui cada arquivo por meio de um arquivo `.restore`.

A substituição é atômica por arquivo, não por diretório inteiro. Se o sistema operacional falhar no meio de vários arquivos, use `pre_restore_backup` para recuperar o estado anterior.

## API local

Endpoints:

```text
GET  /api/v1/data/health
GET  /api/v1/data/backups
POST /api/v1/data/backups
GET  /api/v1/data/backups/{archive_name}
POST /api/v1/data/restore
```

Criação:

```json
{ "kind": "backup" }
```

ou:

```json
{ "kind": "export" }
```

A API não aceita destino arbitrário. Ela cria e lista apenas arquivos em `<data-dir>/backups`. As respostas expõem `archive_name`, tamanho, versão, schema, quantidade de arquivos e URL de download — nunca o caminho absoluto local. O download usa `Cache-Control: no-store`.

A listagem aceita somente nomes SotuHire cujo manifesto possa ser lido. O checksum completo é validado na etapa de restore.

### Restore HTTP em duas etapas

Dry-run padrão:

```json
{
  "archive_name": "sotuhire-data-backup-YYYYMMDD-HHMMSS.zip"
}
```

Aplicação:

```json
{
  "archive_name": "sotuhire-data-backup-YYYYMMDD-HHMMSS.zip",
  "apply": true,
  "confirmation": "RESTAURAR"
}
```

O nome precisa obedecer ao padrão SotuHire, ser apenas basename e resolver dentro do diretório gerenciado. A palavra de confirmação é exata. O frontend `/privacy` exige primeiro o dry-run e abre uma confirmação final antes de aplicar.

No modo Demo, a interface simula o fluxo sem criar, baixar ou restaurar arquivos reais.

## Data health

Comando:

```bash
python scripts/check_data_health.py
python scripts/check_data_health.py --data-dir data --database data/sotuhire.db
```

O relatório traz `checked_at`, caminhos locais no CLI, versão do schema, `healthy`, contagens e issues. A resposta HTTP remove caminhos absolutos.

### Verificações dos stores legados

- JSON/JSONL inválido;
- IDs duplicados no mesmo store;
- memória sem `source_ref`, `source_refs` ou `source_id`;
- datas inválidas em campos conhecidos;
- contagem por arquivo reconhecido.

### Verificações SQLite

- versão atual versus `LATEST_SCHEMA_VERSION` e consistência entre `migration_history` e `schema_metadata`;
- banco inválido ou ilegível, convertido em issue `database_unreadable` em vez de erro HTTP não tratado;
- histórico e validação de todas as migrações;
- `foreign_key_check` e `integrity_check`;
- contagem por tabela;
- datas inválidas em colunas terminadas em `_at`;
- candidatura sem `job_snapshot_id`;
- oportunidade sem origem;
- oportunidade ou edital sem snapshot;
- hashes de snapshot repetidos em registros distintos;
- AiRun sem provider/modo ou fallback sem motivo.

### Severidade

| Severidade | Efeito em `healthy` | Exemplo |
|---|---|---|
| `info` | não altera | banco ainda não criado |
| `warning` | não altera | candidatura legada sem snapshot |
| `error` | define `healthy=false` | JSON/banco ilegível, schema divergente, falha de integridade |

Um relatório saudável pode conter warnings. O health check não corrige, apaga ou mescla registros.

### Limitações do health check

- a inspeção legada é estrutural e não valida toda regra de negócio de cada módulo;
- o flatten de JSON cobre raiz e listas de primeiro nível, não qualquer objeto profundamente aninhado;
- alguns conjuntos de issues são limitados aos primeiros 20 exemplos;
- o hash armazenado não é recalculado para todo registro genérico;
- warnings precisam de revisão humana; não autorizam merge ou descarte automático.

## Ordem operacional recomendada

```text
health read-only
→ migration dry-run
→ revisar rejeições/duplicatas/warnings
→ backup explícito
→ apply autorizado
→ verify
→ health novamente
→ teste de restore em diretório temporário
```

Consulte também o [checklist de migração limpa](../07-development/v1.9.6-clean-migration-checklist.md).

## Testes

```bash
pytest tests/test_storage_backup_restore.py
pytest tests/test_api_data_reliability.py
cd apps/web && npx playwright test tests/e2e/data-reliability.spec.ts --project=chromium
```

Esses testes usam dados temporários/fictícios. Eles não significam que um restore ou `--apply` tenha sido executado sobre dados reais.
