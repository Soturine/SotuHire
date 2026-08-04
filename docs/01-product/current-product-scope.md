# Escopo atual do produto

O SotuHire v1.9.9 é um assistente de carreira local-first, multiárea e orientado por
evidências. Ele organiza perfil, documentos, oportunidades e candidaturas; compara requisitos;
prepara materiais revisáveis; e preserva os snapshots usados em cada decisão. IA externa é
opcional e nunca substitui o caminho determinístico local.

## Entregue

- API FastAPI local com pairing, sessão HttpOnly/CSRF, token nativo, Host/Origin estritos,
  rate limit e limites de corpo, lote e profundidade;
- Perfil Universal com fatos confirmados separados de conteúdo sourced/candidate/rejected;
- ingestão local PDF, DOCX, HTML, TXT e JSON Resume com proveniência e revisão;
- Currículo Mestre, variantes, diff, preview e exports reais PDF/DOCX/JSON Resume;
- Application Lab com Match, ATS, readiness e Tailor reais e independentes;
- Professional Assets e Application Kit com lifecycle, aprovação por item e stale;
- Tracker transacional em SQLite, snapshots, outcomes manuais, Radar paginado e leases locais;
- extensão MV3 0.9.5 com captura assistida, fila, handoff por IDs e Companion idempotente;
- Gemini/OpenAI opt-in, fallback local explícito, schema estruturado e erros tipados.

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
Taxonomias CBO/QBQ/ESCO/O*NET e conectores oficiais estão no roadmap, não na v1.9.9.

O antigo documento de MVP foi preservado como [histórico](../history/mvp-scope.md), sem ser
usado como descrição do produto atual.
