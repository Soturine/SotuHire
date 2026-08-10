# Camada de taxonomias

`modules/taxonomy` representa CBO, QBQ, ESCO e O*NET sem redistribuir datasets oficiais. Manifestos guardam versão, URL, licença, data e SHA-256; snapshots são imutáveis e content-addressed.

O normalizer separa ocupação de skill. Métodos: exact, alias, normalized, taxonomy crosswalk, semantic candidate e manual. Candidatos semânticos começam em revisão e só viram confirmed/rejected com `reviewed_at` explícito. CBO não prova profissão regulamentada.

Manifestos e decisões ficam no SQLite v7; registros do dataset ficam no cache local verificado.
