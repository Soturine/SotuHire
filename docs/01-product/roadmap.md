# Roadmap

## Estratégia geral

O SotuHire deve evoluir em etapas pequenas. A regra é:

> Primeiro entregar valor manualmente. Depois automatizar coleta. Depois escalar.

Não começar por scraper complexo. O núcleo do produto é o match entre currículo e vaga.

## v0.1 - Núcleo do produto

Foco: provar que a análise CV + vaga é útil.

Entregas:

- upload de currículo PDF;
- extração de texto com PyMuPDF;
- campo para descrição de vaga;
- chamada para LLM;
- relatório inicial;
- Streamlit simples;
- tratamento básico de erro.

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

- UI não depende de texto solto;
- score aparece como métrica;
- listas aparecem organizadas;
- output inválido não quebra a aplicação.

## v0.3 - Regras de negócio

Foco: deixar critérios explícitos e testáveis.

Entregas:

- regras de senioridade;
- termos prioritários;
- termos impeditivos;
- classificação de recomendação;
- score de risco;
- testes unitários.

Critério de pronto:

- regras rodam sem IA;
- testes passam;
- alteração de regra não exige mexer na UI.

## v0.4 - QA e qualidade

Foco: mostrar engenharia.

Entregas:

- pytest;
- Ruff;
- pyproject.toml;
- GitHub Actions;
- fixtures;
- mocks para IA;
- comandos de desenvolvimento.

Critério de pronto:

- `ruff check .` passa;
- `ruff format . --check` passa;
- `pytest` passa;
- CI passa no GitHub.

## v0.5 - Persistência local

Foco: histórico.

Entregas:

- SQLite;
- salvar análises;
- listar histórico;
- filtrar por status;
- editar status;
- exportar CSV/JSON.

Critério de pronto:

- análise fica salva;
- usuário consegue ver histórico;
- dados sensíveis não são versionados.

## v0.6 - Scraping responsável

Foco: começar coleta automática controlada.

Entregas:

- interface de fontes;
- conector manual;
- conector de página pública simples;
- normalizador;
- deduplicação;
- rate limit;
- cache;
- logs;
- fixtures HTML.

Critério de pronto:

- conector roda sem login;
- não acessa área privada;
- respeita limites;
- não faz auto-apply;
- testes usam fixtures locais.

## v0.7 - Hidden Jobs Radar

Foco: identificar oportunidades em textos informais.

Entregas:

- classificador de post;
- extração de cargo/empresa/local/contato;
- score de confiança;
- match com currículo;
- mensagem sugerida para abordagem;
- salvamento no tracker.

Critério de pronto:

- texto de post colado vira oportunidade estruturada;
- falso positivo é sinalizado;
- usuário revisa antes de qualquer ação.

## v0.8 - Job Tracker

Foco: organizar busca.

Entregas:

- tabela de vagas;
- status da candidatura;
- campos de contato;
- data de aplicação;
- notas;
- filtros;
- métricas simples.

Status sugeridos:

```text
saved
analyzed
applied
interview
rejected
offer
archived
```

## v0.9 - Extensão assistiva

Foco: reduzir copiar/colar.

Entregas:

- extensão lê página aberta pelo usuário;
- envia texto ao app local;
- mostra match;
- salva no tracker;
- sem auto-apply;
- sem envio automático de mensagens.

## v1.0 - Produto apresentável

Foco: portfólio forte.

Entregas:

- README com screenshots;
- demo em vídeo/GIF;
- docs publicadas;
- CI;
- testes;
- release;
- exemplos fictícios;
- roadmap claro.

## Pós-v1

Ideias futuras:

- suporte a currículo DOCX;
- exportação de relatório PDF;
- comparação entre múltiplos currículos;
- modo local com LLM via Ollama;
- embeddings;
- ranking semântico;
- dashboard mais avançado;
- alertas por e-mail/Telegram;
- deploy opcional.
