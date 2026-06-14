# Career Memory Store

O store da v0.8.0 usa JSONL local para manter a implementação portátil, legível e sem banco
externo obrigatório.

## Arquivos locais

```text
data/memory/
├── career-memory.jsonl
└── career-profile.json

exports/memory/
├── career-memory.json
├── career-memory.jsonl
└── career-memory-summary.md
```

`data/` e `exports/` são ignorados pelo Git.

## Contrato

Cada `CareerMemoryItem` contém identificador, tipo, título, conteúdo, fonte, confiança, tags e
timestamps. Operações de escrita reconstroem o arquivo por meio de um temporário e fazem a troca
atômica ao final.

O store oferece:

- adicionar ou substituir por ID;
- atualizar e excluir;
- listar e filtrar por tipo;
- buscar localmente;
- exportar JSON/JSONL;
- importar JSON/JSONL;
- apagar toda a memória.

## IDs e deduplicação

Currículo, análise e oportunidade usam IDs determinísticos quando existe contexto suficiente.
Eventos e feedbacks podem manter IDs únicos porque representam ocorrências no tempo.

## Falhas

Um arquivo ausente ou inválido retorna uma coleção vazia para preservar o uso do app. A pessoa
usuária pode importar um backup ou reconstruir a memória a partir de novas análises.
