# Custo, tokens e latência de IA

Cada trace pode registrar início/fim, `latency_ms`, tokens de entrada/saída/total e custo estimado. Campos ficam nulos quando o provider não os informa ou quando não existe tabela de preço confiável no runtime.

O painel agrega p50/p95, tokens e custo por tarefa/provider/modelo, e as taxas de aceitação, edição e rejeição humanas; sem decisões registradas essas taxas ficam nulas, nunca zero. Custo por sugestão aceita e qualidade por custo/latência não são calculados: as funções que existiam para isso não tinham consumidor e devolveriam `0.0` com denominador zero; foram removidas em 2026-11.

O release-smoke usa no máximo 10 chamadas por provider nesta versão, apenas fixtures fictícias. Relatórios persistem métricas e identificadores, nunca prompts, respostas completas ou segredos.
