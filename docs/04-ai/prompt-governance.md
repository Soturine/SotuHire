# Governança de prompts

Prompt de produção só existe quando registrado por `PromptSpec` e vinculado a exatamente um `AiTask`. O catálogo gerado é uma visão verificável; o código continua sendo a fonte de verdade.

## Critérios de entrada

Cada prompt precisa de identificador e versão, schema de saída, tarefa proprietária, consumidores reais, exemplos/fixtures, failure modes, política de contexto, suíte de avaliação, fallback e teste estruturado. Mudança incompatível de contrato exige nova versão.

Conteúdo de currículo, vaga, edital, README, memória e evidência é delimitado como `untrusted_content`. A system policy prevalece sobre instruções existentes nesses documentos. Saídas passam por schema guard e validação de claims proibidos.

## Promoção e regressão

1. validar schema e regras determinísticas;
2. executar golden e casos adversariais com seed fixa;
3. comparar com baseline aplicável;
4. revisar claims sem evidência e warnings;
5. executar provider externo somente por opt-in;
6. observar feedback humano sem automatizar alterações.

LLM-as-a-judge, quando usado, é tarefa separada e identificada, nunca é o único juiz e não decide release sozinho.

O catálogo inclui `evaluation_suite`, `golden_cases`, `last_benchmark`, `baseline_status` e `providers_tested`. Valide com:

```bash
python scripts/generate_prompt_catalog.py --check
```
