# Avaliação da IA

## Por que avaliar

Modelos de IA podem variar respostas, interpretar errado ou inventar detalhes. O SotuHire precisa de critérios para saber se a análise está útil e confiável.

## Critérios de qualidade

Uma boa análise deve:

- respeitar o currículo;
- não inventar habilidades;
- explicar o score;
- considerar senioridade;
- apontar gaps reais;
- sugerir ações práticas;
- retornar JSON válido;
- gerar mensagem profissional.

## Casos de teste manuais

Crie exemplos de currículos e vagas fictícias:

1. vaga muito alinhada;
2. vaga parcialmente alinhada;
3. vaga sênior incompatível;
4. vaga com descrição curta;
5. post informal de recrutador;
6. vaga com muitos requisitos desejáveis;
7. vaga fora da área.

## Métricas simples

| Métrica | Como verificar |
|---|---|
| JSON válido | Validação Pydantic |
| Score coerente | Comparação com faixa esperada |
| Sem invenção | Verificar se pontos fortes aparecem no CV |
| Senioridade respeitada | Vaga sênior não deve virar match alto |
| Mensagem útil | Deve ser curta e editável |

## Testes automatizados com mock

Não teste chamando a API real em todo commit. Use mocks.

Exemplo:

```python
def test_ai_response_schema(sample_ai_response):
    analysis = MatchAnalysis.model_validate(sample_ai_response)
    assert 0 <= analysis.match_score <= 100
```

## Avaliação humana

Como é um projeto de apoio à carreira, revisão humana é essencial. O usuário sempre deve revisar:

- currículo;
- mensagem;
- recomendação;
- palavras-chave sugeridas.
