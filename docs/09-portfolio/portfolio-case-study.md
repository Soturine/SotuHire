# SotuHire — case study de produto e engenharia

## Problema

Currículos, vagas, portfólios, Lattes, editais e candidaturas vivem em ferramentas separadas. A pessoa repete contexto, perde proveniência e pode receber sugestões de IA sem saber quais fatos foram usados.

## Solução

SotuHire centraliza evidências em um Perfil Profissional Universal. O Career Context Engine seleciona apenas o contexto necessário e o distribui para Match, ATS, Tailor, Radar, Editais, Tracker e extensão. Tudo permanece revisável e local-first.

## Arquitetura

- `modules/`: regras, parsers, Perfil, contexto, memória/RAG, identidade e scores.
- `apps/api/`: FastAPI local e contratos Pydantic.
- `apps/web/`: React/Vite em Demo e API Real.
- `browser-extension/`: Companion assistiva com captura manual e fila offline.
- JSON/JSONL atômico mantém implantação simples; sem banco externo ou microserviços.

## IA explicável

Gemini/OpenAI são opcionais. Cada análise expõe provider/modelo solicitado e usado, prompt/versionamento, modo, fallback, motivo, request ID, fontes e evidências. Scores críticos continuam ancorados em regras determinísticas e revisão.

## Produto multiárea

A demo cobre engenharia, enfermagem/COREN, pesquisa/Lattes, docência/extensão, transição com experiência não formal, concurso e design/portfólio. GitHub não é requisito universal e registro profissional nunca é presumido.

## Extensão e integrações

A v0.9.1 captura vaga, edital, GitHub e lotes com a Local Companion; funciona sem o frontend aberto. O popup e o modal injetado organizam análise local, IA do SotuHire e Gemini/OpenAI próprios. Catálogos oficiais atualizáveis alimentam uma seleção de modelo funcional, enquanto a API pública do GitHub aprofunda README, commits, stack, estrutura e atividade sem autenticação. Offline, mantém fila temporária e fallback local. O site funciona integralmente sem a extensão.

## Segurança e decisões técnicas

- sem auto-apply, login automático, CAPTCHA bypass ou inscrição/pagamento automático;
- chave do app somente no backend local; chave própria opcional da extensão isolada no service worker;
- candidatos de IA/Lattes/GitHub passam por revisão antes do Perfil;
- identidade canônica preserva DOI, ORCID, owner/repo, URLs e histórico;
- arquitetura existente foi reforçada sem Redis, fila distribuída ou reescrita.

## Testes e qualidade

O projeto combina pytest, Ruff, Pyright, compileall, MkDocs strict, TypeScript, ESLint, Vite, Playwright multi-browser, scanner de segredos, empacotamento da extensão e verificação de checkout limpo.

## Resultado e próximos passos

A v1.9.5 transforma abas antes conectadas de forma desigual em um fluxo demonstrável com proveniência. Próximos passos legítimos: upload direto de PDF/HTML, estudo avançado por edital, notificações do sistema e telemetria local de uso/fallback.
