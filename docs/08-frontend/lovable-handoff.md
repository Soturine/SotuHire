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
- Resultado de Match;
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
- não calcular Match Score real no frontend;
- não recriar ATS, Resume Tailor, GitHub Analyzer ou IA no frontend;
- não prometer backend no GitHub Pages;
- não mover regras anti-invenção para JavaScript visual.

## Contratos obrigatórios

Lovable deve usar:

- [api-contract.md](api-contract.md);
- [mock-data-contract.md](mock-data-contract.md);
- [frontend-rules.md](frontend-rules.md);
- mocks em `docs/assets/mock-api/`.

## Como conectar depois com a API real

1. Criar o frontend com dados mockados.
2. Isolar a camada de dados em um client HTTP.
3. Mapear cada tela para endpoint versionado.
4. Tratar loading, erro, vazio e sucesso.
5. Substituir mocks por `GET`/`POST`/`PATCH` reais quando a API v1 existir.

## Regra anti-invenção

Toda sugestão de currículo deve separar:

- evidência já presente;
- item que pode ser adicionado apenas se for verdadeiro;
- item sem evidência que deve ser tratado como gap real.

Credenciais, certificações, registros profissionais, empregos e formações nunca devem
ser inferidos como existentes sem evidência.
