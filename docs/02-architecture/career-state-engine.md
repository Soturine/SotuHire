# Career State Engine

`CareerStateEngine` agrega SQLite de forma determinística e produz um dependency hash. Ele separa
cobertura de dados, confiança de regra e confiança de provider. Apps, entrevistas, follow-ups,
tasks vencidas, evidências, edges, portfólio, oportunidades e outcomes compõem o estado.

Snapshots são explícitos; render comum não grava. Next Best Actions são ordenadas por regras
transparentes. IA pode explicar o estado, mas não recalcular fatos ou confirmar relações.

