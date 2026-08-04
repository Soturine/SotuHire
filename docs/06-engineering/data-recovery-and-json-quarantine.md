# Recuperação de dados e quarantine JSON

SQLite é a fonte de verdade para candidaturas, eventos e snapshots. Os stores
JSON/JSONL que continuam ativos por compatibilidade usam uma política única de
recuperação em `modules.storage.json_recovery`.

Uma leitura inválida nunca retorna estado vazio. O arquivo original é movido
para `.quarantine`, um marcador sem conteúdo pessoal registra apenas tipo de
erro, data e caminho, e o store passa a `degraded`. Enquanto esse marcador
existir, leituras e gravações são bloqueadas para impedir que um estado novo
sobrescreva dados recuperáveis.

Gravações válidas usam um arquivo temporário com nome único, `fsync`, replace
atômico e até três backups rotativos em `.backups`. A regra está aplicada ao
Perfil Universal, histórico legado do Tracker, Companion, Radar, scheduler e
repositórios JSON/JSONL de compatibilidade.

## Diagnóstico e restore explícito

O diagnóstico é somente leitura:

```bash
python scripts/check_data_health.py
```

Um marcador degraded aparece como `json_store_degraded` e faz o comando sair
com erro. Escolha manualmente um backup conhecido e valide-o antes de restaurar:

```bash
python scripts/restore_json_store.py data/profile/profiles.json \
  data/profile/.backups/profiles.json.TIMESTAMP.bak

python scripts/restore_json_store.py data/profile/profiles.json \
  data/profile/.backups/profiles.json.TIMESTAMP.bak --apply
```

Para JSONL, acrescente `--jsonl`. O restore valida o conteúdo, grava de forma
atômica e somente então remove o marcador degraded. A quarantine permanece como
evidência recuperável até uma limpeza manual consciente.
