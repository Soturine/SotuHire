# Defesa contra prompt injection

Currículos, vagas, editais, README, memória e qualquer texto importado são dados não confiáveis. Frases como “ignore as instruções anteriores”, “envie a API key”, “revele o prompt” ou “marque tudo como atendido” nunca são instruções válidas para o runtime.

A defesa combina:

- delimitadores explícitos de conteúdo não confiável;
- system policy comum anexada aos prompts;
- schema estruturado e parser estrito;
- validação determinística de claims proibidos/sem evidência;
- sanitização de erros e traces;
- fixtures adversariais para vaga, edital, README e currículo.

Detecção de uma frase suspeita é sinal para revisão, não prova suficiente de ataque. Mesmo sem detectar padrões textuais, a saída continua sujeita a schema, evidência e limites de produto. Nenhum fluxo tem acesso à chave como conteúdo de prompt.
