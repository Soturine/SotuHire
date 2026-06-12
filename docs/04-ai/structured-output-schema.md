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


## Extensão futura do schema

Quando o SotuHire passar a usar Lattes, GitHub, LinkedIn e portais como fontes explícitas, o schema pode evoluir para:

```json
{
  "resume_type_detected": "ats_resume",
  "source_profiles_used": ["pdf_resume", "lattes", "github"],
  "source_portal": "gupy",
  "portal_strategy": "manual_url_and_text",
  "ats_score": 78,
  "academic_score": 64,
  "portfolio_score": 82,
  "risk_score": 30,
  "lattes_relevant_items": [],
  "github_relevant_projects": [],
  "recommended_resume_version": "ats_resume_for_data_internship"
}
```

Esses campos ajudam a separar:

- qualidade ATS;
- aderência semântica;
- relevância acadêmica;
- força dos projetos;
- risco da fonte/vaga;
- recomendação de versão do currículo.

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

---

# Schema expandido de análise completa

```json
{
  "match_score": 82,
  "ats_score": 76,
  "risk_score": 18,
  "linkedin_score": 70,
  "portfolio_score": 84,
  "lattes_score": null,
  "readiness_score": 79,
  "recommendation": "Aplicar com ajustes",
  "evidence": [],
  "strengths": [],
  "gaps": [],
  "missing_keywords": [],
  "best_projects_to_highlight": [],
  "linkedin_actions": [],
  "portfolio_actions": [],
  "message_to_recruiter": "",
  "next_follow_up_days": 5,
  "risk_flags": []
}
```

## Regras para IA

- Nunca inventar experiência.
- Nunca alterar fatos do currículo.
- Sempre separar evidência de sugestão.
- Sempre indicar quando faltam dados.
- Sempre devolver JSON válido.
- Sempre permitir revisão humana antes de ação externa.

## Atualização: Pydantic como contrato principal

O SotuHire deve usar Pydantic para validar toda saída de IA que tenha efeito no produto. Isso inclui análise de vaga, currículo direcionado, profile score e portfolio score.

Schemas novos:

- `JobAnalysisSchema`
- `UserPreferences`
- `ResumeTailorOutput`
- `TailoredResumeSection`
- `JSONResume`
- `CareerEvidence`

Regra:

```text
Sem schema, a saída da IA é rascunho.
Com schema validado, a saída pode entrar no produto.
```

Referências:

- [Gemini Structured Outputs](https://ai.google.dev/gemini-api/docs/structured-output)
- [JSON Resume](https://jsonresume.org/schema)
- [Pydantic](https://docs.pydantic.dev/)
