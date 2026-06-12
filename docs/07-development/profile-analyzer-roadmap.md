# Roadmap do Profile Analyzer

O Profile Analyzer transforma dados de presença profissional em recomendações acionáveis.

## Fase 1: Currículo ATS

- extrair texto de PDF/DOCX;
- calcular ATS Score;
- encontrar keywords ausentes;
- sugerir ajustes.

## Fase 2: LinkedIn CSV

- ler exportação oficial do LinkedIn;
- avaliar headline, about, experience, skills, education e certifications;
- gerar LinkedIn Score;
- sugerir plano de ação.

Referência: [linkedin-profile-score](https://github.com/henriquesantanati/linkedin-profile-score).

## Fase 3: GitHub/Portfolio

- analisar repositórios públicos;
- selecionar arquivos relevantes;
- calcular Portfolio Score;
- sugerir projetos para currículo.

Referência: [RepoLogs](https://github.com/VictoriaSCorreia/RepoLogs_GithubExtension).

## Fase 4: Lattes

- importar XML/HTML/texto do Currículo Lattes quando o usuário fornecer;
- extrair produção acadêmica;
- converter para linguagem ATS quando fizer sentido.

## Fase 5: RAG de carreira

- indexar currículo, LinkedIn, GitHub, Lattes e histórico;
- recuperar evidências por vaga;
- gerar recomendações com fontes internas.

## Saída consolidada

```json
{
  "ats_score": 78,
  "linkedin_score": 72,
  "portfolio_score": 84,
  "lattes_score": 61,
  "readiness_score": 79,
  "recommended_actions": []
}
```

## Critérios de aceitação

- Cada score deve ter evidências.
- O usuário deve conseguir revisar dados.
- O sistema não deve inventar experiência.
- O sistema deve diferenciar ausência de dados de baixa qualidade.
- O sistema deve permitir apagar perfil importado.
