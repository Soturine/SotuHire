# SotuHire

> Assistente inteligente de carreira para análise de currículo, compatibilidade com vagas, otimização ATS, radar de oportunidades, coleta controlada de vagas e apoio à candidatura — **sem candidatura automática em massa**.

O **SotuHire** é um projeto de portfólio focado em **IA aplicada, NLP, scraping responsável, engenharia de software, regras de negócio, QA, Clean Code e produto real**.

A ideia é ajudar uma pessoa candidata a responder uma pergunta simples, mas difícil na prática:

> “Essa vaga vale meu tempo? Meu currículo combina? O que eu preciso ajustar antes de aplicar?”

O projeto começou como um “achador de vagas”, mas o escopo correto é maior: um **copiloto de carreira**. Ele pode receber currículo, analisar vagas formais, interpretar posts de recrutadores, ranquear oportunidades, explicar aderência e preparar materiais de candidatura para revisão humana.

## O que o SotuHire faz

O sistema deve evoluir em módulos:

1. **Resume Parser**  
   Lê currículo em PDF/DOCX e extrai texto, seções, skills, experiências, formação, projetos e links. Também deve evoluir para lidar com currículo ATS, Currículo Lattes, LinkedIn, GitHub e portfólio como fontes diferentes de perfil profissional.

2. **ATS Analyzer**  
   Avalia se o currículo está legível para sistemas ATS e aponta problemas como formatação excessiva, seções fracas, falta de palavras-chave e baixa clareza.

3. **Job Matcher**  
   Compara o currículo com uma descrição de vaga e calcula:
   - Match Score;
   - ATS Score;
   - Seniority Fit;
   - Risk Score;
   - recomendação final.

4. **Business Rules Engine**  
   Aplica regras determinísticas antes da IA, como bloqueio de vagas sênior, detecção de termos críticos, priorização de estágio/júnior e filtros por localidade/modalidade.

5. **Application Assistant**  
   Gera mensagem curta para recrutador, resposta para formulário, carta curta e sugestões de ajuste no currículo.

6. **Job Tracker**  
   Salva oportunidades analisadas e acompanha status: salva, analisada, aplicada, entrevista, rejeitada, oferta.

7. **Scraping & Source Connectors**  
   Coleta oportunidades em fontes permitidas e públicas, respeitando limites técnicos, termos de uso, `robots.txt`, rate limit e privacidade.

8. **Hidden Jobs Radar**  
   Detecta vagas escondidas em textos informais, como posts públicos, newsletters, páginas de carreira, comunidades e mensagens copiadas pelo usuário.

## O que o SotuHire NÃO deve ser

O SotuHire **não** deve virar um robô agressivo de candidatura.

Não é objetivo:

- aplicar automaticamente em massa;
- enviar currículo sem revisão humana;
- fazer login em contas do usuário para contornar limites;
- burlar CAPTCHA, paywall, autenticação ou bloqueios;
- extrair dados pessoais em massa;
- simular comportamento humano para driblar plataformas;
- gerar spam para recrutadores.

O objetivo é:

> encontrar, organizar, analisar, explicar, preparar e deixar o usuário decidir.


## Currículo ATS, Lattes e perfis profissionais

O SotuHire deve tratar fontes de perfil de forma separada:

- **currículo ATS** para candidaturas corporativas e plataformas de vagas;
- **Currículo Lattes** para histórico acadêmico, pesquisa, iniciação científica, publicações e projetos;
- **LinkedIn** para narrativa profissional e networking;
- **GitHub** para evidência técnica;
- **portfólio** para apresentação visual e contexto dos projetos.

O objetivo não é usar tudo diretamente no currículo final. O sistema deve converter essas fontes em um `CandidateProfile` estruturado e recomendar o que destacar conforme a vaga.

## Fluxo principal do MVP

```text
1. Usuário envia currículo
2. Usuário cola descrição da vaga ou texto de post
3. Sistema extrai texto do currículo
4. Sistema normaliza a vaga
5. Regras determinísticas identificam riscos
6. IA gera análise estruturada em JSON
7. UI mostra score, recomendação, gaps e mensagens
8. Usuário revisa e decide se aplica
```

## MVPs

### v0.1 — Análise manual de currículo + vaga

- Upload de currículo PDF;
- colagem manual da descrição da vaga;
- extração de texto com PyMuPDF;
- chamada para LLM;
- relatório estruturado;
- interface Streamlit.

### v0.2 — JSON estruturado e UI melhor

- Pydantic schemas;
- validação de resposta da IA;
- `st.metric`, `st.progress`, cards e tabelas;
- fallback para resposta inválida;
- separação entre Match Score, ATS Score e Risk Score.

### v0.3 — Regras de negócio

- detecção de senioridade;
- termos impeditivos;
- termos prioritários;
- filtros por modalidade/localidade;
- testes unitários.

### v0.4 — QA e qualidade de código

- `pytest`;
- `ruff check`;
- `ruff format`;
- GitHub Actions;
- fixtures de teste;
- mocks para IA.

### v0.5 — Persistência local

- SQLite;
- histórico de análises;
- status da candidatura;
- filtros e exportação.

### v0.6 — Scraping responsável

- conectores para fontes públicas;
- normalização de vagas;
- deduplicação;
- rate limit;
- respeito a `robots.txt`;
- logs de origem.

### v0.7 — Hidden Jobs Radar

- análise de posts copiados manualmente;
- classificação de textos como oportunidade real ou não;
- extração de cargo, empresa, local, contato e requisitos;
- priorização de oportunidades informais.

### v0.8 — Extensão assistiva

