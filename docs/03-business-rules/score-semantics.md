# Semântica dos scores

Os scores não são aliases. Match mede requisitos satisfeitos; coverage mede quanto do conjunto
avaliável possui evidência; confidence mede qualidade/estado das evidências; ATS mede presença
e sustentação de termos; readiness mede bloqueios práticos; risk permanece separado.

`unknown` não entra como falha nem como sucesso no denominador. `not_applicable` também é
excluído. Obrigatórios e desejáveis usam pesos distintos; o resultado inclui numerador,
denominador, estados por requisito e warnings. Arredondamento ocorre somente na apresentação.

Uma evidência `sourced` ou `candidate` pode aumentar informação disponível, mas não é tratada
como fato confirmado. Requisitos regulatórios sem comprovação ficam `unknown`/bloqueados e nunca
são inferidos de cargo, curso ou texto parecido.
