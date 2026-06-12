# Regras do Opportunity Fit Score

O Opportunity Fit Score transforma preferências do usuário em cálculo claro e auditável.

## Entradas

- vaga normalizada;
- preferências do usuário;
- pesos;
- campos ausentes;
- sinais de risco.

## Subscores

| Subscore | Exemplo |
|---|---|
| Modalidade | remoto recebe 100 se usuário prioriza remoto |
| Localização | Jacareí/SJC/SP recebem bônus conforme preferência |
| Salário | abaixo do mínimo reduz score |
| Contrato | estágio/júnior/CLT/PJ conforme aceitação |
| Senioridade | sênior derruba score para usuário júnior |
| Velocidade | processo claro e recente aumenta score |
| Risco | descrição vaga/genérica reduz score |

## Campos ausentes

Campo ausente não deve ser tratado como zero automaticamente. Ele deve gerar incerteza.

Exemplo:

```text
salário ausente -> score parcial + warning
modalidade ausente -> score parcial + warning
```

## Recomendação

- `apply`: boa técnica e boa aderência pessoal.
- `apply_with_adjustments`: boa, mas currículo precisa ajuste.
- `save_for_later`: potencial, mas faltam dados.
- `ignore`: incompatível ou alto risco.

## Transparência

Todo score deve vir com explicação simples.

```text
A vaga caiu de 85 para 62 porque é presencial fora da região preferida e não informa salário.
```

## Implementação v0.1

A função pública da v0.1 é `calculate_opportunity_fit_score()`. Ela recebe uma vaga normalizada e `UserPreferences`, calcula apenas os subscores configurados e devolve um inteiro entre 0 e 100.

Quando nenhuma preferência concreta foi configurada, a função usa um valor neutro para permitir que a análise continue sem fingir precisão. Campos ausentes recebem pontuação parcial, preservando a diferença entre “incompatível” e “não informado”.

Pesos disponíveis:

- `modality_weight`;
- `location_weight`;
- `salary_weight`;
- `contract_weight`;
- `seniority_weight`.

## Cenários mínimos de teste

- modalidade preferida aumenta o score;
- localização incompatível reduz o score;
- salário abaixo do mínimo reduz proporcionalmente;
- contrato aceito aumenta o score;
- vaga sênior reduz fortemente o fit de um perfil júnior;
- campos ausentes não quebram a função;
- resultado nunca fica abaixo de 0 ou acima de 100.
