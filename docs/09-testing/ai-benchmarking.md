# Benchmarking de IA

O runner suporta `mock`, `local`, `release-smoke`, `golden`, `adversarial` e `full`, com filtros de providers, modelos, tarefas, domínios, máximo de casos, seed, output, resume e regressão.

```bash
python scripts/run_ai_benchmark.py --suite mock
python scripts/run_ai_benchmark.py --suite golden --providers local
python scripts/run_ai_benchmark.py --suite release-smoke --providers available
```

O relatório contém somente metadados e métricas: benchmark id, Git SHA, versão, provider/modelo, versões de prompt/dataset, seed, ambiente e timestamps. Entradas e saídas não são persistidas.

Baselines vivem em `benchmarks/baselines/`. O local é obrigatório. Baseline externo só existe depois de chamada real bem-sucedida. Thresholds iniciais são aplicados apenas quando a fixture suporta a medição: schema validity 0,98; completion 0,90; evidence precision 0,95; unsupported claims 0,02 em golden determinístico.

Uma regressão não deve ser mascarada por métrica ausente. `--resume` reaproveita resultados identificados, e `--fail-on-regression` retorna falha quando uma métrica comparável cruza seu limite.
