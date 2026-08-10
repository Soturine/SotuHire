# Migração e recuperação v2

Schema 8 adiciona tabelas v2 sem reescrever tabelas v1. `MigrationRunner` suporta 6/7→8 e cria
backup em upgrade real. Dry-run e health são read-only; apply é explícito; verify confere history,
metadata, tabelas, foreign keys e integrity. Rollback recomendado restaura o backup pré-v8.

```bash
python scripts/migrate_local_data.py --dry-run
python scripts/migrate_local_data.py --apply
python scripts/migrate_local_data.py --verify
```

