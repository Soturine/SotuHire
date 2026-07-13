# Avaliação da IA

A avaliação de IA no SotuHire mede se uma saída é válida, baseada em evidências, útil e segura. “O JSON abriu” não é suficiente: uma resposta pode estar estruturalmente correta e ainda atribuir uma experiência inexistente, omitir a evidência mais importante ou esconder um fallback.

O benchmark completo pertence ao ciclo de avaliação e tracing. Esta fundação define métricas, dados necessários e regras de execução sem transformar chamadas externas em requisito do CI padrão.

## Dimensões obrigatórias

| Dimensão | Pergunta |
| --- | --- |
| Schema validity | A resposta valida no contrato Pydantic/JSON esperado? |
| Field extraction accuracy | Os campos extraídos correspondem ao documento de origem? |
| Evidence precision | As evidências citadas realmente sustentam a afirmação? |
| Evidence recall | As evidências relevantes presentes na entrada foram recuperadas? |
| Unsupported claim rate | Quantas afirmações não possuem suporte na entrada/contexto permitido? |
| Hallucination rate | Quantas afirmações contradizem ou inventam fatos? |
| Confidence calibration | Confiança declarada acompanha a taxa observada de acerto? |
| Fallback rate | Com que frequência o provider solicitado não produz a saída final? |
| Latency | Quanto tempo o fluxo leva localmente e por provider/modelo? |
| Token usage | Quantos tokens de entrada/saída são usados? |
| Estimated cost | Qual o custo estimado por execução e capacidade? |
| Human acceptance/rejection | A pessoa aceita, edita ou rejeita cada sugestão? |
| Provider agreement | Providers diferentes concordam nos fatos e evidências centrais? |
| Dedup precision/recall | A identidade une duplicatas reais sem mesclar entidades distintas? |

## Princípios

- comparar saída com evidência anotada, não com preferência estética;
- medir extração, análise e deduplicação separadamente;
- estratificar por área profissional, tipo de documento e dificuldade;
- registrar provider/modelo solicitado e usado, prompt, fallback e warnings;
- nunca enviar dado pessoal real para benchmark;
- tratar item incerto como “a confirmar”, não como erro convertido em certeza;
- manter revisão humana para currículo, recomendação, edital e candidatura;
- não exigir Gemini/OpenAI reais no CI padrão.

## Execução

Mocks e fixtures determinísticos rodam em todo commit. Testes externos usam somente chaves temporárias novas, fornecidas por variável de ambiente local e marcadas como `external_ai`; sem variável, são skipped.

```bash
pytest
pytest -m external_ai
```

O segundo comando não deve ser executado com chaves que apareceram em prompt, conversa, screenshot, log ou histórico. Relatórios não podem conter chave, payload sensível ou traceback com segredo.

## Saídas esperadas

Uma avaliação deve produzir, no mínimo:

- versão do dataset e hash das fixtures;
- commit, prompt e schema avaliados;
- provider/modelo solicitado e usado;
- métricas agregadas e por segmento;
- número de casos executados, skipped e inválidos;
- exemplos sintéticos de falha, sem dados pessoais;
- decisão humana sobre regressão e próximos ajustes.

O desenho completo, critérios de anotação e sequência de adoção estão no [plano de avaliação](ai-evaluation-plan.md). A composição dos dados está em [Golden datasets](../09-testing/golden-datasets.md).
