# JobSpy como referência experimental

[JobSpy](https://github.com/Bunsly/JobSpy) é uma biblioteca Python de scraping/agregação de vagas que aparece como referência interessante para estudo. Ela declara suporte a fontes como LinkedIn, Indeed, Glassdoor, Google e ZipRecruiter.

## Como usar a referência

O SotuHire pode estudar o JobSpy para entender:

- normalização de vagas;
- campos comuns;
- filtros por localização;
- filtros por remoto;
- idade da vaga;
- retorno em dataframe;
- diferenças entre fontes.

## Cuidado de compliance

O SotuHire não deve se posicionar como ferramenta para burlar bloqueios, limites ou regras de plataformas. Qualquer uso de biblioteca externa deve passar por avaliação de termos, rate limit, cache e escopo.

## Estratégia segura

Priorizar:

- entrada manual;
- extensão assistiva;
- fontes públicas simples;
- APIs oficiais quando existirem;
- conectores com status `experimental`;
- logs e rate limit.

## Status recomendado

```text
jobspy: experimental_reference
production_use: not_decided
requires_compliance_review: true
```
