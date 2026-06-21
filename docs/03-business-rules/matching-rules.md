# Regras de match

## Objetivo

O match do SotuHire não deve ser apenas uma porcentagem bonita. Ele precisa ser explicável. Toda recomendação deve responder:

- por que essa vaga combina?
- por que talvez não combine?
- o que falta?
- vale aplicar mesmo assim?
- o currículo precisa ser adaptado?

## Faixas de score

| Score | Rótulo | Recomendação |
|---|---|---|
| 80-100 | Match forte | Aplicar |
| 60-79 | Bom match | Aplicar com cautela |
| 40-59 | Match fraco | Revisar antes de aplicar |
| 0-39 | Baixa aderência | Provavelmente não aplicar |

## Critérios positivos

Aumentam o match:

- vaga de estágio, júnior ou trainee;
- área alinhada ao perfil alvo;
- ferramentas presentes no currículo;
- projetos relevantes;
- formação compatível;
- requisitos desejáveis já atendidos;
- vaga aceita remoto/híbrido/localidade desejada;
- descrição menciona aprendizado ou primeira oportunidade.

## Critérios negativos

Reduzem o match:

- sênior, especialista, tech lead ou arquiteto;
- muitos anos de experiência obrigatória;
- tecnologia completamente fora do perfil;
- inglês fluente obrigatório, se não estiver no currículo;
- superior completo obrigatório, se o candidato ainda estiver cursando;
- certificações obrigatórias ausentes;
- stack muito distante.

## Regras de senioridade

Senioridade deve ter peso alto. Uma vaga com stack compatível, mas nível sênior, não deve receber match alto para candidato de estágio/júnior.

Exemplo:

```text
Vaga: Engenheiro de IA Sênior
Requisitos: 5+ anos, AWS avançado, produção com agentes, liderança técnica
Resultado: baixa aderência, mesmo que cite Python e IA
```

## Fórmula atual da v0.12.0

Na Match Engine 2.0, a nota final é calculada pelo código. A IA pode apoiar classificação e
explicação, mas não decide o score final sozinha.

| Dimensão | Peso |
|---|---:|
| Requisitos obrigatórios | 30% |
| Requisitos desejáveis | 15% |
| Aderência de domínio | 10% |
| Senioridade | 10% |
| Formação, certificações e registros | 10% |
| Força das evidências | 10% |
| Evidências GitHub/portfolio | 5% |
| ATS keyword alignment | 5% |
| Preferências/logística | 5% |

O `risk_adjustment` aplica penalidade depois do cálculo base. Gaps knockout e registros
profissionais obrigatórios ausentes limitam fortemente o score.

## Exemplo de saída

```json
{
  "match_score": 84,
  "recommendation": "Aplicar",
  "reason": "A vaga é de estágio, cita Python, dados e automação, e o currículo possui formação em Engenharia da Computação e projetos alinhados.",
  "risk_flags": [
    "Power BI aparece como diferencial, mas não está forte no currículo"
  ]
}
```

## Regra importante

O sistema nunca deve dizer que o usuário tem uma habilidade se ela não aparece no currículo. Pode dizer:

> A vaga pede Power BI. Se você realmente tiver conhecimento, vale destacar melhor no currículo.

Mas não deve inventar:

> Você possui Power BI avançado.

## Registros profissionais sensíveis

A v0.12.0 trata registros profissionais e conselhos de classe como requisitos sensíveis quando a
vaga os exige.

Catálogo inicial:

- saúde: CRM, CRO, CRF, COREN, CREFITO, CRN, CRMV, CRP, CREF, CRTR;
- engenharia/arquitetura/técnico/indústria: CREA, CAU, CFT, CRT, CRQ;
- humanas/gestão/comunicação/sociais: OAB, CRC, CRA, CORECON, CRB, CRESS, CONRERP, CRECI;
- ciências e outras áreas: CRBio;
- registro profissional vinculado ao trabalho: MTE/DRT como `professional_registration`.

Regras:

