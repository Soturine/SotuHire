# Escopo atual do produto

O SotuHire v2.0 é um copiloto de carreira local-first, multiárea e orientado por evidências. Ele
organiza perfil, documentos, oportunidades e candidaturas em um Evidence Graph; deriva Career
State e próximas ações deterministicamente; e só executa escritas locais depois de preview e
aprovação humana. IA externa é opcional e nunca substitui o caminho determinístico local.

## Entregue

- API FastAPI local com pairing, sessão HttpOnly/CSRF, token nativo, Host/Origin estritos,
  rate limit e limites de corpo, lote e profundidade;
- Perfil Universal com fatos confirmados separados de conteúdo sourced/candidate/rejected;
- ingestão local PDF, DOCX, HTML, TXT e JSON Resume com proveniência e revisão;
- Currículo Mestre, variantes, diff, preview e exports reais PDF/DOCX/JSON Resume;
- Application Lab com Match, ATS, readiness e Tailor reais e independentes;
- Professional Assets e Application Kit com lifecycle, aprovação por item e stale;
- Tracker transacional em SQLite, snapshots, outcomes manuais, Radar paginado e leases locais;
- fontes Greenhouse, Lever, JobPosting e RSS/Atom com proveniência e dedupe;
- taxonomias CBO/QBQ/ESCO/O*NET versionadas e ranking local explicável;
- Interview Preparation, STAR, perguntas, respostas e follow-up draft;
- tarefas, lembretes, Career Plan e export ICS explícito;
- locale/tema adaptativos, ajuda contextual e onboarding;
- extensão MV3 0.10.0 com captura assistida, preferências e Companion idempotente;
- Gemini/OpenAI opt-in, fallback local explícito, schema estruturado e erros tipados.
- Ollama, LM Studio e OpenAI-compatible com loopback default e health explícito;
- matching determinístico por domínio, analytics descritivo e taxonomy updater reversível;
- boundaries SSRF, URL, paths, restore e launcher endurecidos e dependências auditadas.
- Evidence Inbox/Graph, portfólio multidisciplinar, Career State e Next Best Actions;
- Copilot contextual com planos persistentes, proposals, preview, risco, approval, audit e undo;
- Cockpit, fila de aprovações, busca universal e SQLite schema 8 como writer dos domínios v2.

## Modos

| Modo | Garantia |
|---|---|
| Demo | dados fictícios no navegador; nenhum dado real é lido ou persistido |
| API Real | frontend pareado com FastAPI local; SQLite/stores locais persistem o trabalho |
| Site sem extensão | todos os fluxos de documento e candidatura continuam disponíveis |
| Extensão | captura a página visível mediante ação; não lê currículos locais |

## Fora do escopo

Não há auto-apply, login automático, form filling, bypass de CAPTCHA, pagamento, inscrição,
envio de documento/mensagem, scraping autenticado agressivo ou decisão crítica autônoma.
Download automático de datasets oficiais, envio de follow-up, calendário externo, auto-apply e
migração automática/destrutiva dos stores JSON legados permanecem fora da v2.0. MCP também não é
exposto até existir transporte autenticado, escopos e auditoria equivalentes ao registry interno.

O antigo documento de MVP foi preservado como [histórico](../history/mvp-scope.md), sem ser
usado como descrição do produto atual.
