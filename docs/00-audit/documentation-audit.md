# Auditoria da documentação

## Contexto

A primeira versão da documentação do SotuHire foi criada rápido demais e ficou com problemas claros: arquivos curtos, seções interrompidas e trechos truncados. A auditoria deste documento registra o que estava errado e como a documentação foi reconstruída.

## Problemas encontrados

| Arquivo antigo | Problema encontrado | Ação tomada |
|---|---|---|
| `README.md` | Terminava no meio da frase: `Avoid over` | Reescrito como página principal completa, com visão, escopo, princípios e índice |
| `CONTRIBUTING.md` | Terminava no meio da frase: `Make a` | Reescrito com workflow, padrão de PR, testes e qualidade |
| `docs/ARCHITECTURE.md` | Terminava no meio de árvore de pastas | Substituído por `docs/02-architecture/` com vários documentos |
| `docs/BUSINESS_RULES.md` | Terminava no meio de uma tabela | Substituído por `docs/03-business-rules/` |
| `docs/PROJECT_OVERVIEW.md` | Terminava no meio da seção de objetivos | Substituído por `docs/01-product/vision.md` |
| `docs/QUALITY.md` | Terminava logo após uma pergunta | Substituído por `docs/06-engineering/qa-testing.md` e docs relacionados |
| `docs/ROADMAP.md` | Terminava no meio da v0.2 | Substituído por roadmap completo por versões |

## Decisão de reestruturação

Em vez de manter cinco documentos genéricos e curtos, a documentação foi dividida por assunto:

- produto;
- arquitetura;
- regras de negócio;
- IA;
- fontes de vagas;
- engenharia;
- desenvolvimento.

Isso evita que o README vire um arquivo enorme e melhora a navegação no GitHub.

## Critérios da nova documentação

A nova documentação segue estes critérios:

1. explicar o produto de forma completa;
2. deixar claro o que entra no MVP e o que fica para depois;
3. documentar as regras de negócio em linguagem simples;
4. registrar decisões técnicas e por que elas existem;
5. falar explicitamente sobre Clean Code, SOLID, QA e overengineering;
6. incluir links para documentação oficial quando houver dependências técnicas;
7. separar riscos de scraping, automação e candidatura automática;
8. tornar o projeto apresentável em entrevista.

## Resumo da conversa incorporado nos docs

A documentação incorporou as principais decisões discutidas:

- o nome principal escolhido é **SotuHire**;
- o projeto é um **copiloto inteligente de carreira**, não um bot de spam;
- o primeiro MVP deve ser currículo + descrição de vaga colada;
- a resposta da IA deve ser estruturada em JSON;
- a arquitetura deve ser simples, modular e testável;
- regras de negócio devem ficar explícitas;
- LinkedIn e outras plataformas devem ser tratadas com cuidado;
- o Radar de Vagas Escondidas é um diferencial futuro;
- o projeto deve servir como portfólio de IA, automação, dados, QA e engenharia de software.

## Resultado esperado

Depois da reconstrução, o repositório deve ter documentação suficiente para alguém entender:

- o problema;
- o produto;
- o MVP;
- a arquitetura;
- as regras de negócio;
- a estratégia de IA;
- os limites éticos/técnicos;
- como contribuir;
- como testar;
- como evoluir o projeto.
