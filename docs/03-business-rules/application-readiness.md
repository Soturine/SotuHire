# Regras de prontidão da candidatura

Prontidão mede cobertura verificável para preparar uma candidatura. Não prevê entrevista, contratação ou elegibilidade.

## Cálculo

Pesos-base: Currículo 10%, Formação 10%, Experiência 15%, Competências 15%, Projetos 8%, Portfólio 5%, Lattes/produção acadêmica 5%, Certificações 3,5%, Registros profissionais 3,5%, Idiomas 5%, GitHub 5% e Requisitos 15%. O score é a soma ponderada das coberturas, renormalizada somente entre dimensões aplicáveis e arredondada a uma casa.

`met`, `partial`, `missing` e `not_applicable` são derivados da cobertura. Ausência e N/A são distintos: N/A não reduz o denominador. GitHub só é aplicável quando vaga, cargo ou currículo contêm marcadores técnicos. Registros profissionais têm dimensão própria para que áreas regulamentadas não sejam avaliadas como tecnologia.

Cobertura de requisitos compara requisitos estruturados da vaga com texto habilitado do currículo. Cobertura de evidências considera entradas confirmadas ou com referência de origem. Informação ausente vira blocker/warning, nunca fato preenchido.

## Decisões humanas

- sugestão começa `pending` e pode ser aceita, editada, rejeitada ou desfeita;
- trocar mestre, vaga ou evidências invalida análise e artefatos dependentes;
- sugestão sem evidência não pode se tornar afirmação factual;
- a nota é determinística; IA, quando usada, apenas explica ou propõe texto revisável;
- uma amostra de outcomes não altera automaticamente pesos ou currículo.
