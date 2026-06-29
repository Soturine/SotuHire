# Radar de Vagas, feeds públicos e APIs oficiais

Este guia descreve o escopo seguro do Radar de Vagas a partir da v1.8.1.

## O que o Radar faz

- cadastra wishlists locais;
- cadastra fontes configuradas pelo usuário;
- lê RSS/Atom público em rodada manual;
- tenta leitura simples de página pública quando permitido;
- prepara cadastro de APIs oficiais;
- normaliza oportunidades;
- deduplica resultados;
- compara com wishlist e currículo;
- gera alertas locais;
- permite salvar manualmente na Caixa de Entrada ou no Tracker.
- cria rascunhos de wishlist a partir de texto livre, com revisão humana obrigatória.

## O que o Radar não faz

- scraping de Google, Bing ou SERP;
- crawler amplo sem lista explícita de fontes;
- login automático;
- bypass de CAPTCHA;
- captura de cookie, token ou sessão;
- candidatura automática;
- controle de conta de terceiros.

## RSS/Atom público

O usuário informa a URL do feed. A rodada manual do Radar:

1. busca o feed com timeout e limite de tamanho;
2. lê itens RSS/Atom;
3. cria resultados para revisão;
4. calcula score local;
5. gera alertas quando o score passa do mínimo da wishlist.

Nada é salvo em Candidaturas sem clique explícito.

## Wishlist com IA/local

Na v1.8.1, a tela `/radar` inclui **Criar wishlist com IA**. O fluxo:

1. a pessoa descreve o que procura em texto livre;
2. o backend cria um rascunho local ou usa IA opcional quando `allow_radar=true`;
3. a resposta mostra suposições, perguntas, warnings, confiança e modo `IA`, `Local` ou `Fallback`;
4. o formulário é preenchido para edição;
5. a wishlist só é salva se a pessoa confirmar manualmente.

O fallback local é multiárea. Ele não assume que a pessoa é de TI, tem GitHub, busca CLT, possui
diploma, experiência formal, conselho profissional ou registro técnico.

O prompt `job_wishlist_builder_v1` não pode inventar formação, experiência, certificação, registro,
licença, salário, empresa ou requisito. Ele retorna JSON validado e sempre marca
`needs_user_review=true`.

## APIs oficiais

APIs oficiais ficam como estrutura preparada. Um conector real só deve existir quando houver:

- documentação pública/oficial;
- termos compatíveis;
- autenticação clara quando necessária;
- chave armazenada apenas no backend local;
- revisão manual antes de salvar/analisar vagas.

## Página pública manual

Páginas públicas simples podem ser testadas como fonte pontual. Se a página exigir login, bloquear
acesso ou não entregar texto legível, o SotuHire deve orientar a pessoa a usar texto/link/CSV/JSON
manual na Caixa de Entrada.

## Histórico local

Cada rodada registra:

- fontes consultadas;
- quantidade encontrada;
- duplicatas;
- alertas;
- erros de fonte;
- duração;
- warnings.

Esses dados ficam no store local do projeto.
