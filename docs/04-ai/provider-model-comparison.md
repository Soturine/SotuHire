# Comparação de providers e modelos

A rota `/ai-quality` compara por tarefa:

| Task | Provider | Modelo | Qualidade | Latência | Custo | Fallback | Aceitação |
|---|---|---|---:|---:|---:|---:|---:|

Os valores vêm de traces, benchmarks e feedback; conteúdo pessoal completo não é exibido. A interpretação da amostra é fixa:

- `n < 5`: insuficiente;
- `5 <= n < 20`: indicativo;
- `n >= 20`: comparável.

Qualidade por custo e por latência só é calculada quando ambas as grandezas existem. Custo desconhecido permanece ausente; o sistema não inventa preço. Um provider não é declarado vencedor definitivo apenas por média agregada, pois tarefa, domínio, prompt e amostra podem diferir.

O provider local é a referência de disponibilidade e privacidade. Gemini e OpenAI são opt-in. Ollama, LM Studio e endpoints OpenAI-compatible continuam como capacidade futura: a v1.9.7 não introduz um adapter novo sem cobertura suficiente de structured output e fallback.

## Baseline da v1.9.7

O local validou 12/12 schemas. Gemini 2.5 Flash validou 9/12 no smoke real e registrou 25% de erros de provider; OpenAI 4.1 Mini retornou rate/quota limit em 12/12. Como `n=12`, os resultados são apenas indicativos. Há baseline local e Gemini; não há baseline OpenAI porque nenhuma saída estruturada foi válida. Consulte as [release notes](../releases/v1.9.7.md) para as métricas completas.