- extensão de navegador para enviar a vaga aberta ao SotuHire;
- sem auto-apply;
- sem scraping autenticado em massa;
- apenas leitura assistida do conteúdo que o usuário já abriu.


## Portais brasileiros e fontes planejadas

Além de fontes globais como Greenhouse, Lever e Ashby, o SotuHire deve mapear fontes brasileiras importantes:

- LinkedIn;
- Gupy;
- InfoJobs;
- Indeed Brasil;
- CIEE;
- Companhia de Estágios;
- InHire;
- Vagas.com;
- Catho;
- Cia de Talentos;
- Nube;
- 99jobs;
- Eureca;
- Trabalha Brasil;
- BNE;
- Remotar;
- Programathor;
- páginas públicas de empresas;
- newsletters e comunidades com entrada manual.

Cada fonte deve ter política própria: algumas começam como entrada manual, algumas podem virar conectores públicos e outras devem permanecer apenas assistivas por exigirem login ou apresentarem risco de automação indevida.

## Stack inicial

- Python;
- Streamlit;
- PyMuPDF;
- Pydantic;
- Google Gemini API ou outro LLM;
- SQLite;
- pytest;
- Ruff;
- Requests/HTTPX + BeautifulSoup para páginas públicas simples;
- Playwright somente quando renderização dinâmica for realmente necessária;
- Scrapy somente quando o projeto precisar de crawlers mais estruturados.

## Qualidade

O projeto deve seguir:

- Clean Code;
- SOLID sem exagero;
- regras de negócio explícitas;
- testes para lógica determinística;
- validação de schema;
- lint e format com Ruff;
- separação entre UI, domínio, IA e fontes de dados;
- simplicidade no MVP;
- evolução incremental.

## Estrutura de documentação

```text
docs/
├── 00-audit/
├── 01-product/
├── 02-architecture/
├── 03-business-rules/
├── 04-ai/
├── 05-data-sources/
├── 06-engineering/
├── 07-development/
└── 08-benchmark/
```

## Comandos principais

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Qualidade:

```bash
ruff check .
ruff format .
pytest
```

Documentação:

```bash
mkdocs serve
```

## Posicionamento

O diferencial do SotuHire é ser um projeto de **engenharia aplicada a carreira**, não apenas um prompt em uma tela.

Ele junta:

- IA generativa;
- NLP;
- ATS;
- matching semântico;
- scraping responsável;
- regras de negócio;
- dashboard;
- QA;
- privacidade;
- explicabilidade.

## Status

Projeto em fase inicial de documentação e preparação do MVP.

Próximo passo recomendado:

```text
feat: add initial resume job match MVP
```

---

## Expansão planejada: SotuHire como copiloto completo de carreira

A visão atual do SotuHire foi ampliada para ir além de currículo + vaga. O projeto passa a ser documentado como um **copiloto completo de carreira para tecnologia**, com módulos independentes e evolutivos:

- **Resume Analyzer**: leitura de currículo ATS, currículo tradicional e Currículo Lattes.
- **Job Match Engine**: comparação entre perfil e vaga.
- **Search Intelligence**: geração de queries inteligentes para Google/Bing/DuckDuckGo e buscas por domínio.
- **Hidden Jobs Radar**: detecção de oportunidades em posts e textos informais.
- **Responsible Scraping**: coleta pública, limitada, com cache, rate limit e respeito a regras de fonte.
- **Job Tracker / Kanban**: histórico de candidaturas, follow-up e métricas.
- **Profile Score Engine**: LinkedIn Score, ATS Score, Portfolio Score, Lattes Score e Readiness Score.
- **GitHub/Portfolio Analyzer**: análise de GitHub, GitLab, Kaggle, Hugging Face, npm, PyPI, portfólios e demos.
- **RAG Memory**: memória de carreira para recuperar evidências relevantes do usuário.
- **Browser Extension Assistant**: extensão assistiva para analisar página aberta com confirmação humana.
- **Alert Engine**: alertas de vagas relevantes via UI, e futuramente Telegram/e-mail.

### Novos docs importantes

- [Rotina Inteligente de Busca](docs/01-product/job-search-routine.md)
- [Search Intelligence](docs/05-data-sources/search-intelligence.md)
- [Fontes Alternativas de Vagas](docs/05-data-sources/alternative-job-boards.md)
- [Social Post Discovery](docs/05-data-sources/social-post-discovery.md)
- [RAG e Memória de Carreira](docs/04-ai/rag-memory-architecture.md)
- [Provider Strategy](docs/04-ai/provider-strategy.md)
- [Profile Score](docs/03-business-rules/profile-score.md)
- [GitHub/Portfolio Analyzer](docs/05-data-sources/github-portfolio-analyzer.md)
- [Job Tracker Kanban](docs/07-development/job-tracker-kanban.md)
- [Follow-up Assistant](docs/07-development/follow-up-assistant.md)
- [Alerts Roadmap](docs/07-development/alerts-roadmap.md)
- [Browser Extension Roadmap](docs/07-development/browser-extension-roadmap.md)
- [Reference Projects](docs/08-benchmark/reference-projects.md)

### Inspiração nos outros projetos Soturine

O SotuHire pode aproveitar princípios usados em projetos como SoturAI e SotuRail:

- raciocínio adaptativo;
- análise baseada em sinais;
- histórico e feedback loop;
- documentação forte;
- módulos isolados;
- cuidado com overengineering;
- qualidade de código com Ruff, testes e CI;
- visão de produto, não apenas script.

No SotuHire, isso se traduz em um sistema que observa vagas, posts, currículos, portfólio e histórico para sugerir ações melhores, sempre com revisão humana.
