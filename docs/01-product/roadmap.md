# Roadmap

## v0.1 - Núcleo do produto

Foco: provar que a análise CV + vaga é útil.

Entregas:

- upload de currículo PDF;
- extração de texto com PyMuPDF;
- campo para descrição de vaga;
- chamada para LLM;
- relatório textual inicial;
- README e docs básicos.

Critério de pronto:

- usuário consegue rodar localmente;
- currículo e vaga geram relatório;
- erros básicos são tratados.

## v0.2 - Saída estruturada

Foco: transformar o relatório em dados confiáveis.

Entregas:

- schema Pydantic;
- JSON com score, recomendação, listas e mensagem;
- validação de resposta;
- UI com componentes Streamlit;
- fallback para resposta inválida.

Critério de pronto:

- a UI não depende de texto solto;
- score aparece como métrica;
- listas aparecem organizadas.

## v0.3 - Regras de negócio

Foco: deixar critérios explícitos e testáveis.

Entregas:

- regras de senioridade;
- termos de prioridade;
- termos de desclassificação;
- classificação de recomendação;
- testes unitários.

Critério de pronto:

- regras rodam sem IA;
- testes passam;
- alteração de regra não exige mexer na UI.

## v0.4 - QA e refatoração

Foco: qualidade de código.

Entregas:

- `pytest`;
- `ruff`;
- funções menores;
- mocks para IA;
- README de desenvolvimento.

Critério de pronto:

- testes cobrem lógica principal;
- lint não mostra erros graves;
- código está separado por responsabilidade.

## v0.5 - Persistência local

Foco: histórico.

Entregas:

- SQLite;
- salvar análises;
- listar histórico;
- filtrar por score e recomendação;
- exportar relatório.

## v0.6 - Buscador de vagas públicas

Foco: encontrar vagas sem depender de processos manuais.

Entregas:

- fontes públicas configuráveis;
- deduplicação;
- normalização de campos;
- match em lote;
- dashboard.

## v0.7 - Hidden Jobs Radar

Foco: oportunidades em posts e indicações.

Entregas:

- classificador de post;
- extração de contato/link;
- match com currículo;
- mensagem de abordagem;
- status “post informal”.

## v0.8 - Extensão de navegador

Foco: analisar páginas abertas pelo usuário.

Entregas:

- extensão simples;
- leitura do texto visível;
- envio para backend local;
- retorno do relatório.

## v1.0 - Versão demonstrável de portfólio

Foco: projeto apresentável.

Entregas:

- documentação completa;
- testes;
- demo;
- screenshots;
- exemplos sem dados pessoais;
- instruções de instalação;
- limitações claras.
