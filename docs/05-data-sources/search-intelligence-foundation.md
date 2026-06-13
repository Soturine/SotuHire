# Search Intelligence Foundation

## Escopo da v0.6.0

A primeira implementação transforma um perfil de busca em uma estratégia revisável. Ela recebe cargo alvo, skills, localização, modalidade, senioridade, empresas alvo e tipo de contrato.

O resultado inclui:

- queries gerais e por domínio;
- cargos alternativos;
- fontes recomendadas;
- plano semanal;
- alertas manuais;
- riscos de buscas genéricas.

## Arquitetura

```text
modules/search_intelligence/
├── __init__.py
├── query_builder.py
├── source_plan.py
├── hidden_jobs_radar.py
└── schemas.py
```

`query_builder.py` combina os sinais mais relevantes sem criar dezenas de variações redundantes. `source_plan.py` organiza fontes e frequência. Os schemas mantêm a saída explícita e testável.

## Limite de segurança

Na v0.6.0, Search Intelligence:

- não acessa portais;
- não faz scraping;
- não usa login ou sessão da pessoa usuária;
- não envia candidaturas ou mensagens;
- não coleta dados pessoais de terceiros.

O campo `scraping_performed` permanece `false`. A UI informa que esta etapa gera somente estratégia e termos de busca.

## Uso no modo avançado

A aba **Search Intelligence** usa dados já detectados no currículo e na vaga para montar um plano inicial. A pessoa usuária pode copiar queries, escolher fontes e executar as buscas manualmente.

Essa fundação permite adicionar conectores públicos no futuro sem misturar descoberta responsável com automação agressiva.

## Evolução acionável na v0.7.0

Search Intelligence mantém queries, cargos alternativos e plano semanal, mas agora cada fonte sugerida oferece ações para:

- salvar a fonte localmente;
- testar a fonte pública;
- coletar oportunidades;
- abrir uma oportunidade coletada na análise.

A geração da estratégia continua sem rede. A coleta é uma etapa explícita, separada e rastreável, executada somente quando a pessoa usuária escolhe uma fonte.
