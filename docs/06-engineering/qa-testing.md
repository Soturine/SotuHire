# QA e testes

## Objetivo

QA no SotuHire não é burocracia. É o que mostra que o projeto não é só “um prompt com Streamlit”. O foco inicial deve ser testar regras determinísticas, schemas e tratamento de entradas.

## Ferramentas sugeridas

- [`pytest`](https://docs.pytest.org/en/stable/getting-started.html) para testes;
- `ruff` para lint/format;
- `pydantic` para validar schemas;
- mocks para chamadas de IA.

## O que testar primeiro

### Regras de senioridade

```python
def test_detects_senior_position():
    text = "Vaga para Desenvolvedor Senior com 5+ anos de experiência"
    assert is_senior_position(text) is True
```

### Recomendação por score

```python
def test_recommendation_for_high_score():
    assert classify_recommendation(85) == "Aplicar"
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
    data = {"match_score": 82, ...}
    analysis = MatchAnalysis.model_validate(data)
    assert analysis.match_score == 82
```

## Testes que não devem depender de API real

Evite chamar Gemini/OpenAI em testes de rotina. Isso deixa os testes:

- lentos;
- caros;
- instáveis;
- dependentes de internet;
- dependentes de chave.

Use resposta fake.

## Testes manuais

Tenha exemplos em `tests/fixtures/`:

- currículo alinhado;
- currículo pouco alinhado;
- vaga júnior;
- vaga sênior;
- post informal;
- descrição vazia.

## Checklist de QA antes de commit

- `pytest` passa;
- app abre localmente;
- nenhum currículo real foi commitado;
- `.env` não foi commitado;
- README continua atualizado;
- novas regras têm teste;
- prompts foram revisados.

## Qualidade da resposta de IA

Além de teste automatizado, avalie manualmente:

- a IA inventou algo?
- o score faz sentido?
- a recomendação bate com senioridade?
- a mensagem está profissional?
- os gaps são úteis?
