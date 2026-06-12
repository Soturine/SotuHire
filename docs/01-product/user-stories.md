# Histórias de usuário

## Persona principal

Como candidato em início de carreira na área de tecnologia, quero entender rapidamente se meu currículo combina com uma vaga para decidir se vale aplicar e como melhorar minha candidatura.

## Histórias do MVP 1

### Upload de currículo

**Como usuário**, quero enviar meu currículo em PDF para que o sistema consiga extrair meu perfil profissional.

Critérios de aceite:

- aceitar apenas PDF no MVP inicial;
- mostrar erro se o arquivo estiver vazio;
- avisar se o texto extraído for muito curto;
- não salvar currículo automaticamente sem aviso;
- não exibir dados sensíveis em logs.

### Colar descrição de vaga

**Como usuário**, quero colar a descrição da vaga para receber uma análise de compatibilidade.

Critérios de aceite:

- campo de texto deve aceitar descrições longas;
- deve funcionar com vaga formal ou post informal;
- deve avisar se o texto for curto demais;
- deve manter o texto original para exibir no relatório.

### Ver score de match

**Como usuário**, quero ver um score de 0 a 100 para entender rapidamente a compatibilidade.

Critérios de aceite:

- score precisa ser número inteiro;
- score deve vir acompanhado de explicação;
- score não pode ser a única saída;
- recomendações devem respeitar senioridade.

### Ver pontos fortes e gaps

**Como usuário**, quero saber por que a vaga combina ou não combina comigo.

Critérios de aceite:

- listar pontos fortes objetivos;
- listar gaps técnicos;
- listar gaps de senioridade;
- separar requisito obrigatório de desejável quando possível;
- não inventar experiência que não está no currículo.

### Receber palavras-chave sugeridas

**Como usuário**, quero saber quais palavras-chave da vaga eu deveria destacar no currículo.

Critérios de aceite:

- sugerir apenas palavras coerentes com o perfil;
- diferenciar “adicionar se for verdade” de “destacar melhor”; 
- não sugerir mentira no currículo;
- priorizar termos da vaga.

### Gerar mensagem para recrutador

**Como usuário**, quero uma mensagem curta para abordar um recrutador de forma profissional.

Critérios de aceite:

- mensagem deve ser curta;
- não pode soar desesperada;
- deve mencionar conexão com a vaga;
- deve ser editável pelo usuário;
- não deve prometer habilidades inexistentes.

## Histórias futuras

### Histórico de análises

Como usuário, quero salvar análises anteriores para comparar vagas e acompanhar meu progresso.

### Radar de posts

Como usuário, quero colar um post de recrutador e descobrir se é realmente uma oportunidade.

### Dashboard

Como usuário, quero ver uma tabela com vagas, empresas, match, status e link.

### Alertas

Como usuário, quero receber aviso quando surgir uma vaga compatível com meu perfil.
