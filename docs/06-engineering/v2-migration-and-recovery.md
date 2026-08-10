# Migração e recuperação v2

A v2.0 eleva o SQLite ao schema 8 para Evidence Graph, portfólio, Career State e Copilot. A migração
é incremental e preserva contratos `/api/v1`, tabelas anteriores e stores legados que ainda têm
consumidores.

## Antes de migrar

1. encerre API, Companion e processos que possam escrever;
2. identifique o diretório de dados correto;
3. crie backup verificável;
4. mantenha espaço livre para banco, WAL e archive;
5. não apague JSON/JSONL legado;
6. registre a versão atual e valide data health.

Nunca use uma cópia do banco enquanto outro processo mantém WAL não consolidado sem seguir o fluxo
de backup suportado.

## O que o schema 8 adiciona

- `evidence_nodes` e `evidence_edges`;
- `portfolio_items`;
- `career_state_snapshots`;
- `proposed_actions` e `action_executions`;
- `copilot_plans` e `copilot_plan_steps`;
- `copilot_audit_events` e `copilot_feedback`.

As tabelas v1 não são reescritas para acomodar o modelo v2. Isso reduz risco de perda e permite
upgrade gradual.

## Fluxo recomendado

```text
health/read-only
  → backup
  → dry-run quando aplicável
  → apply migration
  → verify
  → health novamente
  → iniciar aplicação
```

Dry-run e health devem ser read-only. Apply é explícito. Verify confere history, metadata, tabelas,
foreign keys e integrity.

## Upgrade v1.11.0 → v2.0

Uma instalação v1.11.0 está no schema 7. O runner aplica somente a migration 8, registra o history e
mantém tarefas, candidaturas, snapshots e dados anteriores. Reexecutar o runner não deve reaplicar a
migration.

Testes de release usam fixture schema 7 com dado v1 preservado e validam upgrade idempotente.

## Clean install

Instalação limpa aplica migrations 1→8 e depois executa verify. O gate da v2.0 também valida um
checkout exportado, venv novo, dependências, testes locais, pacote da extensão, docs e build web.

## Source of truth durante a transição

Novos domínios v2 escrevem somente no SQLite. JSON/JSONL legado continua disponível para módulos
anteriores, compatibilidade, fixture ou export. A migration não faz conversão destrutiva em massa e
não cria dual-write para o Evidence Graph.

Essa decisão evita uma migração difícil de reverter, mas exige que a arquitetura documente quais
domínios ainda usam repositories anteriores.

## Backup

O manifest informa versão do app, schema encontrado, schema máximo suportado, arquivos incluídos e
categorias excluídas. API keys, tokens, cookies e storage da extensão não entram no archive.

Guarde o backup fora do diretório que será restaurado e valide tamanho/manifest antes de depender
dele.

## Restore

Restore valida traversal, links, tamanho, checksum/manifest e schema antes de substituir arquivos.
Faça restore com processos de escrita encerrados. Depois:

1. execute verify;
2. rode data health;
3. confirme a versão do schema;
4. abra Perfil, Tracker, Evidence Inbox e Approval Queue;
5. não execute proposta antiga sem revisar stale/dependency hash.

## Rollback

O rollback recomendado da migration v8 é restaurar o backup pré-v8. Não tente remover tabelas
manualmente em uma instalação com dados reais. A restauração deve voltar banco e arquivos legados
como um conjunto coerente.

Se o app anterior for iniciado sobre schema mais novo, ele deve recusar operação incompatível em vez
de escrever parcialmente.

## Falhas e recuperação

### Migration interrompida

Não edite `migration_history` manualmente. Rode verify e preserve banco/WAL para diagnóstico. Se o
estado não for verificável, restaure o backup.

### Banco íntegro, UI vazia

Confirme diretório de dados, modo Demo/API Real, pairing e versão da API. Não importe novamente até
descartar que o frontend está apontando para outra base URL.

### Propostas stale após upgrade

É comportamento seguro. Gere novo Career State e nova proposta; não altere hash/status no banco.

### JSON legado corrompido

Data health identifica o store e o mecanismo de quarantine/recuperação aplicável. Isso não autoriza
apagar outros stores.

## Verificação mínima pós-upgrade

- schema atual é 8;
- migration history não tem erro;
- integrity e foreign keys estão válidos;
- dado v1 amostrado permanece acessível;
- Evidence Graph aceita candidato e revisão;
- Career State pode ser lido sem escrita implícita;
- proposta pendente não executa sem aprovação;
- backup/restore continuam excluindo segredos.

## Limites

- não há downgrade in-place do schema 8;
- não há migração destrutiva automática de todos os stores JSON;
- restore não substitui política externa de backup;
- backup local não protege contra perda simultânea do dispositivo;
- fixtures automatizadas não substituem validação do proprietário sobre dados pessoais reais.

## Links relacionados

- [Schema SQLite e migrations](../02-architecture/sqlite-schema-and-migrations.md)
- [Backup, restore e data health](../02-architecture/backup-restore-and-data-health.md)
- [Fluxo de dados v2](../02-architecture/data-flow.md)
- [Acceptance matrix v2](../09-testing/v2.0-acceptance-matrix.md)
- [Threat model v2](v2-security-threat-model.md)
