# Schema repair e fallback

Structured output é validado contra o schema Pydantic da task. O parser não preenche campo inválido com default silencioso.

O orçamento máximo é uma resposta original e um reparo. O reparo recebe somente a resposta inválida e o schema sanitizado, não recebe segredo nem contexto adicional, e é instruído a preservar fatos existentes. A execução registra `repair_attempted`, `repaired` e `repair_reason`; reparos são medidos separadamente.

Truncamento, resposta vazia, safety block e schema ainda inválido geram categoria própria. Um reparo não pode completar evidência ausente nem transformar conteúdo não confirmado em fato.

Quando o produto possui motor local, fallback precisa declarar provider/modelo solicitado e usado, motivo e `degraded_mode`. Quando a suite externa mede o provider em si, não há fallback: a falha permanece falha para que schema validity não seja inflada.
