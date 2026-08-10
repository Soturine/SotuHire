# SotuHire — case study de produto e engenharia

## Problema

Currículos, vagas, portfólios, Lattes, editais e candidaturas vivem em ferramentas separadas. A pessoa repete contexto, perde proveniência e pode receber sugestões de IA sem saber quais fatos foram usados.

## Solução

SotuHire centraliza evidências em um Perfil Profissional Universal. O Career Context Engine seleciona apenas o contexto necessário e o distribui para fontes, taxonomias, Match, ATS, Tailor, Radar, Editais, Tracker, entrevistas e ações de carreira. Tudo permanece revisável e local-first.

## Arquitetura

- `modules/`: regras, parsers, Perfil, contexto, memória/RAG, identidade e scores.
- `apps/api/`: FastAPI local e contratos Pydantic.
- `apps/web/`: React/Vite em Demo e API Real.
- `browser-extension/`: Companion assistiva com captura manual e fila offline.
- SQLite 7 sustenta domínios transacionais novos; JSON/JSONL legados permanecem explícitos durante a transição, sem banco externo ou microserviços.

## IA explicável

Gemini/OpenAI são opcionais. Cada análise expõe provider/modelo solicitado e usado, prompt/versionamento, modo, fallback, motivo, request ID, fontes e evidências. Scores críticos continuam ancorados em regras determinísticas e revisão.

## Produto multiárea

A demo cobre engenharia, enfermagem/COREN, pesquisa/Lattes, docência/extensão, transição com experiência não formal, concurso e design/portfólio. GitHub não é requisito universal e registro profissional nunca é presumido.

## Extensão e integrações

A extensão 0.10.0 captura vaga, edital, GitHub e lotes com a Local Companion; funciona sem o frontend aberto e compartilha preferências de locale/tema/ajuda. O popup e o modal injetado organizam análise local, IA do SotuHire e Gemini/OpenAI próprios. Catálogos oficiais atualizáveis alimentam uma seleção de modelo funcional, enquanto a API pública do GitHub aprofunda README, commits, stack, estrutura e atividade sem autenticação. Offline, mantém fila temporária e fallback local. O site funciona integralmente sem a extensão.

## Segurança e decisões técnicas

- sem auto-apply, login automático, CAPTCHA bypass ou inscrição/pagamento automático;
- chave do app somente no backend local; chave própria opcional da extensão isolada no service worker;
- candidatos de IA/Lattes/GitHub passam por revisão antes do Perfil;
- identidade canônica preserva DOI, ORCID, owner/repo, URLs e histórico;
- arquitetura existente foi reforçada sem Redis, fila distribuída ou reescrita.

## Testes e qualidade

O projeto combina pytest, Ruff, Pyright, compileall, MkDocs strict, TypeScript, ESLint, Vite, Playwright multi-browser, scanner de segredos, empacotamento da extensão e verificação de checkout limpo.

## Resultado e próximos passos

A v1.10.1 conecta Perfil → oportunidade → candidatura → entrevista → ação com proveniência e aprovação humana. Próximos passos legítimos estão no roadmap: interoperabilidade madura com IA local, taxonomias mais profundas, evidência acadêmica/profissional ampliada e analytics explicável — sem auto-apply.
