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

## Fórmula inicial sugerida

No MVP, não precisa de fórmula estatística complexa. Uma fórmula simples pode combinar:

- 50% análise semântica da IA;
- 20% senioridade;
- 15% habilidades técnicas;
- 10% localidade/modalidade;
- 5% qualidade ATS.

Essa fórmula deve ser documentada e ajustável.

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
