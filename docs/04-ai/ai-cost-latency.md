# Custo, tokens e latência de IA

Cada trace pode registrar início/fim, `latency_ms`, tokens de entrada/saída/total e custo estimado. Campos ficam nulos quando o provider não os informa ou quando não existe tabela de preço confiável no runtime.

O painel agrega p50/p95, tokens e custo por tarefa/provider/modelo. `cost_per_accepted_suggestion`, `quality_per_cost` e `quality_per_latency` exigem denominadores observados e amostra explícita. Divisão por zero ou dado ausente não produz um número artificial.

O release-smoke usa no máximo 10 chamadas por provider nesta versão, apenas fixtures fictícias. Relatórios persistem métricas e identificadores, nunca prompts, respostas completas ou segredos.
