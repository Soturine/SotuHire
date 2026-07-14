# Local Companion API

A Local Companion API conecta a extensão assistiva ao SotuHire sem publicar um serviço na rede.
Ela usa a biblioteca padrão do Python, escuta somente em `127.0.0.1:8765` e grava dados nos stores
locais ignorados pelo Git.

A FastAPI em `apps/api` atende o frontend em `127.0.0.1:8787/api/v1`. A Companion continua sendo a
ponte enxuta da extensão para os fluxos `/capture/*`; a FastAPI oferece histórico, importações e
revisão no site.

| API local | Porta padrão | Uso principal |
| --- | --- | --- |
| Local Companion API | `8765` | extensão, captura assistida, fila e análise conectada |
| Frontend API Layer | `8787` | frontend, OpenAPI e ponte `/api/v1/extension/*` |

## Endpoints da Companion

| Endpoint | Uso |
| --- | --- |
| `GET /health` | testa localhost sem expor configuração ou segredo |
| `POST /handshake` | negocia versões, capabilities, compatibilidade e warnings |
| `GET /capture/status` | retorna um resumo seguro das capturas |
| `GET /capture/context-summary` | retorna contexto curto, confirmado e não sensível |
| `POST /capture/job` | normaliza a vaga, salva a captura e cria `JobSnapshot` |
| `POST /capture/public-exam` | salva edital revisável e cria `PublicExamSnapshot` |
| `POST /capture/analyze` | cria análise ligada ao anúncio e ao currículo realmente usados |
| `POST /capture/tracker` | envia a captura ao Tracker preservando snapshots e origem |
| `POST /capture/applications` | importa lote de candidaturas já realizadas |
| `POST /capture/github-profile` | analisa perfil GitHub público |
| `POST /capture/github-repo` | analisa repositório público |
| `POST /capture/portfolio` | analisa portfólio público |
| `POST /capture/project` | analisa página pública de projeto |
| `POST /capture/repo-analysis` | gera e salva relatório completo |
| `POST /capture/commit-analysis` | gera relatório com sinais de commits públicos |

## Handshake

O popup informa a versão obtida do próprio `manifest.json`. A resposta inclui:

```json
{
  "extension_version": "0.9.3",
  "companion_version": "1.9.7",
  "api_version": "v1",
  "capabilities": ["capture.job", "queue.retry", "jobposting.jsonld"],
  "compatible": true,
  "warnings": []
}
```

O contrato também informa versões mínima e máxima testada. Ele não contém chave, token, Perfil ou
conteúdo capturado. Um cliente antigo sem handshake ainda pode usar `/health`, mas o popup mostra o
aviso de compatibilidade limitada.

## Contexto ativo

O site sincroniza currículo, preferências e nome do provider em
`data/companion/active-context.json`. A Companion usa apenas o subconjunto necessário para a ação e
prioriza evidências confirmadas. A resposta expõe `context_summary`, `evidence_used`, `warnings` e
`source_refs`, sem devolver Perfil completo ou chave.

Quando **IA configurada no SotuHire** é escolhida, provider e chave permanecem no processo local. A
extensão recebe somente relatório e metadados seguros. Nos modos Gemini/OpenAI próprios, o service
worker chama o provider e nunca envia a chave à Companion.

## Capturas e snapshots

Uma captura de vaga ou edital recebe `capture_id`, `content_hash`, `snapshot_id` e histórico de
snapshots. Conteúdo idêntico é deduplicado por identidade/hash; conteúdo alterado preserva uma nova
versão imutável.

Ao analisar uma vaga, a Companion também pode criar `ResumeSnapshot` do contexto utilizado e
`AnalysisSnapshot` com provider/modelo solicitado e usado, prompt, fallback e evidências. O Tracker
referencia esses IDs, por isso o anúncio continua consultável mesmo que a página original desapareça.

## Identidade e fila

A fila existe no navegador, não na Companion. Antes de enviar, ela normaliza URLs, remove parâmetros
comuns de tracking e deduplica por endpoint + URL. Cada pendência registra tentativas, último erro,
próximo retry e estado. O backend usa identidades canônicas e hashes para tornar reenvios
idempotentes.

O export da fila é separado do backup de dados do SotuHire. `chrome.storage`, IndexedDB, chaves,
tokens e cookies nunca entram no backup geral.

## Segurança

- bind obrigatório em loopback;
- token `SOTUHIRE_COMPANION_TOKEN` opcional;
- contratos Pydantic com limites;
- sanitização do texto recebido;
- nenhum log de conteúdo completo ou chave;
- nenhum login, senha, cookie, sessão ou CAPTCHA tratado pela API;
- nenhuma chave própria Gemini/OpenAI recebida da extensão;
- nenhuma chamada ao authenticated-browser feita por essa ponte.

Para projetos, scores determinísticos críticos permanecem disponíveis mesmo quando um provider
falha. A resposta registra o fallback e seu motivo; não há troca silenciosa.

## Iniciar

```bash
python -m modules.local_api.server
```

No Windows, o launcher também pode iniciar a Companion:

```powershell
.\start-sotuhire.ps1 -WithCompanion
```
