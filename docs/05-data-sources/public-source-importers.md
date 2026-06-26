# Importadores e fontes publicas seguras

Este documento descreve o escopo seguro para entrada de vagas a partir da v1.7.0 e o polimento da
v1.7.1. Ele complementa os guias de fontes de dados sem alterar regras protegidas de compliance ou
navegador autenticado.

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

Feeds RSS e APIs oficiais aparecem como preparacao segura. A v1.7.1 nao implementa refresh
recorrente de feeds nem conectores de APIs oficiais.

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

## Fontes publicas planejadas

Cards no frontend mostram como roadmap:

- paginas de carreira abertas;
- APIs oficiais;
- feeds publicos;
- CSV/JSON recorrente.

Esses itens sao exibidos como futuro/experimental e requerem revisao manual antes de qualquer
automacao recorrente.

## APIs oficiais e integracoes futuras

Conectores futuros devem usar somente APIs oficiais/documentadas, respeitar termos, exigir chave do
usuario quando aplicavel e manter revisao manual antes de salvar/analisar oportunidades. Nao ha
candidatura automatica.
