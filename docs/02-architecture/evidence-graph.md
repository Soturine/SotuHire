# Evidence Graph

O graph usa SQLite, não Neo4j. `evidence_nodes` representa 27 tipos de entidade e
`evidence_edges` possui relações tipadas, `evidence_refs`, `source_refs`, review, confiança e stale.
Nós candidatos vêm de documento, Lattes, GitHub, extensão, IA ou input manual. Merge automático só
ocorre com identidade forte; o restante permanece na Evidence Inbox.

Status: `candidate`, `confirmed`, `rejected`, `stale`. Confiança não substitui revisão. Registros
profissionais usam `sensitive=true`; o número não integra contexto externo por padrão.

