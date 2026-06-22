# Static demo

Esta demo é estática e usa dados fictícios baseados nos mocks em `docs/assets/mock-api/`.
Ela existe para documentação, GitHub Pages e handoff visual para Lovable.

Ela não chama backend real, não processa currículo real e não executa IA.

## Snapshot da análise

<section class="sotu-demo-grid">
  <article class="sotu-demo-card sotu-demo-card--strong">
    <span class="sotu-label">Pontuação de compatibilidade</span>
    <strong data-sotu-count="78">78</strong>
    <p>Bom alinhamento para Backend Python, com evidências em currículo e GitHub.</p>
  </article>
  <article class="sotu-demo-card">
    <span class="sotu-label">Confiança</span>
    <strong>0.66</strong>
    <p>Confiança moderada: há evidências úteis, mas gaps ainda precisam de validação.</p>
  </article>
  <article class="sotu-demo-card">
    <span class="sotu-label">ATS</span>
    <strong data-sotu-count="74">74</strong>
    <p>Keywords principais presentes; Docker e CI/CD só devem entrar se forem verdadeiros.</p>
  </article>
  <article class="sotu-demo-card">
    <span class="sotu-label">Risco</span>
    <strong data-sotu-count="18">18</strong>
    <p>Risco baixo, sem gap crítico de registro profissional neste cenário fictício.</p>
  </article>
</section>

## Evidências e gaps

| Tipo | Item | Status | Ação segura |
|---|---|---|---|
| Skill | Python | Evidenciado | Manter no currículo com contexto de projeto. |
| Skill | FastAPI | Evidenciado | Conectar ao projeto fictitious-api-lab. |
| Skill | Docker | Parcial | Adicionar somente se houver experiência real. |
| Skill | Cloud | Ausente | Tratar como gap até existir evidência verificável. |

## ATS Review

```json
{
  "present": ["Python", "FastAPI", "SQL", "Pytest", "APIs REST"],
  "missing_but_safe_to_add_if_true": ["Docker", "CI/CD"],
  "missing_without_evidence": ["Cloud", "Kubernetes"]
}
```

## Resume Tailor seguro

Sugestões permitidas neste mock:

- Desenvolveu APIs REST em Python com FastAPI, SQL e testes automatizados.
- Apoiou melhorias de qualidade com Pytest, revisão de código e monitoramento de erros.
- Manteve documentação técnica para facilitar manutenção e onboarding.

Avisos:

- Não declarar Cloud ou Kubernetes sem evidência.
- Não transformar keyword ausente em experiência real.
- Revisar manualmente cada bullet antes de usar em candidatura real.

## GitHub Evidence

<section class="sotu-demo-grid sotu-demo-grid--two">
  <article class="sotu-demo-card">
    <h3>Repo fictício</h3>
    <p><strong>example/fictitious-api-lab</strong></p>
    <p>README com instalação, testes com Pytest e estrutura de API.</p>
  </article>
  <article class="sotu-demo-card">
    <h3>Sugestões de portfolio</h3>
    <p>Adicionar screenshot, diagrama simples e seção de tradeoffs técnicos.</p>
  </article>
</section>

## Kanban

| Vaga | Fonte | Status | Compatibilidade | ATS |
|---|---:|---|---:|---:|
| Backend Developer Python | LinkedIn | applied | 78 | 74 |
| API Engineer | Gupy | interview | 84 | 79 |
| Platform Developer | Company career page | saved | 69 | 65 |

## Application Intelligence

<section class="sotu-demo-grid sotu-demo-grid--two">
  <article class="sotu-demo-card">
    <h3>Requisitos mais pedidos</h3>
    <div class="sotu-bars">
      <span style="--value: 92%">Python <b>12</b></span>
      <span style="--value: 72%">FastAPI <b>8</b></span>
      <span style="--value: 64%">Docker <b>7</b></span>
      <span style="--value: 56%">Cloud <b>6</b></span>
    </div>
  </article>
  <article class="sotu-demo-card">
    <h3>Gaps recorrentes</h3>
    <div class="sotu-bars sotu-bars--warn">
      <span style="--value: 70%">Docker <b>7</b></span>
      <span style="--value: 60%">Cloud <b>6</b></span>
    </div>
    <p>Gaps não viram experiência. Eles orientam estudo, portfolio ou revisão honesta.</p>
  </article>
</section>

## Mocks relacionados

- [`match-result.json`](../assets/mock-api/match-result.json)
- [`ats-review.json`](../assets/mock-api/ats-review.json)
- [`resume-tailor.json`](../assets/mock-api/resume-tailor.json)
- [`github-repo-analysis.json`](../assets/mock-api/github-repo-analysis.json)
- [`tracker-jobs.json`](../assets/mock-api/tracker-jobs.json)
- [`tracker-requirements.json`](../assets/mock-api/tracker-requirements.json)

## Limite da demo

Esta página é uma vitrine estática. O frontend moderno real fica em `apps/web`, o Streamlit
continua local/dev e a API local fica disponível em `apps/api`.
