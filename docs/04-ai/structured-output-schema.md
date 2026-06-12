# Schema de saída estruturada

## Por que usar JSON

Texto livre é bom para leitura humana, mas ruim para sistemas. O SotuHire precisa exibir score, listas, alertas e mensagens de forma organizada. Por isso, a resposta da IA deve seguir um schema.

A Gemini API oferece suporte a saídas estruturadas, e a documentação oficial recomenda o SDK `google-genai` para Python. Consulte:

- [Gemini API - Libraries](https://ai.google.dev/gemini-api/docs/libraries)
- [Gemini API - Structured outputs](https://ai.google.dev/gemini-api/docs/structured-output)

## Schema inicial

```json
{
  "match_score": 82,
  "recommendation": "Aplicar",
  "seniority_fit": "Estágio/Júnior",
  "summary": "Resumo curto da análise.",
  "strong_points": [
    "Engenharia da Computação",
    "Projetos com IA e automação"
  ],
  "weak_points": [
    "Falta experiência profissional direta com IA em produção"
  ],
  "missing_keywords": [
    "Power BI",
    "dashboards"
  ],
  "ats_notes": [
    "Currículo possui texto extraível",
    "Seção de projetos poderia destacar mais palavras-chave"
  ],
  "risk_flags": [
    "Vaga menciona inglês avançado"
  ],
  "recommended_actions": [
    "Destacar projetos de automação no currículo",
    "Adaptar resumo profissional para dados e IA"
  ],
  "recruiter_message": "Olá! Vi a oportunidade..."
}
```

## Modelo Pydantic sugerido

```python
from pydantic import BaseModel, Field
from typing import Literal

class MatchAnalysis(BaseModel):
    match_score: int = Field(ge=0, le=100)
    recommendation: Literal[
        "Aplicar",
        "Aplicar com cautela",
        "Revisar antes de aplicar",
        "Não aplicar",
    ]
    seniority_fit: str
    summary: str
    strong_points: list[str]
    weak_points: list[str]
    missing_keywords: list[str]
    ats_notes: list[str]
    risk_flags: list[str]
    recommended_actions: list[str]
    recruiter_message: str
```

## Validações

O sistema deve validar:

- `match_score` entre 0 e 100;
- listas sempre como listas;
- mensagem não vazia;
- recomendação dentro dos valores permitidos;
- score coerente com recomendação.

## Fallback

Se a IA retornar JSON inválido:

1. tentar corrigir uma vez;
2. se falhar, mostrar erro amigável;
3. registrar o erro sem salvar dados sensíveis;
4. permitir nova tentativa.

## Combinação com regras determinísticas

O JSON da IA não deve ser autoridade absoluta. Exemplo:

- IA retorna 82;
- regra detecta `sênior` e `5+ anos`;
- sistema ajusta para 45 ou mostra alerta forte.

Isso evita score bonito para vaga incompatível.
