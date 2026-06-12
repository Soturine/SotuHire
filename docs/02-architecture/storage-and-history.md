# Storage, histórico e privacidade

## Objetivo

A v0.4 adiciona histórico local pequeno e transparente, sem banco externo e sem salvar o texto bruto do currículo.

## Componentes

```text
modules/storage/
├── models.py
└── local_store.py

modules/tracker/
├── status.py
├── job_tracker.py
└── dashboard.py
```

## Registro salvo

`StoredAnalysis` mantém:

- id local;
- timestamps;
- cargo e empresa;
- status;
- scores e recomendação;
- sugestões do Resume Tailor;
- notas;
- confirmação de privacidade.

Não mantém:

- texto bruto do currículo;
- descrição integral da vaga;
- chaves de API;
- arquivos enviados.

## Persistência

O `LocalStore` grava JSON em `data/sotuhire-history.json`. A pasta `data/` é ignorada pelo Git. Escrita usa arquivo temporário e substituição para reduzir risco de arquivo parcial.

## Tracker

Status disponíveis:

```text
found, analyzed, good_fit, applied, message_sent, follow_up,
interview, technical_test, rejected, offer, archived
```

O usuário controla alterações. Não existe candidatura ou mensagem automática.

## Dashboard

As métricas são funções puras:

- total analisado;
- médias de Match, ATS e Opportunity Fit;
- recomendadas para aplicar;
- alto risco;
- últimas análises.

## Privacidade

Salvar exige confirmação explícita na interface. Arquivos locais devem continuar fora do versionamento e podem ser removidos pelo usuário a qualquer momento.
