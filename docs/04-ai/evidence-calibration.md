# Calibração de evidências

A v0.9.0 mantém o retrieval local e explicável, mas substitui uma ordenação lexical simples por um
ranking calibrado com componentes visíveis.

## Componentes do score

- sobreposição lexical;
- compatibilidade de tags;
- boost configurável por tipo de memória;
- recência;
- penalidade para evidência genérica;
- penalidade para item antigo e pouco relacionado;
- feedback útil ou não útil;
- ajuste por resultados anteriores.

O ranker limita quantas evidências de cada tipo podem entrar no resultado e registra o motivo de
seleção e o breakdown do score.

## Feedback

Na aba **Evidências**, a pessoa marca cada item como **Útil** ou **Não útil**. O evento fica na
Career Memory e altera futuras ordenações por regras simples, sem treinamento de ML.

## Princípios

- evidência não vira competência inventada;
- score ajuda a ordenar, não prova experiência;
- gaps recorrentes recebem visibilidade;
- feedback negativo reduz prioridade, mas não apaga o histórico;
- Gemini recebe evidências apenas quando houver opt-in explícito.

Relatórios de projeto adicionam tipos priorizados como `project_evidence`, `github_repo`,
`portfolio`, `commit_analysis` e `readme_analysis`. O ranking continua limitado por tipo para que
um único repositório não domine todas as evidências de uma vaga.
