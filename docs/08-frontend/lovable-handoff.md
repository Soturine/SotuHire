# Lovable handoff

## Visão do produto

SotuHire é um copiloto de carreira local-first para analisar currículos, vagas,
evidências públicas de portfolio e estratégia de candidatura sem inventar experiências.

O produto ajuda a responder:

```text
Esta vaga faz sentido para mim?
Quais são os gaps?
O que posso ajustar com segurança?
```

## Público-alvo

- pessoas procurando vagas com mais critério;
- profissionais de tecnologia, saúde, educação, engenharia, arquitetura, cybersecurity e áreas afins;
- pessoas que querem entender aderência ATS e gaps reais;
- pessoas que valorizam privacidade e uso local dos próprios dados.

## Páginas esperadas

- Landing / Home;
- Dashboard;
- Upload ou colagem de currículo;
- Perfil profissional;
- Entrada de vaga;
- Análise de Compatibilidade;
- ATS Review;
- Resume Tailor;
- GitHub Analyzer;
- Portfolio Evidence;
- Kanban de candidaturas;
- Application Intelligence;
- Histórico;
- Configurações locais;
- Privacidade/local-first.

## Liberdade visual permitida

Lovable pode redesenhar toda a experiência visual: grid, cards, sidebar, navegação,
microinterações, responsividade, visual de charts, copy curta, hierarquia e composição.

Essa liberdade não inclui reimplementar regra crítica no frontend.

## Restrições técnicas

- não colocar API keys no frontend;
- não colocar tokens GitHub, Gemini key ou segredos no site;
- não usar dados reais nos mocks;
- não calcular pontuação real no frontend;
- não recriar ATS, Resume Tailor, GitHub Analyzer ou IA no frontend;
- não prometer backend no GitHub Pages;
- não mover regras anti-invenção para JavaScript visual.

## Contratos obrigatórios

Lovable deve usar:

- [api-contract.md](api-contract.md);
- [mock-data-contract.md](mock-data-contract.md);
- [frontend-rules.md](frontend-rules.md);
- mocks em `docs/assets/mock-api/`.

## Como conectar com a API real

Desde a v1.3.0, o frontend moderno existe em `apps/web` e a API real local existe em `apps/api`.

1. Usar `http://127.0.0.1:8787/api/v1` em desenvolvimento local.
2. Consultar `http://127.0.0.1:8787/openapi.json` para gerar ou validar types.
3. Mapear cada tela para endpoint versionado.
4. Tratar loading, erro, vazio e sucesso.
5. Manter mocks no Modo Demo.
6. Usar `GET`/`POST`/`PATCH` reais no Modo API Real sem recalcular regra critica no frontend.

Para subir a API:

```bash
python scripts/run_api.py
```

## Regra anti-invenção

Toda sugestão de currículo deve separar:

- evidência já presente;
- item que pode ser adicionado apenas se for verdadeiro;
- item sem evidência que deve ser tratado como gap real.

Credenciais, certificações, registros profissionais, empregos e formações nunca devem
ser inferidos como existentes sem evidência.
