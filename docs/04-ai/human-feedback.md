# Feedback humano para IA

`AiFeedback` liga uma avaliação a `run_id` e `task_id` sem copiar a entrada ou saída. Ratings possíveis: `useful`, `partial`, `not_useful`. Decisões: `accepted`, `edited`, `rejected`, `ignored`. Também podem ser marcados edição, afirmação sem evidência e comentário opcional sanitizado.

O site permite criar e apagar feedback. A extensão 0.9.3 envia feedback do GitHub somente quando a IA do SotuHire devolve um trace persistido; o payload não inclui README, relatório, chave ou token.

Taxas de aceitação, edição e rejeição descrevem comportamento observado, não correção absoluta. Comentários podem conter dados pessoais e, por isso, são limitados, sanitizados e não entram em benchmarks públicos.
