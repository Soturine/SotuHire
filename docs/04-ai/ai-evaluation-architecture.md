# Arquitetura de avaliação da IA

A avaliação da IA do SotuHire separa qualidade do conteúdo, confiabilidade operacional e utilidade humana. A ordem é deliberada: schema, regras determinísticas, labels golden, avaliação humana e, somente como apoio opcional, LLM-as-a-judge.

## Componentes

```text
AiTask + PromptSpec
  → provider ou fallback local
  → schema guard + validação de afirmações
  → AiRunStore (metadados seguros)
  → métricas determinísticas/golden
  → feedback humano
  → associação exploratória com outcomes
```

`modules/ai/task_registry.py` vincula as 16 tarefas de produção a prompt, versão, schemas, providers, fallback, propósito de contexto, política sensível e suíte. `modules/ai/evaluation/` contém o contrato das fixtures e métricas puras. O runner reprodutível está em `scripts/run_ai_benchmark.py`.

## Evidência e confiança

Uma saída JSON válida ainda pode estar errada. Por isso, validade de schema é medida antes de `evidence_precision`, `evidence_recall`, cobertura de referências e taxa de afirmações sem suporte. Confiança é comparada com acerto observado usando Brier score e erro de calibração; ela nunca substitui evidência.

Os cenários de contexto são:

- A: sem Perfil;
- B: Perfil confirmado;
- C: Perfil confirmado mais memória/RAG;
- D: Perfil, memória e itens não confirmados.

No cenário D, itens não confirmados são dados não confiáveis e não podem virar fatos. A comparação mede evidência, claims sem suporte, utilidade, latência e tokens.

A fixture determinística da release executa A–D em `tests/test_ai_context_ab_evaluation.py`. Ela confirma `unconfirmed_fact_rate=0` no cenário D; os valores de utilidade/tokens são labels controladas de política, não benchmark de provider.

## Privacidade dos traces

Por padrão, `ai_trace_store_inputs=false`, `ai_trace_store_outputs=false` e `ai_trace_store_redacted_excerpts=true`. O trace guarda hashes, contagens, referências seguras e métricas; não guarda chave, Authorization, cookie, token, currículo, vaga, prompt, resposta ou contexto pessoal integral. A retenção padrão é 90 dias e pode ser configurada por `ai_trace_retention_days`.

## Limites

O sistema não declara vencedor de provider com amostra insuficiente, não infere causalidade a partir do Tracker, não altera Perfil/pesos automaticamente e funciona sem provider externo por meio de fallback determinístico explícito.
