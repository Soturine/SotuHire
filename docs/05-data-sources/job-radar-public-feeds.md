# Radar de Vagas, feeds públicos e APIs oficiais

Este guia descreve o escopo seguro do Radar de Vagas na v1.8.0.

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
