# SotuHire

<section class="sotu-hero">
  <div class="sotu-hero__content">
    <p class="sotu-kicker">Local-first career intelligence platform</p>
    <h1>Compare currículo, vaga e evidências antes de aplicar.</h1>
    <p class="sotu-lead">
      SotuHire combina Match Engine 2.0, ATS review, Resume Tailor seguro, GitHub Analyzer,
      tracker e Application Intelligence para transformar candidatura em decisão informada.
    </p>
    <div class="sotu-actions">
      <a class="sotu-button sotu-button--primary" href="07-development/setup/">Rodar localmente</a>
      <a class="sotu-button" href="08-frontend/static-demo/">Ver demo estática</a>
      <a class="sotu-button" href="08-frontend/lovable-handoff/">Handoff frontend</a>
    </div>
  </div>
  <div class="sotu-hero__panel" aria-label="Resumo fictício de análise">
    <div class="sotu-score-row">
      <div>
        <span class="sotu-label">Match Score</span>
        <strong data-sotu-count="78">78</strong>
      </div>
      <div>
        <span class="sotu-label">Confidence</span>
        <strong>0.66</strong>
      </div>
      <div>
        <span class="sotu-label">ATS</span>
        <strong data-sotu-count="74">74</strong>
      </div>
    </div>
    <div class="sotu-mini-list">
      <span>Python evidenciado no currículo e GitHub</span>
      <span>Docker ausente: adicionar somente se for verdadeiro</span>
      <span>Cloud sem evidência: tratar como gap real</span>
    </div>
  </div>
</section>

!!! info "GitHub Pages é estático"
    Este site apresenta documentação, visão de produto e demos estáticas. Ele não roda Python,
    Streamlit, IA, Local Companion API ou backend. O app completo continua local.

## O produto em quatro passos

<div class="sotu-flow">
  <div><strong>1. Currículo</strong><span>Extrai perfil, skills, experiências e evidências.</span></div>
  <div><strong>2. Vaga</strong><span>Estrutura requisitos, domínio, senioridade e riscos.</span></div>
  <div><strong>3. Match</strong><span>Calcula score, confidence, gaps e ações seguras.</span></div>
  <div><strong>4. Tracker</strong><span>Acompanha candidaturas e padrões recorrentes.</span></div>
</div>

## Features principais

<div class="sotu-grid">
  <article>
    <h3>Match Engine 2.0</h3>
    <p>Matching por requisitos, evidências, senioridade, domínio, gaps críticos, confidence e risco.</p>
    <a href="07-development/v0.12.0-match-engine-2/">Ler detalhes</a>
  </article>
  <article>
    <h3>ATS + Resume Tailor</h3>
    <p>Keywords separadas entre presentes, seguras se verdadeiras e ausentes sem evidência.</p>
    <a href="03-business-rules/resume-tailor-rules/">Ver regras</a>
  </article>
  <article>
    <h3>GitHub Analyzer 2.0</h3>
    <p>Repositórios públicos viram evidências técnicas para portfolio, match e memória local.</p>
    <a href="07-development/v0.11.0-github-analyzer-2/">Explorar</a>
  </article>
  <article>
    <h3>Application Intelligence</h3>
    <p>Direção para métricas de Kanban, requisitos recorrentes, gaps, fontes e funil.</p>
    <a href="08-frontend/application-intelligence/">Ver contrato</a>
  </article>
  <article>
    <h3>Frontend-ready</h3>
    <p>Contratos, mocks e screen map para Lovable, React, Vite, Next.js ou outro stack moderno.</p>
    <a href="08-frontend/">Abrir handoff</a>
  </article>
  <article>
    <h3>Local-first</h3>
    <p>O fluxo principal roda localmente; IA externa é opcional e controlada pela pessoa usuária.</p>
    <a href="01-product/github-pages-site/">Pages vs app local</a>
  </article>
</div>

## Como rodar localmente

```bash
git clone https://github.com/Soturine/SotuHire.git
cd SotuHire
python -m venv .venv
pip install -r docs/requirements/requirements.txt
streamlit run app.py
```

Para recursos opcionais de IA:

```bash
pip install -r docs/requirements/requirements-ai.txt
```

## Frontend moderno futuro

<section class="sotu-band">
  <div>
    <h2>Lovable pode redesenhar tudo. O core continua mandando na lógica.</h2>
    <p>
      A v1.1.0 documenta contratos, mocks e regras para um frontend moderno futuro. O visual pode
      mudar livremente, mas matching, scoring, ATS, Tailor, GitHub Analyzer, validações fortes e
      regras anti-invenção continuam no backend/core.
    </p>
    <a class="sotu-button sotu-button--primary" href="08-frontend/api-contract/">Ver API contract</a>
  </div>
</section>

## Links úteis

- [Índice documental](documentation-index.md)
- [Roadmap](01-product/roadmap.md)
- [Demo estática v1.1](08-frontend/static-demo.md)
- [GitHub Pages vs app local](01-product/github-pages-site.md)
- [Prompt catalog](04-ai/prompt-catalog.md)
- [Release notes](https://github.com/Soturine/SotuHire/releases)
