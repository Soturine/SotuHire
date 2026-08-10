# Approval Queue

A fila agrupa propostas, nunca oferece “Aprovar tudo”. Cada card mostra razão, evidence refs,
entidades afetadas, before/after, risco, reversibilidade e undo strategy. Transições usam compare
and set; só `approved` pode executar. Execução e undo geram audit events separados.

