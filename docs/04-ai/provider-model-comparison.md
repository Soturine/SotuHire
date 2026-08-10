# Comparação de providers e modelos

A rota `/ai-quality` compara por tarefa:

| Task | Provider | Modelo | Qualidade | Latência | Custo | Fallback | Aceitação |
|---|---|---|---:|---:|---:|---:|---:|

Os valores vêm de traces, benchmarks e feedback; conteúdo pessoal completo não é exibido. A interpretação da amostra é fixa:

- `n < 5`: insuficiente;
- `5 <= n < 20`: indicativo;
- `n >= 20`: comparável.

Qualidade por custo e por latência só é calculada quando ambas as grandezas existem. Custo desconhecido permanece ausente; o sistema não inventa preço. Um provider não é declarado vencedor definitivo apenas por média agregada, pois tarefa, domínio, prompt e amostra podem diferir.

O provider local é a referência de disponibilidade e privacidade. Gemini e OpenAI são opt-in. Ollama, LM Studio e endpoints OpenAI-compatible continuam como capacidade futura: a v1.10.1 não introduz um adapter novo sem cobertura suficiente de structured output e fallback.

## Baseline da v1.9.7

O local validou 12/12 schemas. Gemini 2.5 Flash validou 9/12 no smoke real e registrou 25% de erros de provider; OpenAI 4.1 Mini retornou rate/quota limit em 12/12. Como `n=12`, os resultados são apenas indicativos. Há baseline local e Gemini; não há baseline OpenAI porque nenhuma saída estruturada foi válida. Consulte as [release notes](../releases/v1.9.7.md) para as métricas completas.

## Validação da v1.9.8

O local repetiu 12/12 schemas no release-smoke. Gemini 2.5 Flash aprovou o diagnóstico, mas o structured output e o smoke atingiram `RATE_LIMIT` após um retry; o teste opt-in também encontrou 503 de alta demanda. OpenAI 4.1 Mini foi classificada como `INSUFFICIENT_QUOTA`, sem retry e sem baseline. As amostras externas finais são `n=1` por suite e não permitem declarar vencedor. Consulte a [validação externa](../07-development/v1.9.8-external-provider-validation.md).

## Validação da v1.10.1

Em 2026-08-10, o diagnóstico concluiu 2/3 providers: local e Gemini responderam; OpenAI foi bloqueado por `INSUFFICIENT_QUOTA`. No structured output, local e Gemini mantiveram schema válido nos casos executados e o agregado ficou em 8/9; o único caso inválido foi o bloqueio da conta OpenAI. O release-smoke encerrou sem regressões, com `schema_validity=0.85`, resistência a prompt injection de 1.0 e um bloqueio externo OpenAI. Erros reais de casos Gemini permaneceram visíveis nas métricas, sem fallback para fingir aprovação.

`pytest -m external_ai` terminou com 2 casos aprovados e 2 skips explícitos por quota OpenAI. Esses números comprovam execução e classificação de falha, mas continuam insuficientes para eleger provider/modelo.
