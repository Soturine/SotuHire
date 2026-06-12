# QA e testes

## Objetivo

QA no SotuHire não é burocracia. É o que mostra que o projeto não é só “um prompt com Streamlit”.

O foco inicial deve ser testar:

- regras determinísticas;
- schemas;
- parsers;
- normalizadores;
- tratamento de entradas;
- deduplicação;
- conectores com fixtures locais.

## Ferramentas

- `pytest` para testes;
- `ruff` para lint e format;
- `pydantic` para validar schemas;
- mocks para chamadas de IA;
- fixtures para currículos, vagas e HTML;
- GitHub Actions para CI.

## Pirâmide de testes

### Unitários

Testam funções puras.

Exemplos:

- detectar vaga sênior;
- classificar recomendação;
- normalizar modalidade;
- calcular risco;
- deduplicar vagas.

### Integração local

Testam módulos juntos, mas sem internet.

Exemplos:

- parser de currículo com fixture;
- parser de HTML salvo;
- normalizador de vaga;
- schema Pydantic.

### Manuais

Testam o fluxo real no Streamlit.

Exemplos:

- upload PDF;
- colar vaga;
- analisar;
- salvar resultado.

### E2E futuro

Somente quando houver UI mais estável ou extensão.

Pode usar Playwright, mas não é necessário no MVP inicial.

## Testes que não devem depender de API real

Evite chamar Gemini/OpenAI em testes automáticos.

Motivos:

- custo;
- lentidão;
- instabilidade;
- necessidade de internet;
- necessidade de API key;
- output variável.

Use resposta fake.

## Testes de IA

Teste:

- se o prompt foi montado com campos esperados;
- se o JSON fake valida no schema;
- se resposta inválida gera fallback;
- se score fora de faixa é rejeitado.

## Testes de scraping

Não bater em sites reais no CI.

Use fixtures:

```text
tests/fixtures/sources/
├── company_page_sample.html
├── greenhouse_sample.html
├── lever_sample.html
└── hidden_post_sample.txt
```

Testes:

- extrai título;
- extrai empresa;
- extrai local;
- extrai descrição;
- não quebra com campo ausente;
- ignora vaga inválida;
- normaliza senioridade;
- gera hash de deduplicação.

## Exemplos de testes

### Senioridade

```python
def test_detects_senior_position():
    text = "Vaga para Desenvolvedor Senior com 5+ anos de experiência"
    assert is_senior_position(text) is True
```

### Recomendação

```python
def test_recommendation_for_high_score():
    assert classify_recommendation(match_score=85, risk_score=10) == "Aplicar"
```

### Gatilhos de baixa aderência

```python
def test_low_match_when_many_disqualifying_terms():
    text = "Tech Lead, 7+ anos, AWS avançado obrigatório"
    flags = detect_disqualifying_terms(text)
    assert len(flags) >= 3
```

### Schema da IA

```python
def test_match_analysis_schema_validates_score():
    data = {
        "match_score": 82,
        "ats_score": 75,
        "risk_score": 15,
        "recommendation": "Aplicar",
        "strengths": [],
        "gaps": [],
        "missing_keywords": [],
        "recruiter_message": "Olá..."
    }

    analysis = MatchAnalysis.model_validate(data)

    assert analysis.match_score == 82
```

## Critério mínimo para PR

Antes de abrir PR:

```bash
ruff check .
ruff format . --check
pytest
```

## Critério de qualidade do MVP

O MVP é aceitável quando:

- app roda localmente;
- parser de PDF tem erro tratado;
- schema da IA é validado;
- regras principais têm teste;
- Ruff passa;
- README explica como rodar;
- não há dados reais versionados.
