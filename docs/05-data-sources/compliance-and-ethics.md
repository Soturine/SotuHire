# Compliance e ética

## Por que este documento existe

Ferramentas de busca de vagas podem facilmente virar bots agressivos. O SotuHire deve ser construído como projeto profissional, com limites claros.

## Princípio central

> O SotuHire ajuda o usuário a decidir e preparar candidaturas. Ele não deve remover o controle humano nem violar regras de plataformas.

## Candidatura automática

Não recomendado:

- aplicar em massa;
- enviar currículo sem revisão;
- personalizar respostas automaticamente sem o usuário olhar;
- usar conta do usuário para clicar em botões em larga escala;
- simular comportamento humano para driblar bloqueios.

Recomendado:

- preparar texto;
- sugerir ajustes;
- ranquear vagas;
- registrar status;
- deixar o usuário aplicar manualmente.

## LinkedIn e plataformas similares

A documentação oficial do LinkedIn deve ser considerada antes de qualquer integração. O contrato de usuário do LinkedIn menciona limites de uso, responsabilidade do usuário, disponibilidade do serviço, restrições e possibilidade de limitação/suspensão por uso indevido.

Referência: [LinkedIn User Agreement](https://www.linkedin.com/legal/user-agreement)

## Scraping

Scraping pode ser útil em contexto controlado, mas exige cuidado.

Não fazer:

- burlar login;
- burlar captcha;
- ignorar bloqueios;
- usar proxies para contornar rate limit;
- coletar dados pessoais em massa;
- copiar bases inteiras;
- violar termos de uso.

Preferir:

- APIs oficiais;
- feeds públicos;
- páginas públicas simples;
- entrada manual;
- exportações feitas pelo próprio usuário;
- links de vagas fornecidos pelo usuário.

## Privacidade

Currículo contém dados pessoais. O projeto deve evitar:

- salvar currículo real no GitHub;
- logar texto completo do currículo;
- expor e-mail/telefone em exemplos;
- enviar dados para múltiplas APIs sem necessidade;
- manter arquivos enviados sem aviso.

## Transparência

A UI deve deixar claro:

- IA pode errar;
- score é estimativa;
- usuário deve revisar textos;
- candidatura final é responsabilidade do usuário.