- registro obrigatório explícito vira `importance = required` e `criticality = knockout`;
- registro desejável vira `importance = preferred` e `criticality = medium`;
- registro obrigatório ausente vira `match_status = missing` e `gap_severity = knockout`;
- MTE/DRT não são tratados como conselho de classe, mas como `professional_registration`;
- a opção genérica `Outro conselho / Outro registro profissional` deve ser aceita para cadastro ou
  revisão manual.

Sugestão correta:

```text
A vaga exige CREA. Como o currículo não mostra esse registro, isso deve ser tratado como gap
crítico. Se você possui CREA ativo, destaque no currículo; caso contrário, a vaga pode não ser
compatível.
```

# Atualização: Match Engine 2.0 multiárea

A regra antiga de match continua útil como base, mas a próxima evolução precisa ser mais rica que cobertura de palavras.

O SotuHire deve tratar o match como compatibilidade entre:

- requisitos obrigatórios;
- requisitos desejáveis;
- formação;
- credenciais;
- experiência;
- ferramentas;
- equipamentos;
- normas;
- ambiente de atuação;
- senioridade;
- modalidade;
- localidade;
- portfólio;
- evidências;
- preferências;
- riscos.

## Novo status por requisito

Cada requisito deve receber status:

- `matched`: evidência clara;
- `partial`: evidência parcial;
- `missing`: ausência clara;
- `unclear`: falta informação;
- `not_applicable`: não aplicável.

Competências transferíveis ficam em uma lista própria e não viram match direto.

## Exemplo de requisito classificado

```json
{
  "requirement": "Experiência em UTI",
  "importance": "required",
  "category": "experience",
  "status": "missing",
  "gap_severity": "high",
  "candidate_evidence": [],
  "safe_action": "Se essa experiência existir, especificar o setor; se não existir, tratar como gap real."
}
```

## Travas de score

Alguns gaps devem limitar o score final.

Exemplos:

- registro profissional obrigatório ausente;
- diploma obrigatório ausente;
- senioridade muito acima;
- idioma obrigatório ausente;
- localidade incompatível com presencial obrigatório;
- certificação legal obrigatória ausente.

Sugestão:

```text
1 knockout gap real -> score máximo 45
2+ knockout gaps reais -> score máximo 30
knockout incerto -> pedir revisão antes de travar
```

## Competências transferíveis

Competências transferíveis devem ajudar, mas não substituir requisitos críticos.

Exemplo:

```text
Experiência com atendimento ao público em saúde pode ajudar em vaga de healthtech,
mas não comprova experiência em produto, dados ou desenvolvimento.
```

## Pesos implementados

```text
required_requirements: 30%
preferred_requirements: 15%
domain_fit: 10%
seniority_fit: 10%
education_credentials: 10%
evidence_strength: 10%
portfolio_github_evidence: 5%
ats_keyword_alignment: 5%
preferences_fit: 5%
risk_adjustment: penalidade
```

Esses pesos são a base da v0.12.0 e podem evoluir por domínio em versões futuras.

## Regras por domínio

- TI: stack, projetos, arquitetura, testes e GitHub podem pesar mais.
- Cybersecurity: labs, writeups, ferramentas, fundamentos, segurança e ética pesam mais.
- Enfermagem: COREN, setor, procedimentos, escala e ambiente hospitalar pesam mais.
- Psicologia: CRP, público atendido, contexto e abordagem pesam mais.
- Pedagogia: etapa de ensino, BNCC, inclusão e sala de aula pesam mais.
- Engenharia civil: CREA, obras, orçamento, cronograma, AutoCAD/Revit e normas pesam mais.
- Arquitetura/interiores: portfólio visual, ferramentas, projeto executivo e atendimento pesam mais.

## Saída explicável obrigatória

A engine deve gerar explicação por requisito e uma síntese final.

A síntese deve responder:

- por que aplicar;
- por que ter cautela;
- quais gaps são críticos;
- quais gaps são apenas de currículo;
- quais evidências ajudam;
- o que não deve ser inventado.

Documento relacionado: [Match Engine 2.0](../07-development/v0.12.0-match-engine-2.md).
