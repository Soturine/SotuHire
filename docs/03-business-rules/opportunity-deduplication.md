# Deduplicação de oportunidades

Ordem de identidade:

1. mesmo provider + external_id: confiança 1,00;
2. URL canônica igual: 0,99;
3. organização + título + local iguais: 0,93;
4. similaridade textual com mesma organização: candidato abaixo de 0,86 e revisão obrigatória.

Merges preservam todas as proveniências e preferem o conteúdo observado mais recentemente. Query strings de tracking e fragments não participam da URL canônica. Nunca fundir apenas por título.

Ranking é local primeiro; fit (0–100), confiança (0–1) e cobertura de evidência (0–1) são campos separados. IA opcional recebe somente o top-K limitado a 100.
