# Importadores e fontes publicas seguras

Este documento descreve o escopo seguro para entrada de vagas a partir da v1.7.0 e o polimento da
v1.7.1. Ele complementa os guias de fontes de dados sem alterar regras protegidas de compliance ou
navegador autenticado.

## O que existe na v1.8.2

- Perfil Profissional Universal usado como contexto local para classificar capturas futuras;
- endpoint `POST /api/v1/sources/authenticated-captures`;
- captura assistida autenticada iniciada pelo usuário;
- aceite de texto visível ou selecionado na página atual;
- gravação na Caixa de Entrada para revisão;
- sinais locais de perfil, como itens confirmados encontrados e possíveis gaps;
- bloqueio de metadata com cookie, token, sessão, headers ou segredos.

Esse fluxo não altera a lógica sensível de authenticated browser/Chromium/CDP. Ele não automatiza
login, não burla CAPTCHA, não faz auto-apply, não navega em massa e não salva candidatura final sem
ação explícita da pessoa.

## O que existe na v1.8.0

- tela **Radar de Vagas** no frontend moderno;
- wishlists locais para cargos, skills, locais e preferências;
- fontes RSS/Atom públicas com refresh manual;
- resultados do Radar com score local, evidências, lacunas e próximas ações;
- alertas locais para oportunidades relevantes;
- ações para salvar resultado na Caixa de Entrada ou em Candidaturas;
- estrutura de adapters para APIs oficiais documentadas.

## O que existe na v1.7.1

- upload real de CSV/JSON pelo navegador;
- preview antes de confirmar a importacao;
- textarea CSV/JSON mantido como alternativa;
- mescla visual de duplicatas preservando historico;
- exportacao local da Caixa de Entrada em CSV/JSON;
- Diretório de Fontes para paginas abertas, feeds publicos, APIs oficiais, CSV/JSON recorrente e
  links manuais;
- IA opcional para enriquecimento de importacoes, sempre com fallback local.

## O que existe na v1.7.0

- importacao manual por texto;
- importacao de uma URL publica especifica;
- importacao CSV;
- importacao JSON;
- historico local de capturas/importacoes;
- deduplicacao local explicavel;
- Caixa de Entrada de Oportunidades;
- conexao com Vaga, Analise de Compatibilidade e Candidaturas/Kanban.

## O que nao existe

- crawler amplo;
- busca massiva;
- login automatico;
- coleta de cookies/tokens;
- bypass de CAPTCHA;
- auto-apply;
- automacao de conta em plataformas de terceiros.

Feeds RSS públicos agora têm refresh manual pela tela **Radar de Vagas**. APIs oficiais continuam
como estrutura preparada: um conector real depende de contrato/documentação oficial e revisão
manual antes de salvar qualquer oportunidade.

Se uma pagina exige login, bloqueia leitura publica simples ou nao permite extrair texto, o SotuHire
deve orientar a pessoa a abrir a pagina manualmente e colar o texto da vaga.

## Formato CSV

```csv
cargo,empresa,link,local,descricao,fonte,status,observacoes
Analista de Dados,Empresa Exemplo,https://example.com/jobs/123,Remoto,"Python, SQL e dashboards",CSV Manual,nova,"vaga ficticia"
Desenvolvedor Backend,Tech Exemplo,https://example.com/jobs/456,Hibrido,"APIs, testes e bancos de dados",CSV Manual,nova,"vaga ficticia"
```

Campos tambem aceitos em ingles:

```txt
title, company, url, location, description, source, status, notes
```

## Formato JSON

```json
[
  {
    "cargo": "Analista de Dados",
    "empresa": "Empresa Exemplo",
    "link": "https://example.com/jobs/123",
    "local": "Remoto",
    "descricao": "Python, SQL e dashboards.",
    "fonte": "JSON Manual",
    "status": "nova",
    "observacoes": "vaga ficticia"
  }
]
```

## Deduplicacao

Critérios usados:

- URL normalizada;
- empresa + cargo;
- empresa + cargo + localidade;
- texto normalizado da descricao.

O sistema marca `possible_duplicate` e mantem o historico. Na v1.7.1, a pessoa pode:

- mesclar preservando fonte, link, notas e rastro local;
- manter separado;
- arquivar o item novo;
- marcar como nao duplicata.

A mescla nao apaga a fonte original nem remove o item existente.

## Exportacao

A Caixa de Entrada pode exportar:

- todos os itens;
- itens filtrados;
- itens selecionados.

Formatos:

```txt
CSV
JSON
```

Campos minimos:

```txt
cargo, empresa, link, origem, status, data, score, ats_score, tags, notas
```

## IA opcional em importacoes

Quando `use_ai=true` e o provider esta configurado, o backend pode tentar enriquecer:

- tags;
- dominio;
- senioridade provavel;
- prioridade;
- resumo curto;
- explicacao de duplicata;
- alertas de inconsistencia.

Se a IA falhar, a importacao continua localmente. A IA nao deve inventar requisitos, experiencia,
formacao, certificacao, salario, licenca, empresa ou status de candidatura.

## Radar de Vagas v1.8.0

O Radar não faz busca ampla na web. Ele roda somente em fontes configuradas pelo usuário:

- RSS/Atom público;
- página pública simples quando permitida;
- API oficial planejada/documentada;
- entradas manuais já existentes.

O resultado fica em revisão. O usuário decide se salva na Caixa de Entrada, envia para análise ou
salva em Candidaturas.

## Fontes publicas planejadas

Cards no frontend mostram como roadmap:

- paginas de carreira abertas;
- APIs oficiais;
- feeds publicos recorrentes/agendados;
- CSV/JSON recorrente.

Esses itens sao exibidos como futuro/experimental e requerem revisao manual antes de qualquer
automacao recorrente.

## APIs oficiais e integracoes futuras

Conectores futuros devem usar somente APIs oficiais/documentadas, respeitar termos, exigir chave do
usuario quando aplicavel e manter revisao manual antes de salvar/analisar oportunidades. Nao ha
candidatura automatica.
