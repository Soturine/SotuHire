# Regra de negócio: matching por domínio

- O mesmo conjunto de fatos, mesma política e mesma versão sempre produz o mesmo score.
- Um atributo irrelevante ou dimensão não aplicável não altera o score.
- Ausência de evidência aplicável gera lacuna explícita; não autoriza inferência.
- Mudança de domínio altera pesos/aplicabilidade, nunca o conteúdo das evidências.
- Score é apoio à decisão, não elegibilidade, ranking de pessoas ou decisão de contratação.
- Breakdown deve exibir domínio, versão da política, peso, contribuição e referências usadas.

Testes contrafactuais cobrem, entre outros, healthcare sem influência de portfolio irrelevante e
invariância a atributos fora da política.

