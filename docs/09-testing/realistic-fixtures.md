# Fixtures Realistas

## Objetivo

As fixtures permitem validar o SotuHire sem currículo, vaga ou segredo real.

## Estrutura

```text
examples/
├── resumes/
├── jobs/
└── expected/
```

Os currículos cobrem formação técnica, faculdade, estágio, CLT, projetos selecionados, transição de carreira, IoT, links sem HTTPS e soft skills em linha corrida.

As vagas cobrem remoto, híbrido, presencial, estágio, júnior, salário ausente, benefícios e diferentes volumes de requisitos.

## Expected outputs

Os JSON em `examples/expected/` registram fatos estáveis:

- nome fictício;
- contagens de experiência, projeto, formação e curso;
- skills obrigatórias esperadas;
- links esperados.

Eles não armazenam texto bruto completo.

## Validar manualmente

```bash
python -m pytest -q tests/test_examples_fixtures.py tests/test_expected_outputs.py
```

Na UI, clique em `Rodar análise de exemplo` para percorrer parser, vaga, análise local e apresentação.

## Privacidade

Todos os nomes, empresas, instituições, emails e links são fictícios. Não substitua esses arquivos por dados pessoais reais versionados.
