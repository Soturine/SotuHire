# Outcome Learning

Outcome Learning associa recomendações a eventos manuais do Tracker sem afirmar causalidade. Eventos suportados: candidatura criada/enviada manualmente, resposta, entrevista agendada/concluída, oferta, rejeição, desistência e ausência de resposta.

São derivados `response_rate`, `interview_rate`, `offer_rate`, tempo até resposta, tempo em estágio, efetividade por fonte/variante e associação de Match/ATS com outcome. Todo resultado mostra `n`:

- menos de 5: confiança insuficiente;
- de 5 a 19: sinal indicativo;
- 20 ou mais: comparação possível.

Exemplo de linguagem correta: “3 de 8 candidaturas com esta variante receberam resposta. Amostra pequena; use como sinal exploratório.”

Os sinais não alteram Perfil, pesos, currículo ou estratégia automaticamente. Atributos sensíveis desnecessários não são armazenados. Eventos podem ser consultados por candidatura, e o resumo global deixa explícito que correlação não implica causalidade.
